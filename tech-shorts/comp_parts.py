#!/usr/bin/env python3
"""Resolve compilation parts to local masters and propose in/out trim points.

    python3 comp_parts.py C1 C2 C3          # report for the planned compilations
    python3 comp_parts.py --ids ID ID ...   # ad-hoc list of YouTube video ids

For each part it prints the master to cut from and the in/out seconds:

  * `raw_cinematic.mp4` (preferred) is the NotebookLM master -- no channel hook
    card, no SUBSCRIBE outro. in = 0, out = end of narration. That is exactly
    what a compilation chapter wants.
  * `final_long.mp4` is the published video, so it carries BOTH cards. in = end
    of the hook card (first scene cut after 3s), out = end of narration MINUS the
    outro card. Those bounds are a proposal -- eyeball every one of them with
    --frames before building, because the hook card length is not a constant
    (measured 18-24s for intro+outro across the archive).

Nothing is written or re-encoded here; this only reports.
"""
import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
JOBS = HERE / "jobs.json"

# The three compilations planned on 2026-10-24. Order is the running order.
PLAN = {
    "C1": ("AI Will Do the Work, Vol. 2", [
        "7UPyRA9cBtE", "lChiYc1A4B8", "Vritr444eKs", "jxi-GUpdhYI",
        "Miw8TeG3RFI", "JFhLTSY7Pxw"]),
    "C2": ("The Attack Surface in Your House", [
        "ECuneH0hPcg", "KbxsK1LlVSw", "n0J3a4-1rmY", "D-LV9YJN2ZM",
        "GLLa6t_MQuA", "lZ_LLtp8Ulo", "cRgmoG-XqkQ"]),
    "C3": ("Alien Minds, Vol. 2", [
        "ygFTq74Vs9I", "hRW9NgbagLU", "QKBBcGqJQ0I", "Z71EvBczPiQ",
        "ckNAJdh26Sg", "LCn_xfbxfeA"]),
}


def jobs():
    return json.load(open(JOBS))["jobs"]


def master(vid, js):
    """-> (path, kind, title). Prefers the raw NotebookLM master."""
    r = next((x for x in js if vid in json.dumps(x.get("youtube") or {})), None)
    if not r:
        return "", "", ""
    a = r.get("assets") or {}
    title = (r.get("youtube") or {}).get("title_long") or r.get("title") or r.get("slug")
    rc, fl = a.get("raw_cinematic_mp4") or "", a.get("final_long_mp4") or ""
    if rc and os.path.exists(rc):
        return rc, "raw_cinematic", title
    return fl, "final_long", title


def duration(p):
    o = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "default=nw=1:nk=1", p], capture_output=True, text=True)
    return float(o.stdout.strip() or 0)


def narration_end(p, d):
    """Start of the trailing silence that runs to EOF, else the full duration.

    Same idea as pipeline.content_audio_end, repeated here so this stays a
    standalone report that does not import the build pipeline.
    """
    err = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", p,
                          "-af", "silencedetect=noise=-35dB:d=0.6", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    starts = [float(m) for m in re.findall(r"silence_start: ([-\d.]+)", err)]
    ends = [float(m) for m in re.findall(r"silence_end: ([-\d.]+)", err)]
    if starts and ends and abs(ends[-1] - d) < 0.25:
        return starts[-1]
    return d


def first_scene_cut(p, after=3.0, before=40.0):
    """First hard cut between `after` and `before` seconds -- the hook card's end."""
    err = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", p,
                          "-vf", f"select='gt(scene,0.4)',metadata=print",
                          "-an", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    for m in re.finditer(r"pts_time:([\d.]+)", err):
        t = float(m.group(1))
        if after <= t <= before:
            return t
    return None


def report(vids, label=""):
    js = jobs()
    total = 0.0
    rows = []
    for vid in vids:
        p, kind, title = master(vid, js)
        if not p or not os.path.exists(p):
            rows.append((vid, "MISSING", 0, 0, 0, title)); continue
        d = duration(p)
        out = narration_end(p, d) + 0.15      # keep the tail of the last word
        if kind == "raw_cinematic":
            tin = 0.0
        else:
            tin = first_scene_cut(p) or 0.0
            # Note: pipeline.py's SUBSCRIBE outro card is 5s of silence (anullsrc),
            # so narration_end(p, d) already lands at the end of spoken narration
            # (~8.6s before EOF, prior to both NotebookLM trailing silence and the
            # silent SUBSCRIBE card). Only step back to a scene cut if narration_end
            # failed to strip the 5s outro card (i.e. d - out < 4.5s).
            if d - out < 4.5:
                cut = first_scene_cut(p, after=max(out - 12, 5), before=out)
                if cut and out - cut > 2:
                    out = cut
        out = min(out, d)
        total += max(0.0, out - tin)
        rows.append((vid, kind, tin, out, out - tin, title))
    if label:
        print(f"\n=== {label} ===")
    print(f"{'id':13} {'source':14} {'in':>7} {'out':>8} {'keeps':>8}  title")
    for vid, kind, tin, out, keep, title in rows:
        print(f"{vid:13} {kind:14} {tin:7.2f} {out:8.2f} {keep:8.2f}  {(title or '')[:52]}")
    print(f"{'':13} {'':14} {'':7} {'TOTAL':>8} {total:8.2f}s = {int(total//60)}m{int(total%60):02d}s")
    return total


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("which", nargs="*", default=["C1", "C2", "C3"])
    ap.add_argument("--ids", nargs="*", help="ad-hoc YouTube video ids instead of a plan key")
    args = ap.parse_args()
    if args.ids:
        report(args.ids, "ad-hoc")
        return
    for k in args.which:
        if k not in PLAN:
            print(f"unknown compilation {k!r}; known: {', '.join(PLAN)}", file=sys.stderr)
            continue
        name, vids = PLAN[k]
        report(vids, f"{k} -- {name}")


if __name__ == "__main__":
    main()
