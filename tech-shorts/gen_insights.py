#!/usr/bin/env python3
"""
Tech Shorts Insights generator.

Rebuilds the "Content Intelligence" data (topics, per-video metrics, traffic
attribution, category + compilation membership, verdicts) into a single
`insights.json`, so the /fleet/insights page can fetch it live instead of
carrying a baked snapshot. The heavy compute runs here on the Mac (which holds
the YouTube token); the droplet only serves the resulting JSON.

    python3 gen_insights.py                 # fetch, compute, write insights.json (+ push)
    python3 gen_insights.py --no-push       # local only
    python3 gen_insights.py --limit 5       # only N videos (quick test)
    python3 gen_insights.py --since 2026-08-01

Data sources reused from the tech-shorts pipeline:
    geo_attribution.services()   -> (youtubeAnalytics v2, youtube v3) on the shared token
    compilations.json            -> categories, topic->category map, compilation membership

Topic classification is keyword-rule based (deterministic, no API), with an
optional per-video override in `insights_topic_overrides.json` ({video_id: topic}).
Verdicts are rule-based from each topic's aggregate performance.
"""
import argparse
import json
import os
import sys
from datetime import date, datetime, timezone
from pathlib import Path

from geo_attribution import services, published_date

HERE = Path(__file__).resolve().parent
COMPILATIONS = HERE / "compilations.json"
OVERRIDES = HERE / "insights_topic_overrides.json"
OUT = HERE / "insights.json"
REMOTE = "root@159.223.22.165:/opt/salesman-api/fleet/insights/insights.json"

# Topic -> colour class used by the page (matches the existing palette).
TOPIC_COLOR = {
    "AI Threats & Security": "c-coral",
    "AI Agents & Capabilities": "c-teal",
    "Consciousness & Mind": "c-violet",
    "Economy & Work": "c-warm",
    "Alignment & Safety": "c-green",
    "Governance & Geopolitics": "c-grey",
    "Music (Classical Remix)": "c-blue",
    "Other": "c-grey",
}

# Ordered keyword rules: first match wins. (regex-free substring match, lowercased)
TOPIC_RULES = [
    ("Music (Classical Remix)", ["remix", "liszt", "mozart", "tchaikovsky", "beethoven",
                                  "vivaldi", "chopin", "rhapsody", "swan lake", "mountain king",
                                  "nachtmusik", "classical goes"]),
    ("Governance & Geopolitics", ["governance", "geopolit", "sovereign", "framework 3.0",
                                   "regulation", "eu ai act", "policy", "congress", "china",
                                   "europe", "us-china", "transformative ai strategy"]),
    ("Consciousness & Mind", ["conscious", "alien mind", "have a mind", "does ai have a mind",
                               "inner life", "sentien", "disposition", "hard problem", "qualia",
                               "identity", "memento", "the borrowed self"]),
    ("AI Threats & Security", ["threat", "breach", "breakout", "broke out", "break out", "escape",
                                "sandbox", "hacker", "weaponiz", "exploit", "espionage", "attack",
                                "malware", "zero-day", "escaped"]),
    ("Alignment & Safety", ["alignment", "aligned", "misaligned", "safety", "lie", "cheat",
                             "deception", "deceive", "bengio", "welfare", "reasoning transparency",
                             "reading an ai", "reading a", "slow down", "warning", "ai risk",
                             "nash equilibrium", "game theory", "catch an ai"]),
    ("Economy & Work", ["job", "paycheck", "paid", "vibe cod", "economy", "labor", "labour",
                         "wellbeing", "coder", "employ", "wage", "hours a week", "productivity",
                         "r&d", "saves scientists", "runs 26"]),
    ("AI Agents & Capabilities", ["agent", "civilization", "arc-agi", "agi", "language", "lora",
                                   "rag", "cognitive", "capabilit", "swarm", "orchestrat",
                                   "benchmark", "gpt-", "open-weight", "open weight", "inference",
                                   "quantiz", "pace of ai", "measuring the pace", "billion ai"]),
]

