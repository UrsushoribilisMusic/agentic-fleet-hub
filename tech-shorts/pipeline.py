#!/usr/bin/env python3
"""
tech-shorts pipeline coordinator (TS-0 EPIC).

Wires together: PIL card rendering + ElevenLabs VO + ffmpeg assembly →
YouTube upload → X cross-post.

Usage:
    python3 pipeline.py status                          # show all jobs
    python3 pipeline.py set-sources <job_id> --short P --long P
    python3 pipeline.py set-copy <job_id> --vo TEXT --hook-a-main T ...
    python3 pipeline.py run <job_id> [--stage build|localize|upload|post] [--dry-run]

Localization: set a job's `localize` (or youtube.localize_langs) to e.g.
["de","fr"] and a full `run` will, after build, produce native-voice dub audio
+ subtitles + translated title/description, then push the title/description and
captions to YouTube on upload (audio tracks still attach manually in Studio —
no public API). `--stage localize` forces it with the default languages.
"""

from __future__ import annotations

import argparse
import fcntl
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
JOBS_FILE = HERE / "jobs.json"
JOBS_LOCK = HERE / "jobs.lock"

# ElevenLabs voice for hook VO (Alice, British female)
ELEVENLABS_VOICE_ID = "Xb7hH8MSUJpSbSDYk0k2"
ELEVENLABS_MODEL = "eleven_multilingual_v2"

# Branding palette (RGB)
INK = (11, 29, 38)
RED = (232, 103, 77)
TEAL = (79, 209, 197)
MUTE = (157, 179, 184)
WHITE = (231, 241, 239)
COLOR_MAP = {"WHITE": WHITE, "RED": RED, "TEAL": TEAL, "MUTE": MUTE, "INK": INK}

FONT_PATH = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"

# YouTube channel key to use for tech-shorts uploads
YT_CHANNEL = "main"
YT_CATEGORY = "28"  # Science & Technology

# Paths
MUSIC_VIDEO_TOOL = HERE.parent.parent / "music-video-tool"
FLOTILLA_PUBLISHER = Path("/Users/miguelrodriguez/flotilla/publisher")

# Python interpreter that has whisper + anthropic + elevenlabs installed (used by
# the localize stage, which runs ASR/translate/TTS out-of-process).
LOCALIZE_VENV_PY = MUSIC_VIDEO_TOOL / ".venv312" / "bin" / "python3"
# Languages the localizer produces when a job opts in but doesn't name specific ones.
LOCALIZE_LANGS_DEFAULT = ["de", "fr"]


# ── Job I/O ──────────────────────────────────────────────────────────────────

def load_jobs() -> dict:
    with open(JOBS_FILE) as f:
        return json.load(f)


def save_jobs(data: dict) -> None:
    with open(JOBS_LOCK, "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            tmp = JOBS_FILE.with_suffix(".json.tmp")
            tmp.write_text(json.dumps(data, indent=4, ensure_ascii=False) + "\n")
            tmp.replace(JOBS_FILE)
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)


def find_job(data: dict, job_id: str) -> dict | None:
    for j in data["jobs"]:
        if j["id"] == job_id or j.get("slug") == job_id:
            return j
    return None


def update_job_field(job_id: str, **fields) -> None:
    data = load_jobs()
    job = find_job(data, job_id)
    if job is None:
        raise ValueError(f"Job not found: {job_id}")
    def _deep_set(target, source):
        for k, v in source.items():
            if isinstance(v, dict) and isinstance(target.get(k), dict):
                _deep_set(target[k], v)
            else:
                target[k] = v
    _deep_set(job, fields)
    import datetime
    job["updated_at"] = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    save_jobs(data)


# ── PIL card rendering ────────────────────────────────────────────────────────

