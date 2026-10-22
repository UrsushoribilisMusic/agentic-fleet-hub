#!/usr/bin/env python3
"""
build_vertical_short.py — Derived Vertical Short (<90s, 9:16, 1080x1920) Builder
=================================================================================
Creates a standalone <90-second vertical YouTube Short (1080x1920 @ 30fps) from an
existing landscape (16:9) Tech Short job by:
  1. Rendering native 9:16 vertical Intro Hook Cards (A & B) and a vertical Outro
     Card with multi-line word wrapping (avoiding single-line shrink or 16:9 crop cutoff).
  2. Synthesizing a dedicated <90s voiceover script via local Kokoro TTS (`af_bella`
     with `HF_HUB_OFFLINE=1`) and normalizing loudness to -16 LUFS.
  3. Extracting curated visual highlight segments from `raw_cinematic.mp4` and
     formatting each segment to 1080x1920 using either:
       - `crop`: 9:16 center-crop (`scale=-2:1920,crop=1080:1920`) for full-bleed
         graphical illustrations.
       - `pillarbox`: blurred 9:16 backdrop with centered 16:9 foreground and subtle
         vertical title/topic framing so wide charts, scaling curves, and architecture
         diagrams remain 100% legible on mobile screens.
  4. Assembling Intro Cards + Curated Visual Segments + Vertical Outro Card with the
     continuous voiceover into `final_short.mp4`, staging a copy in
     `~/Downloads/tech-shorts-captions/<slug>/`, and updating `jobs.json`.

Usage:
  /Users/miguelrodriguez/projects/music-video-tool/.venv312/bin/python3 \\
    /Users/miguelrodriguez/projects/agentic-fleet-hub/tech-shorts/build_vertical_short.py \\
    --job-id ts-20261021-squeezing-an-autonomous-agent-into-32gb
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import tempfile
import textwrap
from pathlib import Path
from typing import Any

import numpy as np
import soundfile as sf
from PIL import Image, ImageDraw, ImageFont

os.environ.setdefault("HF_HUB_OFFLINE", "1")

JOBS_JSON = Path(__file__).resolve().parent / "jobs.json"
CAPTIONS_ROOT = Path("/Users/miguelrodriguez/Downloads/tech-shorts-captions")

# Brand palette (matches pipeline.py)
BG = (11, 15, 23)        # #0B0F17 deep slate
FG = (242, 245, 250)     # #F2F5FA crisp white
TEAL = (0, 212, 170)     # #00D4AA accent teal
RED = (255, 92, 92)      # #FF5C5C coral red
MUTE = (130, 142, 160)   # #828EA0 muted slate

FONT_CANDIDATES_BOLD = [
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/System/Library/Fonts/HelveticaNeue.ttc",
    "/Library/Fonts/Arial Bold.ttf",
]
FONT_CANDIDATES_REG = [
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
    "/Library/Fonts/Arial.ttf",
]


def _pick_font(candidates: list[str], size: int) -> ImageFont.FreeTypeFont:
    for p in candidates:
        if Path(p).exists():
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    return ImageFont.load_default()


def ffprobe_duration(path: Path) -> float:
    out = subprocess.check_output(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        text=True,
    ).strip()
    return float(out)


def render_vertical_hook_card(
    out_png: Path,
    headline: str,
    accent_line: str,
    sub_line: str,
    badge: str = "TECH SHORTS · 90s ARCHITECTURE BRIEF",
    footer: str = "The Classical Remix",
    size: tuple[int, int] = (1080, 1920),
) -> Path:
    """Render a native 1080x1920 vertical hook card with multi-line word wrapping."""
    w, h = size
    img = Image.new("RGB", size, BG)
    draw = ImageDraw.Draw(img)

    # Top and bottom accent bars
    bar_h = 16
    draw.rectangle([(0, 0), (w, bar_h)], fill=TEAL)
    draw.rectangle([(0, h - bar_h), (w, h)], fill=RED)

    f_badge = _pick_font(FONT_CANDIDATES_BOLD, 34)
    f_head = _pick_font(FONT_CANDIDATES_BOLD, 88)
    f_accent = _pick_font(FONT_CANDIDATES_BOLD, 56)
    f_sub = _pick_font(FONT_CANDIDATES_REG, 42)
    f_foot = _pick_font(FONT_CANDIDATES_REG, 34)

    # Top badge pill
    bbox_b = draw.textbbox((0, 0), badge, font=f_badge)
    bw = bbox_b[2] - bbox_b[0]
    draw.text(((w - bw) // 2, 220), badge, font=f_badge, fill=TEAL)

    # Subtle divider line
    draw.rectangle([(w // 2 - 140, 290), (w // 2 + 140, 294)], fill=MUTE)

    # Wrapped headline
    head_lines = textwrap.wrap(headline, width=16)
    accent_lines = textwrap.wrap(accent_line, width=24) if accent_line else []
    sub_lines = textwrap.wrap(sub_line, width=30) if sub_line else []

    y = 480
    for line in head_lines:
        bbox = draw.textbbox((0, 0), line, font=f_head)
        lw, lh = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.text(((w - lw) // 2, y), line, font=f_head, fill=FG)
        y += lh + 26

    if accent_lines:
        y += 40
        for line in accent_lines:
            bbox = draw.textbbox((0, 0), line, font=f_accent)
            lw, lh = bbox[2] - bbox[0], bbox[3] - bbox[1]
            draw.text(((w - lw) // 2, y), line, font=f_accent, fill=TEAL)
            y += lh + 22

    if sub_lines:
        y += 44
        for line in sub_lines:
            bbox = draw.textbbox((0, 0), line, font=f_sub)
            lw, lh = bbox[2] - bbox[0], bbox[3] - bbox[1]
            draw.text(((w - lw) // 2, y), line, font=f_sub, fill=MUTE)
            y += lh + 18

    # Footer
    bbox_f = draw.textbbox((0, 0), footer, font=f_foot)
    fw = bbox_f[2] - bbox_f[0]
    draw.text(((w - fw) // 2, h - 160), footer, font=f_foot, fill=MUTE)

    out_png.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_png, "PNG")
    return out_png


def render_vertical_outro_card(
    out_png: Path,
    channel_name: str = "The Classical Remix",
    tagline: str = "New videos every week",
    size: tuple[int, int] = (1080, 1920),
) -> Path:
    """Render a native 1080x1920 vertical outro card matching the channel style."""
    w, h = size
    img = Image.new("RGB", size, BG)
    draw = ImageDraw.Draw(img)

    bar_h = 16
    draw.rectangle([(0, 0), (w, bar_h)], fill=TEAL)
    draw.rectangle([(0, h - bar_h), (w, h)], fill=RED)

    f_big = _pick_font(FONT_CANDIDATES_BOLD, 108)
    f_mid = _pick_font(FONT_CANDIDATES_BOLD, 54)
    f_sub = _pick_font(FONT_CANDIDATES_REG, 42)

    blocks: list[tuple[str, ImageFont.FreeTypeFont, tuple[int, int, int], int]] = [
        ("SUBSCRIBE", f_big, TEAL, 45),
        ("for more AI & computer", f_mid, FG, 18),
        ("science explainers", f_mid, FG, 70),
        (channel_name, f_sub, MUTE, 22),
        (tagline, f_sub, FG, 0),
    ]

    measured = []
    total_h = 0
    for text, font, color, gap in blocks:
        bbox = draw.textbbox((0, 0), text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        measured.append((text, font, color, tw, th, gap))
        total_h += th + gap

    y = (h - total_h) // 2
    for text, font, color, tw, th, gap in measured:
        x = (w - tw) // 2
        draw.text((x, y), text, font=font, fill=color)
        y += th + gap

    out_png.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_png, "PNG")
    return out_png


def synthesize_kokoro_vo(
    script_text: str,
    out_wav: Path,
    voice: str = "af_bella",
    speed: float = 1.04,
) -> float:
    """Synthesize continuous narration using local Kokoro TTS and normalize to -16 LUFS."""
    from kokoro import KPipeline

    pipeline = KPipeline(lang_code="a", repo_id="hexgrad/Kokoro-82M")
    chunks: list[np.ndarray] = []
    # Split by paragraph/sentence groups for clean prosody
    paragraphs = [p.strip() for p in script_text.strip().split("\n") if p.strip()]
    for para in paragraphs:
        for _, _, audio in pipeline(para, voice=voice, speed=speed, split_pattern=r"(?<=[.!?])\s+"):
            if audio is not None and len(audio) > 0:
                chunks.append(np.asarray(audio, dtype=np.float32))
                # 0.18s natural breath pause between sentences
                chunks.append(np.zeros(int(24000 * 0.18), dtype=np.float32))

    full_audio = np.concatenate(chunks) if chunks else np.zeros(24000, dtype=np.float32)
    raw_wav = out_wav.with_suffix(".raw.wav")
    sf.write(str(raw_wav), full_audio, 24000)

    # Normalize loudness and resample to 44.1kHz stereo for YouTube Shorts
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(raw_wav),
            "-af",
            "loudnorm=I=-16:TP=-1.5:LRA=11",
            "-ar",
            "44100",
            "-ac",
            "2",
            str(out_wav),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    raw_wav.unlink(missing_ok=True)
    return ffprobe_duration(out_wav)


def build_intro_segment(
    card_a_png: Path,
    card_b_png: Path,
    duration: float,
    out_mp4: Path,
) -> Path:
    """Render a 1080x1920 30fps two-card intro with smooth crossfade."""
    half = round(duration / 2.0, 2)
    fade_d = 0.45
    dur_a = half + fade_d / 2.0
    dur_b = duration - half + fade_d / 2.0
    offset = max(0.2, dur_a - fade_d)

    filter_complex = (
        f"[0:v]scale=1080:1920,fps=30,format=yuv420p,fade=t=in:st=0:d=0.35[va];"
        f"[1:v]scale=1080:1920,fps=30,format=yuv420p[vb];"
        f"[va][vb]xfade=transition=fade:duration={fade_d}:offset={offset:.2f},"
        f"fade=t=out:st={max(0.2, duration - 0.35):.2f}:d=0.35,format=yuv420p[v]"
    )
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-loop",
            "1",
            "-t",
            f"{dur_a:.2f}",
            "-i",
            str(card_a_png),
            "-loop",
            "1",
            "-t",
            f"{dur_b:.2f}",
            "-i",
            str(card_b_png),
            "-filter_complex",
            filter_complex,
            "-map",
            "[v]",
            "-t",
            f"{duration:.2f}",
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "18",
            "-pix_fmt",
            "yuv420p",
            "-r",
            "30",
            "-an",
            str(out_mp4),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return out_mp4


def build_visual_clip(
    raw_mp4: Path,
    start_sec: float,
    duration: float,
    mode: str,
    out_mp4: Path,
) -> Path:
    """
    Extract a visual segment from `raw_cinematic.mp4` and format to 1080x1920 @ 30fps.
    Modes:
      - `crop`: Center crop (`scale=-2:1920,crop=1080:1920`) for graphic illustrations.
      - `pillarbox`: Blurred 1080x1920 background + full-width 1080 foreground so wide
        charts and architectural diagrams stay 100% readable.
    """
    fade_out_st = max(0.1, duration - 0.25)
    if mode == "pillarbox":
        vf = (
            "split[bg][fg];"
            "[bg]scale=1080:1920:force_original_aspect_ratio=increase,"
            "crop=1080:1920,boxblur=28:6,eq=brightness=-0.12:saturation=0.85[bg2];"
            "[fg]scale=1080:-2[fg2];"
            f"[bg2][fg2]overlay=(W-w)/2:(H-h)/2,fps=30,"
            f"fade=t=in:st=0:d=0.25,fade=t=out:st={fade_out_st:.2f}:d=0.25,format=yuv420p"
        )
    else:
        vf = (
            "scale=-2:1920:flags=lanczos,crop=1080:1920,fps=30,"
            f"fade=t=in:st=0:d=0.25,fade=t=out:st={fade_out_st:.2f}:d=0.25,format=yuv420p"
        )

    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-ss",
            f"{start_sec:.2f}",
            "-t",
            f"{duration:.2f}",
            "-i",
            str(raw_mp4),
            "-vf",
            vf,
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "18",
            "-pix_fmt",
            "yuv420p",
            "-r",
            "30",
            "-an",
            str(out_mp4),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return out_mp4


def build_outro_segment(
    outro_png: Path,
    duration: float,
    out_mp4: Path,
) -> Path:
    """Render a 1080x1920 30fps outro clip with fade-in and fade-out."""
    fade_out_st = max(0.2, duration - 0.5)
    vf = (
        f"scale=1080:1920,fps=30,"
        f"fade=t=in:st=0:d=0.4,fade=t=out:st={fade_out_st:.2f}:d=0.5,format=yuv420p"
    )
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-loop",
            "1",
            "-t",
            f"{duration:.2f}",
            "-i",
            str(outro_png),
            "-vf",
            vf,
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "18",
            "-pix_fmt",
            "yuv420p",
            "-r",
            "30",
            "-an",
            str(out_mp4),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return out_mp4


# Default preset for Muse Glimmer 30B (ts-20261021-squeezing-an-autonomous-agent-into-32gb)
PRESETS: dict[str, dict[str, Any]] = {
    "ts-20261021-squeezing-an-autonomous-agent-into-32gb": {
        "card_a": {
            "headline": "30 BILLION PARAMETERS IN 32GB VRAM?",
            "accent_line": "Meta’s Muse Glimmer 30B",
            "sub_line": "Co-designing a frontier autonomous agent for a single consumer GPU",
        },
        "card_b": {
            "headline": "55.7GB → 19.65GB WITHOUT LOSING IQ",
            "accent_line": "Dense > MoE · EvoPress · 16:1 GQA",
            "sub_line": "How Meta Superintelligence Labs beat the memory wall",
        },
        "script": (
            "Can you squeeze a frontier thirty-billion-parameter autonomous agent onto a single thirty-two-gigabyte consumer GPU? "
            "Meta Superintelligence Labs just proved you can, with Muse Glimmer Thirty-B.\n"
            "Instead of shrinking a huge model after training, they co-designed the architecture around hardware limits from day one, beating Gemma Four and Qwen Three-Point-Six on agentic benchmarks.\n"
            "First, under a fixed thirty-two-gigabyte ceiling, a dense thirty-billion model beat sparse Mixture-of-Experts by two-point-five-X in compute efficiency.\n"
            "Second, sixteen-bit weights take fifty-five-point-seven gigabytes. "
            "Using EvoPress evolutionary quantization across four hundred eighteen weight units, they compressed the model to nineteen-point-six-five gigabytes with almost zero accuracy loss.\n"
            "Third, a sixteen-to-one grouped-query attention ratio and a two-thousand-forty-eight-token sliding window cap KV-cache memory, fitting both a vision encoder and a speculative drafter on the same card.\n"
            "Finally, they distilled intelligence from Muse Spark inside Dockerized simulated persona universes. "
            "Watch the full deep dive on the channel!"
        ),
        # Visual segments in raw_cinematic.mp4 (relative weights; scaled to match VO duration)
        "segments": [
            {"start": 38.0, "weight": 1.0, "mode": "crop", "label": "32GB MAX GPU illustration"},
            {"start": 53.0, "weight": 0.9, "mode": "pillarbox", "label": "Capability Radar Chart"},
            {"start": 126.0, "weight": 0.85, "mode": "crop", "label": "Max Extraction 100% chip"},
            {"start": 141.0, "weight": 0.95, "mode": "pillarbox", "label": "Dense vs MoE scaling curves"},
            {"start": 210.0, "weight": 0.9, "mode": "crop", "label": "EvoPress quantization graph"},
            {"start": 230.0, "weight": 0.95, "mode": "crop", "label": "418-unit mixed-precision matrix"},
            {"start": 290.0, "weight": 0.85, "mode": "pillarbox", "label": "16:1 GQA 32 Query -> 2 KV heads"},
            {"start": 305.0, "weight": 0.85, "mode": "pillarbox", "label": "2048 Sliding Window Attention"},
            {"start": 384.0, "weight": 1.0, "mode": "crop", "label": "Dockerized simulated persona universes"},
        ],
        "intro_ratio": 0.14,  # ~14% of VO duration on Intro Cards A & B
        "outro_sec": 4.0,     # 4.0s vertical outro card at the end
    }
}


def build_vertical_short_for_job(job_id: str, config_path: Path | None = None) -> Path:
    data = json.loads(JOBS_JSON.read_text())
    job = next((j for j in data["jobs"] if j["id"] == job_id), None)
    if not job:
        raise ValueError(f"Job {job_id} not found in {JOBS_JSON}")

    if config_path and config_path.exists():
        cfg = json.loads(config_path.read_text())
    elif job_id in PRESETS:
        cfg = PRESETS[job_id]
    else:
        raise ValueError(f"No preset found for {job_id}; pass --config <json_path>.")

    raw_mp4 = Path(job["assets"]["raw_cinematic_mp4"])
    asset_dir = raw_mp4.parent
    slug = job["slug"]

    print(f"[1/5] Rendering native 1080x1920 vertical Intro & Outro cards in {asset_dir}...")
    card_a_png = render_vertical_hook_card(
        asset_dir / "short_hook_card_a_vertical.png",
        headline=cfg["card_a"]["headline"],
        accent_line=cfg["card_a"]["accent_line"],
        sub_line=cfg["card_a"]["sub_line"],
    )
    card_b_png = render_vertical_hook_card(
        asset_dir / "short_hook_card_b_vertical.png",
        headline=cfg["card_b"]["headline"],
        accent_line=cfg["card_b"]["accent_line"],
        sub_line=cfg["card_b"]["sub_line"],
    )
    outro_png = render_vertical_outro_card(asset_dir / "short_outro_vertical.png")

    script_path = asset_dir / "short_script.txt"
    script_path.write_text(cfg["script"].strip() + "\n")

    print("[2/5] Synthesizing <90s continuous narration via local Kokoro (af_bella)...")
    vo_wav = asset_dir / "short_vo.wav"
    vo_dur = synthesize_kokoro_vo(cfg["script"], vo_wav, voice="af_bella", speed=1.04)
    print(f"      Voiceover duration: {vo_dur:.2f}s")

    outro_sec = float(cfg.get("outro_sec", 4.0))
    total_target = vo_dur + outro_sec
    if total_target >= 89.5:
        raise RuntimeError(
            f"Total Short duration ({total_target:.2f}s) exceeds 90s limit! Shorten script or increase speed."
        )

    intro_dur = round(max(8.0, min(11.0, vo_dur * float(cfg.get("intro_ratio", 0.14)))), 2)
    body_dur = round(vo_dur - intro_dur, 2)

    segments = cfg["segments"]
    total_weight = sum(float(s.get("weight", 1.0)) for s in segments)

    with tempfile.TemporaryDirectory(prefix="vertical_short_") as tmp_str:
        tmp = Path(tmp_str)
        clip_paths: list[Path] = []

        print(f"[3/5] Building vertical intro ({intro_dur:.2f}s) + {len(segments)} visual segments ({body_dur:.2f}s)...")
        intro_mp4 = build_intro_segment(card_a_png, card_b_png, intro_dur, tmp / "00_intro.mp4")
        clip_paths.append(intro_mp4)

        allocated = 0.0
        for idx, seg in enumerate(segments, start=1):
            if idx < len(segments):
                seg_dur = round(body_dur * (float(seg.get("weight", 1.0)) / total_weight), 2)
                allocated += seg_dur
            else:
                seg_dur = round(max(3.0, body_dur - allocated), 2)

            seg_out = tmp / f"{idx:02d}_seg.mp4"
            print(
                f"      - Segment {idx}/{len(segments)}: raw @{seg['start']}s for {seg_dur:.2f}s "
                f"[{seg['mode']}] ({seg.get('label', '')})"
            )
            build_visual_clip(raw_mp4, float(seg["start"]), seg_dur, seg["mode"], seg_out)
            clip_paths.append(seg_out)

        outro_mp4 = build_outro_segment(outro_png, outro_sec, tmp / "99_outro.mp4")
        clip_paths.append(outro_mp4)

        concat_txt = tmp / "concat.txt"
        concat_txt.write_text("".join(f"file '{p}'\n" for p in clip_paths))
        video_only_mp4 = tmp / "video_only.mp4"
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(concat_txt),
                "-c",
                "copy",
                str(video_only_mp4),
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        print("[4/5] Muxing video track with Kokoro voiceover + silent outro padding...")
        final_short_mp4 = asset_dir / "final_short.mp4"
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-i",
                str(video_only_mp4),
                "-i",
                str(vo_wav),
                "-filter_complex",
                f"[1:a]apad=whole_dur={total_target:.2f}[a]",
                "-map",
                "0:v:0",
                "-map",
                "[a]",
                "-c:v",
                "copy",
                "-c:a",
                "aac",
                "-b:a",
                "192k",
                "-ar",
                "44100",
                "-ac",
                "2",
                "-t",
                f"{total_target:.2f}",
                "-movflags",
                "+faststart",
                str(final_short_mp4),
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    final_dur = ffprobe_duration(final_short_mp4)
    print(f"[5/5] Built {final_short_mp4} ({final_dur:.2f}s, 1080x1920)")

    # Stage copy to Downloads/tech-shorts-captions/<slug>/
    stage_dir = CAPTIONS_ROOT / slug
    stage_dir.mkdir(parents=True, exist_ok=True)
    staged_short = stage_dir / f"{slug}_SHORT_FINAL.mp4"
    shutil.copy2(final_short_mp4, staged_short)
    print(f"      Staged copy: {staged_short}")

    # Update jobs.json
    job["assets"]["final_short_mp4"] = str(final_short_mp4)
    job["assets"]["short_vo_wav"] = str(vo_wav)
    job["assets"]["short_script_txt"] = str(script_path)
    JOBS_JSON.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    print(f"      Updated jobs.json -> assets.final_short_mp4")
    return final_short_mp4


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a <90s 9:16 vertical Short from a Tech Short job.")
    parser.add_argument("--job-id", required=True, help="Job ID in jobs.json")
    parser.add_argument("--config", type=Path, default=None, help="Optional JSON config file for segments/script")
    args = parser.parse_args()
    build_vertical_short_for_job(args.job_id, args.config)


if __name__ == "__main__":
    main()