# YouTube insightTrafficSourceType -> one of 4 buckets: [suggested, search, shorts, external]
SEARCH = {"YT_SEARCH"}
SHORTS = {"SHORTS"}
EXTERNAL = {"EXT_URL", "NO_LINK_OTHER", "NO_LINK_EMBEDDED"}
# everything else (RELATED_VIDEO, SUBSCRIBER, YT_CHANNEL, PLAYLIST, NOTIFICATION,
# END_SCREEN, BROWSE, YT_OTHER_PAGE, CAMPAIGN_CARD, ...) -> suggested/browse

# External referrer domain -> friendly label used on the page.
REFERRERS = [
    (["t.co", "twitter", "x.com"], "X / Twitter"),
    (["linkedin"], "LinkedIn"),
    (["google", "bing", "duckduckgo", "search"], "Search / Web"),
    (["whatsapp", "telegram", "messeng", "l.facebook", "lm.facebook"], "Messaging"),
]


def load_json(p, default):
    try:
        return json.load(open(p))
    except Exception:
        return default


def classify_topic(title, vid, overrides):
    if vid in overrides:
        return overrides[vid]
    t = title.lower()
    for topic, kws in TOPIC_RULES:
        if any(k in t for k in kws):
            return topic
    return "Other"


def bucket_traffic(rows):
    """rows: [[insightTrafficSourceType, views], ...] -> [sugg, search, shorts, ext]."""
    tb = [0, 0, 0, 0]
    for src, v in rows:
        v = int(v)
        if src in SEARCH:
            tb[1] += v
        elif src in SHORTS:
            tb[2] += v
        elif src in EXTERNAL:
            tb[3] += v
        else:
            tb[0] += v
    return tb


def label_referrer(domain):
    d = domain.lower()
    for keys, label in REFERRERS:
        if any(k in d for k in keys):
            return label
    return "Other sites"