def render_card(
    out_path: Path,
    lines: list[tuple[str, tuple, int, float]],
    width: int,
    height: int,
) -> None:
    """Render a single text card via Pillow.

    lines: list of (text, rgb_color, font_size, gap_frac)
      gap_frac = space to add BEFORE this line, as a fraction of height
                 (ignored for the first line; None → default 0.02).
    Lines are measured (ascent+descent) and stacked as one vertically-centred
    block, so they can never overlap regardless of font size or aspect ratio.
    """
    from PIL import Image, ImageDraw, ImageFont

    img = Image.new("RGB", (width, height), INK)
    dr = ImageDraw.Draw(img)

    bar_h = max(4, height // 180)
    dr.rectangle([0, 0, width, bar_h], fill=TEAL)
    dr.rectangle([0, height - bar_h, width, height], fill=RED)

    max_w = width * 0.92
    prepared = []
    total = 0.0
    for i, (text, color, size, gap_frac) in enumerate(lines):
        font = ImageFont.truetype(FONT_PATH, size)
        # Shrink to fit the card width so long lines never spill off the edges.
        while size > 10 and dr.textlength(text, font=font) > max_w:
            size -= 2
            font = ImageFont.truetype(FONT_PATH, size)
        ascent, descent = font.getmetrics()
        line_h = ascent + descent
        gap = 0.0 if i == 0 else (gap_frac if gap_frac is not None else 0.02) * height
        prepared.append((text, color, font, line_h, gap))
        total += line_h + gap

    y = (height - total) / 2
    for text, color, font, line_h, gap in prepared:
        y += gap
        dr.text((width / 2, y), text, font=font, fill=color, anchor="ma")
        y += line_h

    img.save(str(out_path))


def build_hook_cards(job: dict, workdir: Path, w: int, h: int) -> tuple[Path, Path]:
    """Render hook card A and B from job.hook_copy."""
    hc = job["hook_copy"]
    big = w // 8
    med = w // 18
    sm = w // 30

    card_a_lines = [
        (hc["card_a_main"], WHITE, big, None),
        (hc["card_a_sub"], RED, big, 0.01),
        (hc["card_a_footer"], MUTE, sm, 0.07),
    ]
    card_b_lines = [
        (hc["card_b_main"], WHITE, med, None),
        (hc["card_b_sub"], WHITE, med, 0.015),
        (hc["card_b_footer"], TEAL, sm, 0.07),
    ]

    a = workdir / "hookA.png"
    b = workdir / "hookB.png"
    render_card(a, card_a_lines, w, h)
    render_card(b, card_b_lines, w, h)
    return a, b


# Default outro: keep viewers ON YouTube (subscribe + watch-next) rather than
# sending them off-platform. An outbound link in the outro costs session time —
# the exact signal the recommendation engine rewards — and we're growing the
# Classical Remix channel's audience in place, not driving traffic elsewhere.
# Per-job outro_copy keys override these defaults.
DEFAULT_OUTRO = {
    "title": "SUBSCRIBE",
    "subtitle": "for more AI explainers",
    "tagline": "AI-generated music and tech, every week",
    "url": "The Classical Remix",
    "cta": "Like, subscribe, and watch the next one",
}


def build_outro_card(job: dict, workdir: Path, w: int, h: int) -> Path:
    """Render outro card from job.outro_copy (falls back to DEFAULT_OUTRO)."""
    oc = {**DEFAULT_OUTRO, **(job.get("outro_copy") or {})}
    big = w // 8
    med = w // 18
    sm = w // 30

    outro_lines = [
        (oc["title"], TEAL, big, None),
        (oc["subtitle"], WHITE, med, 0.03),
        (oc["tagline"], MUTE, sm, 0.05),
        (oc["url"], TEAL, med, 0.05),
        (oc["cta"], WHITE, sm, 0.05),
    ]

    path = workdir / "outro.png"
    render_card(path, outro_lines, w, h)
    return path


# ── ElevenLabs VO ────────────────────────────────────────────────────────────

def generate_vo(text: str, out_path: Path) -> None:
    """Generate hook VO via ElevenLabs API (Alice, British female)."""
    api_key = os.environ.get("ELEVENLABS_API_KEY", "")
    if not api_key:
        env_file = MUSIC_VIDEO_TOOL / ".env"
        if env_file.exists():
            for line in env_file.read_text().splitlines():
                if line.startswith("ELEVENLABS_API_KEY="):
                    api_key = line.split("=", 1)[1].strip()
                    break

    if not api_key:
        raise RuntimeError("ELEVENLABS_API_KEY not found in env or music-video-tool/.env")

    try:
        from elevenlabs.client import ElevenLabs
    except ImportError:
        raise RuntimeError("elevenlabs not installed — run: pip install elevenlabs")

    client = ElevenLabs(api_key=api_key)
    audio_iter = client.text_to_speech.convert(
        voice_id=ELEVENLABS_VOICE_ID,
        text=text,
        model_id=ELEVENLABS_MODEL,
        output_format="mp3_44100_128",
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "wb") as f:
        for chunk in audio_iter:
            f.write(chunk)
    print(f"  VO written: {out_path} ({out_path.stat().st_size // 1024}KB)")


# ── ffmpeg assembly ───────────────────────────────────────────────────────────

def ffprobe(path: Path, field: str) -> str:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", f"stream={field}", "-of", "csv=p=0", str(path)],
        check=True, capture_output=True, text=True,
    )
    return result.stdout.strip()


def run_ffmpeg(*args: str) -> None:
    subprocess.run(["ffmpeg", "-y"] + list(args) + ["-loglevel", "error"], check=True)


def card_to_segment(png: Path, duration: float, fade_out_start: float, fps: int, workdir: Path, name: str) -> Path:
    out = workdir / name
    run_ffmpeg(
        "-loop", "1", "-i", str(png),
        "-t", str(duration), "-r", str(fps), "-an",
        "-vf", f"fade=t=in:st=0:d=0.3,fade=t=out:st={fade_out_start:.2f}:d=0.35,format=yuv420p",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", str(out),
    )
    return out


def assemble_video(
    src: Path,
    hook_a_png: Path,
    hook_b_png: Path,
    outro_png: Path,
    vo_mp3: Path | None,
    out: Path,
    workdir: Path,
    trim_s: float = 0.0,
) -> None:
    w = int(ffprobe(src, "width"))
    h = int(ffprobe(src, "height"))
    fps_raw = ffprobe(src, "r_frame_rate")
    fps = int(fps_raw.split("/")[0])
    print(f"  source: {w}x{h} @ {fps}fps")

    # Intro duration = VO length if supplied, else 7s
    if vo_mp3 and vo_mp3.exists():
        dur_res = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=nk=1:nw=1", str(vo_mp3)],
            check=True, capture_output=True, text=True,
        )
        intro_dur = float(dur_res.stdout.strip())
    else:
        intro_dur = 7.0

    d1 = intro_dur * 0.48
    d2 = intro_dur - d1

    seg_a = card_to_segment(hook_a_png, d1, max(0, d1 - 0.35), fps, workdir, "seg_a.mp4")
    seg_b = card_to_segment(hook_b_png, d2, max(0, d2 - 0.35), fps, workdir, "seg_b.mp4")

    # Concat card segments
    intro_v = workdir / "introv.mp4"
    run_ffmpeg(
        "-i", str(seg_a), "-i", str(seg_b),
        "-filter_complex", "[0:v][1:v]concat=n=2:v=1[v]",
        "-map", "[v]", "-r", str(fps), "-c:v", "libx264", "-pix_fmt", "yuv420p",
        str(intro_v),
    )

    # Attach audio (VO or silence)
    intro_mp4 = workdir / "intro.mp4"
    if vo_mp3 and vo_mp3.exists():
        run_ffmpeg(
            "-i", str(intro_v), "-i", str(vo_mp3),
            "-map", "0:v", "-map", "1:a",
            "-c:v", "copy", "-c:a", "aac", "-ar", "44100", "-ac", "1", "-shortest",
            str(intro_mp4),
        )
    else:
        run_ffmpeg(
            "-i", str(intro_v),
            "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono",
            "-map", "0:v", "-map", "1:a", "-shortest",
            "-c:v", "copy", "-c:a", "aac",
            str(intro_mp4),
        )

    # Outro (5s, silent)
    outro_mp4 = workdir / "outro.mp4"
    run_ffmpeg(
        "-loop", "1", "-i", str(outro_png),
        "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono",
        "-t", "5",
        "-vf", "fade=t=in:st=0:d=0.3,fade=t=out:st=4.6:d=0.4,format=yuv420p",
        "-r", str(fps), "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-ar", "44100", "-ac", "1",
        str(outro_mp4),
    )

    # Normalize source (optionally trim NotebookLM end-card)
    src_norm = workdir / "src.mp4"
    trim_args: list[str] = []
    if trim_s > 0:
        dur_res = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=nk=1:nw=1", str(src)],
            check=True, capture_output=True, text=True,
        )
        src_dur = float(dur_res.stdout.strip())
        keep = max(0.0, src_dur - trim_s)
        trim_args = ["-t", f"{keep:.3f}"]
        print(f"  trimming {trim_s}s end-card (keep {keep:.1f}s of {src_dur:.1f}s)")
    run_ffmpeg(
        "-i", str(src),
        *trim_args,
        "-vf", f"scale={w}:{h}", "-r", str(fps),
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-ar", "44100", "-ac", "1",
        str(src_norm),
    )

    # Final concat: intro + src + outro
    run_ffmpeg(
        "-i", str(intro_mp4), "-i", str(src_norm), "-i", str(outro_mp4),
        "-filter_complex", "[0:v][0:a][1:v][1:a][2:v][2:a]concat=n=3:v=1:a=1[v][a]",
        "-map", "[v]", "-map", "[a]",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-ar", "44100",
        str(out),
    )
    print(f"  assembled: {out}")


# ── Build stage ───────────────────────────────────────────────────────────────

def stage_build(job: dict, dry_run: bool) -> None:
    job_id = job["id"]
    hc = job.get("hook_copy", {})
    if not all(k in hc for k in ("card_a_main", "card_a_sub", "card_a_footer",
                                  "card_b_main", "card_b_sub", "card_b_footer")):
        raise ValueError("hook_copy is incomplete — run set-copy first")

    # Accept both legacy (raw_short/long_mp4) and canonical store names (raw_short/raw_cinematic_mp4)
    assets = job["assets"]
    raw_short = assets.get("raw_short_mp4", "")
    raw_long = assets.get("raw_long_mp4", "") or assets.get("raw_cinematic_mp4", "")
    # The long/Cinematic is required; the Short is optional so a job can ship the
    # long alone (e.g. when NotebookLM quota hasn't yielded the Short yet). Add the
    # Short later by setting raw_short_mp4 and re-running build/upload.
    if not raw_long:
        raise ValueError("raw_long/raw_cinematic path not set — run set-sources or store-raw first")

    src_long = Path(raw_long)
    if not src_long.exists():
        raise FileNotFoundError(f"Long/Cinematic source not found: {src_long}")

    src_short = Path(raw_short) if raw_short else None
    if src_short and not src_short.exists():
        raise FileNotFoundError(f"Short source not found: {src_short}")
    build_short = src_short is not None

    if dry_run:
        which = f"{src_short} and {src_long}" if build_short else f"{src_long} (long only, no Short)"
        print(f"[dry-run] would build from {which}")
        return

    # Determine output directory: prefer asset store, fall back to HERE
    store_dir = assets.get("store_dir", "")
    if store_dir and Path(store_dir).is_dir():
        out_dir = Path(store_dir)
    else:
        try:
            from asset_store import asset_dir as _asset_dir
            out_dir = _asset_dir(job)
        except ImportError:
            out_dir = HERE

    # VO: generate if not already present
    vo_path = out_dir / f"{job['slug']}_hook_vo.mp3"
    if not vo_path.exists():
        # Fallback to legacy location
        legacy_vo = HERE / "assets" / f"{job['slug']}_hook_vo.mp3"
        if legacy_vo.exists():
            vo_path = legacy_vo
        elif hc.get("vo_text"):
            print(f"  generating ElevenLabs VO...")
            generate_vo(hc["vo_text"], vo_path)
        else:
            vo_path = None
            print("  no vo_text set, building silent hook")
    else:
        print(f"  reusing VO: {vo_path}")

    # Existing hand-built VO fallback
    if vo_path is None:
        existing_vo = assets.get("hook_vo_audio", "")
        if existing_vo and Path(existing_vo).exists():
            vo_path = Path(existing_vo)
        elif existing_vo and (HERE / existing_vo).exists():
            vo_path = HERE / existing_vo

    trim_s = float(job.get("trim_s", 0))
    final_short = out_dir / "final_short.mp4"
    final_long = out_dir / "final_long.mp4"

    if build_short:
        with tempfile.TemporaryDirectory(prefix="ts_build_") as tmp:
            workdir = Path(tmp)
            ws = int(ffprobe(src_short, "width"))
            hs = int(ffprobe(src_short, "height"))
            hook_a, hook_b = build_hook_cards(job, workdir, ws, hs)
            outro = build_outro_card(job, workdir, ws, hs)
            print(f"  cards rendered {ws}x{hs}")
            (workdir / "short").mkdir()
            assemble_video(src_short, hook_a, hook_b, outro, vo_path, final_short, workdir / "short", trim_s)
    else:
        print("  no Short source — building long only")

    with tempfile.TemporaryDirectory(prefix="ts_build_long_") as tmp:
        workdir = Path(tmp)
        wl = int(ffprobe(src_long, "width"))
        hl = int(ffprobe(src_long, "height"))
        hook_a, hook_b = build_hook_cards(job, workdir, wl, hl)
        outro = build_outro_card(job, workdir, wl, hl)
        print(f"  cards rendered {wl}x{hl}")
        (workdir / "long").mkdir()
        assemble_video(src_long, hook_a, hook_b, outro, vo_path, final_long, workdir / "long", trim_s)

    update_job_field(
        job_id,
        status="assembled",
        assets={
            **assets,
            "store_dir": str(out_dir),
            "hook_vo_audio": str(vo_path) if vo_path else "",
            "final_short_mp4": str(final_short) if build_short else assets.get("final_short_mp4", ""),
            "final_long_mp4": str(final_long),
        },
    )
    print(f"  job {job_id} → assembled ({out_dir}){'' if build_short else ' [long only]'}")