def channel_uploads(yt, limit=None):
    """Return [(video_id, title, published, duration_s, is_short)] for the channel."""
    ch = yt.channels().list(part="contentDetails", mine=True).execute()
    uploads = ch["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
    vids, page = [], None
    while True:
        r = yt.playlistItems().list(part="contentDetails", playlistId=uploads,
                                     maxResults=50, pageToken=page).execute()
        vids += [it["contentDetails"]["videoId"] for it in r.get("items", [])]
        page = r.get("nextPageToken")
        if not page or (limit and len(vids) >= limit):
            break
    if limit:
        vids = vids[:limit]
    out = []
    for i in range(0, len(vids), 50):
        chunk = vids[i:i + 50]
        r = yt.videos().list(part="snippet,contentDetails", id=",".join(chunk)).execute()
        for it in r.get("items", []):
            dur = iso_dur(it["contentDetails"]["duration"])
            out.append((it["id"], it["snippet"]["title"],
                        it["snippet"]["publishedAt"][:10], dur, dur <= 60))
    return out


def iso_dur(s):
    """PT#M#S -> seconds."""
    import re
    m = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", s or "")
    if not m:
        return 0
    h, mi, se = (int(x) if x else 0 for x in m.groups())
    return h * 3600 + mi * 60 + se


def analytics_for(ya, vid, since):
    today = date.today().isoformat()

    def q(dims="", metrics="views", detail_filter=""):
        filt = f"video=={vid}" + (";" + detail_filter if detail_filter else "")
        try:
            return ya.reports().query(ids="channel==MINE", startDate=since, endDate=today,
                                      metrics=metrics, dimensions=dims, filters=filt,
                                      sort="-views", maxResults=25).execute().get("rows", [])
        except Exception as exc:
            print(f"      q({dims}/{metrics}): {str(exc)[:80]}", file=sys.stderr)
            return []

    # totals
    tot = q(metrics="views,estimatedMinutesWatched,averageViewDuration,"
                    "averageViewPercentage,estimatedRevenue")
    if tot:
        v, wmin, avd, avp, rev = tot[0]
        views, watch_min, avg_dur = int(v), float(wmin), int(float(avd))
        retention, revenue = round(float(avp)), round(float(rev), 3)
    else:
        views = watch_min = avg_dur = retention = revenue = 0
    tb = bucket_traffic([[s, vv] for s, vv in q(dims="insightTrafficSourceType")])
    geo_rows = q(dims="country")
    geo = geo_rows[0][0] if geo_rows else "-"
    er = {}
    for dom, vv in q(dims="insightTrafficSourceDetail", detail_filter="insightTrafficSourceType==EXT_URL"):
        er[label_referrer(dom)] = er.get(label_referrer(dom), 0) + int(vv)
    return {"v": views, "w": round(watch_min * 60), "a": avg_dur, "r": revenue,
            "ret": retention, "geo": geo, "tb": tb, "er": er}


def verdict_for(agg):
    """Rule-based verdict from a topic's aggregate: (label, pill-class)."""
    wh = agg["w"] / 3600.0            # watch hours
    ext_share = agg["e"] / max(agg["v"], 1)
    if wh >= 5 and ext_share >= 0.25:
        return ["Reach engine", "warm"]
    if wh >= 5:
        return ["Double down", "good"]
    if wh >= 1.5:
        return ["Promising", "good"]
    if agg["v"] >= 400:
        return ["Emerging", "warm"]
    return ["Base", "muted"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-push", action="store_true")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--since", default=None, help="floor start date; default = each video's publish date")
    args = ap.parse_args()

    comp = load_json(COMPILATIONS, {"categories": [], "topic_to_category": {}, "compilations": []})
    overrides = load_json(OVERRIDES, {})
    t2c = comp.get("topic_to_category", {})
    # video-title -> compilation label (published + queued both shown)
    title2comp = {}
    for c in comp.get("compilations", []):
        for m in c.get("members", []):
            title2comp[m.strip().lower()] = {"id": c["id"], "title": c["title"],
                                             "status": c["status"], "category": c["category"]}

    ya, yt = services()
    vids = channel_uploads(yt, args.limit)
    print(f"channel videos: {len(vids)}")

    videos = []
    for vid, title, pub, dur, is_short in vids:
        since = args.since or pub
        a = analytics_for(ya, vid, since)
        topic = classify_topic(title, vid, overrides)
        cat = t2c.get(topic, "others")
        cm = title2comp.get(title.strip().lower())
        videos.append({
            "t": title, "p": pub, "tp": topic, "tc": TOPIC_COLOR.get(topic, "c-grey"),
            "v": a["v"], "w": a["w"], "a": a["a"], "r": a["r"], "L": dur, "ret": a["ret"],
            "geo": a["geo"], "sh": is_short, "tb": a["tb"], "er": a["er"],
            "cat": cat, "comp": cm["title"] if cm else "", "comp_status": cm["status"] if cm else "",
        })
        print(f"  {a['v']:6} v  {topic:26} {title[:50]}")

    # per-topic aggregates -> verdicts
    agg = {}
    for x in videos:
        o = agg.setdefault(x["tp"], {"v": 0, "w": 0, "e": 0})
        o["v"] += x["v"]; o["w"] += x["w"]; o["e"] += x["tb"][3]
    verdicts = {tp: verdict_for(o) for tp, o in agg.items()}

    payload = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "categories": comp.get("categories", []),
        "topic_to_category": t2c,
        "compilations": comp.get("compilations", []),
        "verdicts": verdicts,
        "videos": videos,
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=1) + "\n")
    print(f"\nwrote {len(videos)} videos -> {OUT}  (generated_at {payload['generated_at']})")

    if not args.no_push:
        import subprocess
        r = subprocess.run(["scp", "-o", "StrictHostKeyChecking=accept-new", str(OUT), REMOTE])
        print("pushed to droplet" if r.returncode == 0 else "PUSH FAILED")


if __name__ == "__main__":
    main()