# ── Localize stage ──────────────────────────────────────────────────────────

def job_localize_langs(job: dict) -> list[str]:
    """Languages this job opts into for localization.

    Opt-in is explicit so a full `run` never spends ElevenLabs credits by
    surprise: set either top-level `localize` or `youtube.localize_langs` to a
    list like ["de", "fr"]. Returns [] when the job hasn't opted in.
    """
    langs = job.get("localize") or job.get("youtube", {}).get("localize_langs") or []
    return [str(l).strip() for l in langs if str(l).strip()]


def stage_localize(job: dict, dry_run: bool, forced: bool = False) -> None:
    """Produce per-language dub audio + subtitles + translated title/description.

    Runs on the FINAL long video (so the dub track lines up with the intro hook,
    content, and outro). Records everything under job.youtube.localizations, which
    stage_upload then pushes to YouTube via the Data API.

    Skipped (no cost) unless the job opts in via job['localize'] / youtube
    ['localize_langs'] — except when run explicitly as `--stage localize`
    (forced=True), which falls back to the default languages.
    """
    job_id = job["id"]
    langs = job_localize_langs(job) or (LOCALIZE_LANGS_DEFAULT if forced else [])
    if not langs:
        print("  no localize languages set for this job — skipping "
              "(set job['localize']=['de','fr'] to opt in, or run --stage localize)")
        return

    final_long = job["assets"].get("final_long_mp4", "")
    if not final_long or not Path(final_long).exists():
        raise FileNotFoundError(f"final_long_mp4 not found: {final_long!r} — run build stage first")

    if not LOCALIZE_VENV_PY.exists():
        raise FileNotFoundError(
            f"localizer interpreter not found: {LOCALIZE_VENV_PY}\n"
            "It needs whisper + anthropic + elevenlabs (music-video-tool/.venv312)."
        )

    out_dir = Path(job["assets"].get("store_dir") or HERE)

    if dry_run:
        print(f"[dry-run] would localize {final_long} into {langs} → {out_dir}")
        return

    print(f"  localizing into {langs} (this uses ElevenLabs credits)...")
    proc = subprocess.run(
        [str(LOCALIZE_VENV_PY), str(HERE / "localize.py"),
         job_id, str(out_dir), final_long, ",".join(langs)],
        capture_output=True, text=True,
    )
    sys.stdout.write(proc.stdout)
    if proc.returncode != 0:
        sys.stderr.write(proc.stderr)
        raise RuntimeError(f"localize.py failed (exit {proc.returncode})")

    result = None
    for line in proc.stdout.splitlines():
        if line.startswith("RESULT_JSON:"):
            result = json.loads(line[len("RESULT_JSON:"):])
    if result is None:
        raise RuntimeError("localize.py produced no RESULT_JSON")

    yt = dict(job.get("youtube", {}))
    existing = dict(yt.get("localizations") or {})
    existing.update(result.get("localizations", {}))
    yt["localizations"] = existing
    if result.get("captions_en_srt"):
        yt["captions_en_srt"] = result["captions_en_srt"]
    update_job_field(job_id, youtube=yt)
    print(f"  job {job_id} → localized ({', '.join(existing.keys())})")
    print("  NOTE: alternate AUDIO tracks have no public YouTube API — attach the "
          ".m4a files in Studio → Languages manually. Title/desc + captions are "
          "pushed automatically on upload.")


# ── Upload stage ──────────────────────────────────────────────────────────────

def push_localizations(svc, video_id: str, job: dict) -> None:
    """Push localized title/description (all langs) + captions (per lang) to a
    freshly uploaded video via the YouTube Data API.

    - Title/description: videos.update with a read-modify-write of snippet +
      localizations, preserving defaultLanguage=en. Works with the `youtube`
      scope the token already has.
    - Captions: captions.insert per language from the .srt. Needs the
      `youtube.force-ssl` scope; if the token lacks it the call 403s, which we
      report once (non-fatal) with the re-consent instruction rather than failing
      the whole upload.
    """
    locs = (job.get("youtube", {}) or {}).get("localizations") or {}
    if not locs:
        return

    # --- localized title/description ---
    try:
        items = svc.videos().list(part="snippet,localizations", id=video_id).execute().get("items", [])
        if items:
            sn = items[0]["snippet"]
            loc_body = dict(items[0].get("localizations") or {})
            for lang, meta in locs.items():
                if meta.get("title") or meta.get("description"):
                    loc_body[lang] = {
                        "title": (meta.get("title") or sn["title"])[:100],
                        "description": (meta.get("description") or sn["description"])[:4900],
                    }
            new_sn = {"title": sn["title"], "description": sn["description"],
                      "categoryId": sn["categoryId"], "defaultLanguage": "en"}
            if sn.get("tags"):
                new_sn["tags"] = sn["tags"]
            svc.videos().update(part="snippet,localizations",
                                body={"id": video_id, "snippet": new_sn,
                                      "localizations": loc_body}).execute()
            print(f"    localized title/desc pushed: {', '.join(loc_body.keys())}")
    except Exception as exc:
        print(f"    WARNING: localized title/desc push failed (non-fatal): {exc}")

    # --- captions per language ---
    from googleapiclient.http import MediaFileUpload  # type: ignore
    for lang, meta in locs.items():
        srt = meta.get("srt")
        if not srt or not Path(srt).exists():
            continue
        try:
            svc.captions().insert(
                part="snippet",
                body={"snippet": {"videoId": video_id, "language": lang,
                                  "name": "", "isDraft": False}},
                media_body=MediaFileUpload(srt, mimetype="application/octet-stream"),
            ).execute()
            print(f"    caption uploaded: {lang}")
        except Exception as exc:
            msg = str(exc)
            if "insufficient" in msg.lower() or "forbidden" in msg.lower() or "403" in msg:
                print("    NOTE: caption upload needs the 'youtube.force-ssl' scope. "
                      "One-time re-consent: delete music-video-tool/youtube_token.pickle "
                      "and re-run the auth flow, then re-push captions. "
                      f"({lang} .srt staged at {srt})")
                break
            print(f"    WARNING: caption upload failed for {lang} (non-fatal): {exc}")


def stage_upload(job: dict, dry_run: bool) -> None:
    job_id = job["id"]
    final_short = job["assets"].get("final_short_mp4", "")
    final_long = job["assets"].get("final_long_mp4", "")

    if not final_long or not Path(final_long).exists():
        raise FileNotFoundError(f"final_long_mp4 not found: {final_long!r} — run build stage first")
    # Short is optional: upload just the long when there is no built Short (e.g. a
    # long-only run). The Short can be uploaded later by building + re-running upload.
    upload_short = bool(final_short and Path(final_short).exists())

    # Idempotency: never re-upload a cut that already has a YouTube id/url on the job.
    # This makes "ship long-only now, add the Short later" safe — re-running upload
    # uploads only the missing cut instead of creating a duplicate long video.
    prev_yt = job.get("youtube", {}) or {}
    already_long = bool(prev_yt.get("long_id") and prev_yt.get("long_url"))
    already_short = bool(prev_yt.get("short_id") and prev_yt.get("short_url"))

    title_short = job.get("youtube", {}).get("title_short") or f"{job['title']} | #Shorts"
    title_long = job.get("youtube", {}).get("title_long") or job["title"]
    description = (
        job.get("youtube", {}).get("description")
        or f"{job.get('idea_notes', '')}\n\nGenerated by Canis AI pipeline."
    )
    tags = job.get("youtube", {}).get("tags") or job.get("tags", [])
    # Privacy: default private (safe); a job can opt into public via youtube.privacy.
    privacy = (job.get("youtube", {}).get("privacy") or "private").strip()
    if privacy not in ("private", "unlisted", "public"):
        raise ValueError(f"invalid youtube.privacy: {privacy!r}")

    if dry_run:
        print(f"[dry-run] would upload ({privacy}):")
        if upload_short:
            print(f"  short: {final_short}  title: {title_short}")
        else:
            print(f"  short: (none — long only)")
        print(f"  long:  {final_long}   title: {title_long}")
        return

    # Inject music-video-tool on path
    sys.path.insert(0, str(MUSIC_VIDEO_TOOL))
    from youtube_uploader import upload_video  # type: ignore

    short_id = ""
    short_url = ""
    if already_short:
        short_id, short_url = prev_yt.get("short_id", ""), prev_yt.get("short_url", "")
        print(f"  short already uploaded, skipping: {short_url}")
    elif upload_short:
        print(f"  uploading short...")
        short_result = upload_video(
            video_path=final_short,
            title=title_short,
            description=description,
            privacy_status=privacy,
            tags=tags,
            category_id=YT_CATEGORY,
            channel=YT_CHANNEL,
        )
        short_id = short_result.get("id", "")
        short_url = short_result.get("url", f"https://youtu.be/{short_id}")
        if not short_id:
            short_id = youtube_video_id(short_url)
        print(f"  short uploaded: {short_url}")
    else:
        print("  no built Short — uploading long only")

    long_freshly_uploaded = False
    if already_long:
        long_id, long_url = prev_yt.get("long_id", ""), prev_yt.get("long_url", "")
        print(f"  long already uploaded, skipping: {long_url}")
    else:
        print(f"  uploading long...")
        long_result = upload_video(
            video_path=final_long,
            title=title_long,
            description=description,
            privacy_status=privacy,
            tags=tags,
            category_id=YT_CATEGORY,
            channel=YT_CHANNEL,
        )
        long_id = long_result.get("id", "")
        long_url = long_result.get("url", f"https://youtu.be/{long_id}")
        if not long_id:  # some uploader return shapes carry only the URL
            long_id = youtube_video_id(long_url)
        long_freshly_uploaded = True
        print(f"  long uploaded: {long_url}")

    # Push localized title/description + captions to the long video (the dub is
    # timed to the long content). Only on a fresh long upload; no-op without localizations.
    if long_freshly_uploaded and (job.get("youtube", {}) or {}).get("localizations") and long_id:
        try:
            from youtube_uploader import (  # type: ignore
                get_authenticated_service, channel_token_path,
            )
            svc = get_authenticated_service(token_path=channel_token_path(YT_CHANNEL))
            print("  pushing localizations to long video...")
            push_localizations(svc, long_id, job)
        except Exception as exc:
            print(f"  WARNING: localization push skipped (non-fatal): {exc}")

    yt_update = {
        **job.get("youtube", {}),
        "long_id": long_id,
        "long_url": long_url,
    }
    if upload_short:  # don't clobber an existing short_url on a long-only run
        yt_update["short_id"] = short_id
        yt_update["short_url"] = short_url
    update_job_field(job_id, status="uploaded", youtube=yt_update)

    # TS-12: record canonical YouTube URLs in the asset store record
    try:
        from asset_store import sync_record
        sync_record(job_id, youtube=yt_update)
    except Exception:
        pass  # non-fatal — URLs already in jobs.json via update_job_field above

    print(f"  job {job_id} → uploaded")
    print(f"  IMPORTANT: open YouTube Studio and enable 'Altered content' on both videos before publishing.")


# ── Post stage ────────────────────────────────────────────────────────────────

def contains_url_text(text: str) -> bool:
    """True if the text carries an outbound link.

    Mirrors flotilla_publisher.x_client.contains_url, but is duplicated here so
    the FLOT-118 guard runs during --dry-run too, before any credential loading.
    """
    import re
    return bool(re.search(r"(https?://|www\.)\S+", text or ""))


def youtube_video_id(url: str) -> str:
    """Extract the video id from a watch?v= or youtu.be URL."""
    import re
    m = re.search(r"(?:watch\?v=|youtu\.be/|/shorts/)([\w-]+)", url or "")
    return m.group(1) if m else ""


def assert_youtube_public(url: str) -> None:
    """Refuse to advertise a video that is not public.

    stage_post used to take a URL straight from the job record and post it,
    never asking YouTube whether the video was actually watchable. Uploads are
    created private, so the window between upload and publishing is exactly when
    a cross-post goes out pointing at a video nobody but the owner can open —
    and the first hours are when a post gets its reach. This closes that.
    """
    vid = youtube_video_id(url)
    if not vid:
        raise ValueError(f"Could not parse a YouTube video id from: {url!r}")

    sys.path.insert(0, str(MUSIC_VIDEO_TOOL))
    from youtube_uploader import (  # type: ignore
        get_authenticated_service,
        channel_token_path,
    )

    svc = get_authenticated_service(token_path=channel_token_path(YT_CHANNEL))
    items = svc.videos().list(part="status", id=vid).execute().get("items", [])
    if not items:
        raise ValueError(
            f"YouTube video {vid} not found on channel '{YT_CHANNEL}'. "
            "Refusing to post a link that may 404."
        )
    status = items[0]["status"]
    privacy = status.get("privacyStatus")
    if privacy != "public":
        raise ValueError(
            f"YouTube video {vid} is '{privacy}', not public. Refusing to post.\n"
            f"  {url}\n"
            "Publish it in YouTube Studio first, then re-run --stage post.\n"
            "(Posting now would advertise a video nobody can watch, and the "
            "post's first hours are when it gets its reach.)"
        )
    if status.get("uploadStatus") != "processed":
        raise ValueError(
            f"YouTube video {vid} uploadStatus is "
            f"'{status.get('uploadStatus')}', not 'processed'. Refusing to post."
        )


def clean_source_url(url: str) -> str:
    """Drop tracking params (utm_*, ref, fbclid, …) from a source URL so the
    cited link is the clean canonical one (e.g. the arXiv abs page, not
    ?ref=aisecret.us)."""
    url = (url or "").strip()
    if "?" not in url:
        return url
    base, _, query = url.partition("?")
    kept = []
    for part in query.split("&"):
        key = part.split("=", 1)[0].lower()
        if key in ("ref", "fbclid", "gclid", "mc_cid", "mc_eid") or key.startswith("utm_"):
            continue
        if part:
            kept.append(part)
    return base + ("?" + "&".join(kept) if kept else "")


def build_source_reply(job: dict) -> str:
    """Compose the source-attribution reply for the X thread.

    Cites the origin material (job['source_urls']) and credits the authors
    (job['source_authors'], typically @handles). Returns "" when there is
    nothing to cite, so the extra reply is only posted for jobs that actually
    carry a source — no cost or behaviour change for jobs without one.

    An explicit job['x_post']['source_reply_text'] overrides the auto-composed
    text (mirrors how reply_text can be overridden).
    """
    override = (job.get("x_post", {}) or {}).get("source_reply_text")
    if override is not None:
        return override.strip()

    urls = [clean_source_url(u) for u in (job.get("source_urls") or []) if u]
    authors = [a.strip() for a in (job.get("source_authors") or []) if a and a.strip()]
    if not urls and not authors:
        return ""

    lines = []
    if urls:
        lines.append("Source: " + " ".join(urls))
    if authors:
        lines.append("By " + ", ".join(authors))
    return "\n".join(lines)


def stage_post(job: dict, dry_run: bool) -> None:
    job_id = job["id"]
    yt = job.get("youtube", {}) or {}
    yt_url = yt.get("short_url") or yt.get("long_url")
    if not yt_url:
        raise ValueError("No YouTube URL found — run upload stage first")

    # FLOT-118 link-in-reply: the URL NEVER goes in the main post.
    #   cost  — a post containing a link is $0.20; hook + link-in-reply is
    #           $0.015 + $0.015, ~13x cheaper.
    #   reach — X deprioritises posts that carry an outbound link.
    # So the caption is the hook alone, and the link follows as a reply.
    caption_template = job.get("x_post", {}).get("caption") or job["title"]
    caption = caption_template.replace("{yt_url}", "").strip()
    reply_text = job.get("x_post", {}).get("reply_text") or yt_url
    # Attribution reply (source material + author handles). Empty for jobs
    # with no source, in which case no extra reply is posted.
    source_reply = build_source_reply(job)

    if contains_url_text(caption):
        raise ValueError(
            "X caption contains a URL. FLOT-118 requires the link to go in the "
            "reply, not the main post (13x cost, and X suppresses link posts). "
            "Remove the URL from the caption; the reply carries it."
        )

    # Preflight the link BEFORE spending anything. Runs in dry-run too, so the
    # rehearsal actually rehearses the thing most likely to be wrong.
    for link in set(re.findall(r"https?://\S+", reply_text)) or {reply_text}:
        if "youtu" in link:
            assert_youtube_public(link)
    print("  preflight: target video is public")

    if dry_run:
        print("[dry-run] would post to X (link-in-reply):")
        print(f"  post : {caption}")
        print(f"  reply: {reply_text}")
        if source_reply:
            print(f"  reply(source): {source_reply}")
        return

    # Inject flotilla publisher on path
    sys.path.insert(0, str(FLOTILLA_PUBLISHER))
    from flotilla_publisher.x_client import build_client  # type: ignore

    # --- X credential loading (Infisical) — headless-safe setup ---
    # 1. launchd/cron hand us a minimal PATH without Homebrew, so the `infisical`
    #    CLI isn't found. Restore it.
    for _p in ("/opt/homebrew/bin", "/usr/local/bin"):
        if _p not in os.environ.get("PATH", "").split(":") and os.path.isdir(_p):
            os.environ["PATH"] = _p + ":" + os.environ.get("PATH", "")
    # 2. X keys live at the ROOT of the UrsusFleet Infisical project (dev env),
    #    not the x_client default /flotilla/x.
    os.environ.setdefault("X_SECRET_PATH", "/")
    # 3. Run build_client from the publisher dir so infisical resolves the project
    #    from its .infisical.json (UrsusFleet); restore cwd afterwards.
    _cwd = os.getcwd()
    try:
        os.chdir(FLOTILLA_PUBLISHER)
        client = build_client()
    finally:
        os.chdir(_cwd)
    from flotilla_publisher.x_client import extract_tweet_id  # type: ignore

    print(f"  posting to X: {caption[:80]}...")
    resp = client.create_post(caption)
    tweet_id = extract_tweet_id(resp)
    post_url = f"https://x.com/i/web/status/{tweet_id}"
    print(f"  posted: {post_url}")

    # The main post is already public and paid for. If the reply fails, record
    # the main post before raising — otherwise a retry would double-post the
    # hook, and the operator would have no record of what actually shipped.
    reply_id = ""
    reply_url = ""
    try:
        print(f"  replying with link: {reply_text}")
        reply_resp = client.create_post(reply_text, reply_to_tweet_id=tweet_id)
        reply_id = extract_tweet_id(reply_resp)
        reply_url = f"https://x.com/i/web/status/{reply_id}"
        print(f"  replied: {reply_url}")
    except Exception as exc:
        update_job_field(
            job_id,
            x_post={
                **job.get("x_post", {}),
                "post_id": tweet_id,
                "post_url": post_url,
                "caption": caption,
                "reply_error": str(exc),
            },
        )
        raise RuntimeError(
            f"Main X post published ({post_url}) but the link reply FAILED: {exc}\n"
            f"The hook is live with no link. Reply manually with: {reply_text}\n"
            f"Do NOT re-run --stage post; it would post the hook a second time."
        ) from exc

    # Source-attribution reply, threaded under the link reply. Non-critical:
    # the hook + link already shipped, so a failure here is logged, not raised
    # (and it never re-posts the hook). Only runs when there is a source to cite.
    source_reply_id = ""
    source_reply_url = ""
    if source_reply:
        try:
            print(f"  replying with source: {source_reply[:80].replace(chr(10), ' / ')}")
            sr_resp = client.create_post(source_reply, reply_to_tweet_id=reply_id or tweet_id)
            source_reply_id = extract_tweet_id(sr_resp)
            source_reply_url = f"https://x.com/i/web/status/{source_reply_id}"
            print(f"  source replied: {source_reply_url}")
        except Exception as exc:
            print(f"  WARNING: source-credit reply failed (non-fatal): {exc}")

    published_xp = {
        **job.get("x_post", {}),
        "post_id": tweet_id,
        "post_url": post_url,
        "caption": caption,
        "reply_id": reply_id,
        "reply_url": reply_url,
        "reply_text": reply_text,
    }
    if source_reply:
        published_xp["source_reply_text"] = source_reply
        published_xp["source_reply_id"] = source_reply_id
        published_xp["source_reply_url"] = source_reply_url
    update_job_field(job_id, status="published", x_post=published_xp)
    print(f"  job {job_id} → published")


# ── CLI ───────────────────────────────────────────────────────────────────────

def cmd_status(args: argparse.Namespace) -> None:
    data = load_jobs()
    jobs = data["jobs"]
    if args.job_id:
        jobs = [j for j in jobs if j["id"] == args.job_id or j.get("slug") == args.job_id]
    for j in jobs:
        yt = j.get("youtube", {})
        xp = j.get("x_post", {})
        print(f"[{j['status']:16s}] {j['id']}")
        print(f"    title: {j['title']}")
        print(f"    raw_short: {j['assets'].get('raw_short_mp4') or '(not set)'}")
        print(f"    final_short: {j['assets'].get('final_short_mp4') or '(not built)'}")
        print(f"    yt_short: {yt.get('short_url') or '(not uploaded)'}")
        print(f"    x_post: {xp.get('post_url') or '(not posted)'}")
        print()


def cmd_set_sources(args: argparse.Namespace) -> None:
    data = load_jobs()
    job = find_job(data, args.job_id)
    if job is None:
        sys.exit(f"Job not found: {args.job_id}")
    updates: dict = {"assets": {**job["assets"], "raw_short_mp4": args.short, "raw_long_mp4": args.long}}
    if args.trim is not None:
        updates["trim_s"] = float(args.trim)
    update_job_field(args.job_id, **updates)
    print(f"Sources set for {args.job_id}")


def cmd_set_copy(args: argparse.Namespace) -> None:
    data = load_jobs()
    job = find_job(data, args.job_id)
    if job is None:
        sys.exit(f"Job not found: {args.job_id}")

    updates: dict = {}
    hook_copy = dict(job.get("hook_copy") or {})
    if args.vo:
        hook_copy["vo_text"] = args.vo
    if args.hook_a_main:
        hook_copy["card_a_main"] = args.hook_a_main
    if args.hook_a_sub:
        hook_copy["card_a_sub"] = args.hook_a_sub
    if args.hook_a_footer:
        hook_copy["card_a_footer"] = args.hook_a_footer
    if args.hook_b_main:
        hook_copy["card_b_main"] = args.hook_b_main
    if args.hook_b_sub:
        hook_copy["card_b_sub"] = args.hook_b_sub
    if args.hook_b_footer:
        hook_copy["card_b_footer"] = args.hook_b_footer
    updates["hook_copy"] = hook_copy

    if args.x_caption:
        if contains_url_text(args.x_caption):
            raise SystemExit(
                "x-caption contains a URL. FLOT-118: the link goes in the reply, "
                "not the main post (13x cost, and X suppresses link posts). "
                "Pass the link via --x-reply-text instead."
            )
        updates["x_post"] = {**job.get("x_post", {}), "caption": args.x_caption}
    if args.x_reply_text:
        updates["x_post"] = {**updates.get("x_post", job.get("x_post", {})),
                             "reply_text": args.x_reply_text}
    if args.yt_title_short:
        updates.setdefault("youtube", dict(job.get("youtube", {})))
        updates["youtube"]["title_short"] = args.yt_title_short
    if args.yt_title_long:
        updates.setdefault("youtube", dict(job.get("youtube", {})))
        updates["youtube"]["title_long"] = args.yt_title_long
    if args.yt_description:
        updates.setdefault("youtube", dict(job.get("youtube", {})))
        updates["youtube"]["description"] = args.yt_description
    if args.yt_tags:
        updates.setdefault("youtube", dict(job.get("youtube", {})))
        updates["youtube"]["tags"] = [t.strip() for t in args.yt_tags.split(",")]
    if args.source_url:
        updates["source_urls"] = [u.strip() for u in args.source_url.split(",") if u.strip()]
    if args.source_authors:
        updates["source_authors"] = [a.strip() for a in args.source_authors.split(",") if a.strip()]

    update_job_field(args.job_id, **updates)
    print(f"Copy set for {args.job_id}")


def cmd_run(args: argparse.Namespace) -> None:
    data = load_jobs()
    job = find_job(data, args.job_id)
    if job is None:
        sys.exit(f"Job not found: {args.job_id}")

    # Full run inserts localize between build and upload. It is a no-op unless the
    # job opts in (job['localize'] / youtube['localize_langs']), so it never spends
    # credits by surprise; `--stage localize` forces it with the default languages.
    stages = [args.stage] if args.stage else ["build", "localize", "upload", "post"]

    for stage in stages:
        print(f"\n── stage: {stage} ──────────────────")
        if stage == "build":
            # Reload fresh copy before each stage
            job = find_job(load_jobs(), args.job_id)
            stage_build(job, args.dry_run)
        elif stage == "localize":
            job = find_job(load_jobs(), args.job_id)
            stage_localize(job, args.dry_run, forced=bool(args.stage))
        elif stage == "upload":
            job = find_job(load_jobs(), args.job_id)
            stage_upload(job, args.dry_run)
        elif stage == "post":
            job = find_job(load_jobs(), args.job_id)
            stage_post(job, args.dry_run)
        else:
            sys.exit(f"Unknown stage: {stage}")


def main() -> None:
    parser = argparse.ArgumentParser(description="tech-shorts pipeline coordinator")
    sub = parser.add_subparsers(dest="command", required=True)

    # status
    p_status = sub.add_parser("status", help="Show pipeline status for all jobs")
    p_status.add_argument("job_id", nargs="?", help="Filter to one job")

    # set-sources
    p_src = sub.add_parser("set-sources", help="Set raw NotebookLM source paths")
    p_src.add_argument("job_id")
    p_src.add_argument("--short", required=True, help="Path to short (vertical) NotebookLM mp4")
    p_src.add_argument("--long", required=True, help="Path to long (landscape) NotebookLM mp4")
    p_src.add_argument("--trim", type=float, default=None, metavar="SECONDS",
                       help="Seconds to trim from end of each source (drops NotebookLM end-card)")

    # set-copy
    p_copy = sub.add_parser("set-copy", help="Set hook/outro copy + YouTube/X metadata")
    p_copy.add_argument("job_id")
    p_copy.add_argument("--vo", help="ElevenLabs VO script text (~1–2 sentences)")
    p_copy.add_argument("--hook-a-main", metavar="TEXT")
    p_copy.add_argument("--hook-a-sub", metavar="TEXT")
    p_copy.add_argument("--hook-a-footer", metavar="TEXT")
    p_copy.add_argument("--hook-b-main", metavar="TEXT")
    p_copy.add_argument("--hook-b-sub", metavar="TEXT")
    p_copy.add_argument("--hook-b-footer", metavar="TEXT")
    p_copy.add_argument("--x-caption", metavar="TEXT",
                        help="X main-post text (the hook). Must NOT contain a URL — "
                             "FLOT-118 puts the link in a reply instead.")
    p_copy.add_argument("--x-reply-text", metavar="TEXT",
                        help="X reply text carrying the link. Defaults to the "
                             "YouTube short URL if unset.")
    p_copy.add_argument("--source-url", metavar="url1,url2",
                        help="Source material URL(s), comma-separated. Cited in a "
                             "reply on the X thread (tracking params are stripped).")
    p_copy.add_argument("--source-authors", metavar="@h1,@h2",
                        help="Author credits/handles, comma-separated. Cited alongside "
                             "the source in the X thread.")
    p_copy.add_argument("--yt-title-short", metavar="TEXT")
    p_copy.add_argument("--yt-title-long", metavar="TEXT")
    p_copy.add_argument("--yt-description", metavar="TEXT")
    p_copy.add_argument("--yt-tags", metavar="tag1,tag2,…")

    # run
    p_run = sub.add_parser("run", help="Run pipeline stages for a job")
    p_run.add_argument("job_id")
    p_run.add_argument("--stage", choices=["build", "localize", "upload", "post"],
                       help="Run only this stage (default: all)")
    p_run.add_argument("--dry-run", action="store_true", help="Print what would happen, don't execute")

    args = parser.parse_args()

    if args.command == "status":
        cmd_status(args)
    elif args.command == "set-sources":
        cmd_set_sources(args)
    elif args.command == "set-copy":
        cmd_set_copy(args)
    elif args.command == "run":
        cmd_run(args)


if __name__ == "__main__":
    main()
