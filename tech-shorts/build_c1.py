#!/usr/bin/env python3
"""Build Compilation C1: AI Will Do the Work, Vol. 2 (TSC-1).

Implements COMPILATION_PLAYBOOK.md §2 and §3:
- §3.1 Trim each of the 6 parts to exact verified in/out bounds, normalized to
  1920x1080 @ 30fps, yuv420p, aac 44100Hz mono.
- §3.2 Build the 20s motion cold open from Miguel's 20s Gemini motion video
  (gemini_intro_20s.mp4) or two 10s motion clips (clip_a.mp4 + clip_b.mp4) with
  the channel title card composited over the second 10s half (Clip B) and the
  Kokoro channel hook VO layered underneath.
- §3.3 Build 5x 4-second chapter transition cards before parts 2..6: part number
  small, transition line large, held on a slow push-in over a dimmed still from
  the part that follows, with 0.5s fade in and out.
- §3.4 Concat intro + part_1 + (card_2, part_2) .. (card_6, part_6) + outro into
  final_comp.mp4.
"""
from __future__ import annotations

import argparse
import base64
import io
import json
import subprocess
import sys
import textwrap
import time
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import pipeline as P

OUT_DIR = Path("/Users/miguelrodriguez/flotilla/tech-shorts/assets/2026-10-24-compilation-c1-ai-will-do-the-work-vol-2")
W, H, FPS = 1920, 1080, 30

# Verified in/out points for C1 parts (COMPILATION_PLAYBOOK.md §2 & §3.1)
PARTS = [
    {
        "num": 1,
        "vid": "7UPyRA9cBtE",
        "kind": "raw_cinematic",
        "path": "/Users/miguelrodriguez/flotilla/tech-shorts/assets/2026-10-11-the-ai-bottleneck-why-exponential-tech-is-trapped-in-a-linear-world/raw_cinematic.mp4",
        "in": 0.00,
        "out": 498.87,
        "title": "The AI Bottleneck: Exponential Models, Linear World",
        "short_title": "1. The AI Bottleneck: Exponential Models, Linear World",
        "card_num": None,
        "card_line": None,
    },
    {
        "num": 2,
        "vid": "lChiYc1A4B8",
        "kind": "final_long",
        "path": "/Users/miguelrodriguez/flotilla/tech-shorts/assets/2026-09-09-anthropic-economic-scenarios/final_long.mp4",
        "in": 17.67,
        "out": 273.89,
        "title": "How AI Reshapes Jobs, Growth & Unemployment: Anthropic's 2026-2030 Economic Scenarios",
        "short_title": "2. How AI Reshapes Jobs, Growth & Unemployment (Anthropic 2026–2030)",
        "card_num": "TWO",
        "card_line": "The models move exponentially. The world does not.",
    },
    {
        "num": 3,
        "vid": "Vritr444eKs",
        "kind": "raw_cinematic",
        "path": "/Users/miguelrodriguez/flotilla/tech-shorts/assets/2026-10-12-labor-llm-language-based-occupational-representations-with-large-language-models/raw_cinematic.mp4",
        "in": 0.00,
        "out": 405.01,
        "title": "The Grammar of Work: How LLMs Learn Career Moves",
        "short_title": "3. The Grammar of Work: How LLMs Learn Career Moves",
        "card_num": "THREE",
        "card_line": "What a career looks like to a language model.",
    },
    {
        "num": 4,
        "vid": "jxi-GUpdhYI",
        "kind": "final_long",
        "path": "/Users/miguelrodriguez/flotilla/tech-shorts/assets/2026-10-02-can-the-ai-boom-can-continue-without-leading-to-a-massive-increase-in-inequality/final_long.mp4",
        "in": 11.53,
        "out": 311.99,
        "title": "The Catch-22 of the AI Economy: Can the Boom Pay for Itself Without Widening Inequality?",
        "short_title": "4. The Catch-22 of the AI Economy",
        "card_num": "FOUR",
        "card_line": "Someone has to pay for the boom.",
    },
    {
        "num": 5,
        "vid": "Miw8TeG3RFI",
        "kind": "final_long",
        "path": "/Users/miguelrodriguez/flotilla/tech-shorts/assets/2026-10-05-the-jevons-paradox-and-the-future-of-ai-employment/final_long.mp4",
        "in": 16.50,
        "out": 367.30,
        "title": "Will AI Create Jobs or Destroy Them? The Jevons Paradox and the Future of Work",
        "short_title": "5. Will AI Create Jobs or Destroy Them? The Jevons Paradox",
        "card_num": "FIVE",
        "card_line": "Cheaper work has never meant less work. Until now?",
    },
    {
        "num": 6,
        "vid": "JFhLTSY7Pxw",
        "kind": "raw_cinematic",
        "path": "/Users/miguelrodriguez/flotilla/tech-shorts/assets/2026-10-12-the-white-collar-bypass/raw_cinematic.mp4",
        "in": 0.00,
        "out": 289.16,
        "title": "The White-Collar Bypass: How AI Is Erasing Entry-Level Jobs",
        "short_title": "6. The White-Collar Bypass: How AI Is Erasing Entry-Level Jobs",
        "card_num": "SIX",
        "card_line": "The jobs that taught you the job are going first.",
    },
]

STYLE_SUFFIX = (
    "Cinematic documentary photography, shallow depth of field, anamorphic lens, "
    "subtle film grain, muted teal-and-amber palette, slow deliberate camera motion, "
    "no text, no captions, no logos, no people looking at camera. 16:9, 1920x1080, 30fps."
)

CLIP_A_PROMPT = (
    "An empty open-plan office at dawn, long rows of identical desks, every monitor "
    "glowing with scrolling output that nobody is reading. A single chair slowly "
    "rotates on its own. Camera pushes forward down the aisle at walking pace. Cold "
    "blue window light, warm desk lamps. " + STYLE_SUFFIX
)

CLIP_B_PROMPT = (
    "Close on a payslip-sized sheet of paper on an empty desk, its printed figures "
    "dissolving into drifting particles that rise and scatter. Camera pulls back and "
    "up to reveal the whole floor of desks below, now lit only by screens. " + STYLE_SUFFIX
)

HOOK_VO_TEXT = (
    "Every screen in the building is still glowing, and the work is still getting done. "
    "Only the chairs are empty. Exponential models have collided with a linear economy—"
    "reshaping career ladders, entry-level jobs, and who gets paid. "
    "Across six investigations, we follow the data on one question: "
    "when AI does the work, what happens to yours?"
)


def ff(*args: object) -> None:
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *[str(a) for a in args]]
    subprocess.run(cmd, check=True)


def ffdur(path: Path) -> float:
    res = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nk=1:nw=1", str(path)],
        check=True, capture_output=True, text=True,
    )
    return float(res.stdout.strip())


def generate_kokoro_vo(text: str, out_mp3: Path) -> None:
    import soundfile as sf
    from kokoro import KPipeline
    import numpy as np

    pipe = KPipeline(lang_code="a")
    chunks = [audio for _, _, audio in pipe(text, voice="af_bella", speed=1.12) if audio is not None]
    wav = np.concatenate(chunks) if len(chunks) > 1 else chunks[0]
    tmp_wav = out_mp3.with_suffix(".wav")
    sf.write(str(tmp_wav), wav, 24000)
    ff("-i", tmp_wav, "-c:a", "libmp3lame", "-q:a", "2", out_mp3)


def trim_parts() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for part in PARTS:
        n = part["num"]
        out_mp4 = OUT_DIR / f"part_{n}.mp4"
        if out_mp4.exists() and out_mp4.stat().st_size > 1_000_000:
            d = ffdur(out_mp4)
            expected = part["out"] - part["in"]
            if abs(d - expected) < 1.0:
                print(f"[part_{n}] reusing {out_mp4.name} ({d:.2f}s)")
                continue
        tin = part["in"]
        tout = part["out"]
        dur = tout - tin
        fade_out_st = max(0.0, dur - 0.25)
        print(f"[part_{n}] trimming {part['vid']} ({tin:.2f}s -> {tout:.2f}s = {dur:.2f}s)...")
        ff(
            "-ss", f"{tin:.3f}",
            "-to", f"{tout:.3f}",
            "-i", part["path"],
            "-vf", f"scale={W}:{H}:flags=lanczos,fps={FPS},format=yuv420p",
            "-af", f"afade=t=in:st=0:d=0.15,afade=t=out:st={fade_out_st:.3f}:d=0.20",
            "-c:v", "libx264", "-preset", "fast", "-crf", "20", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-ar", "44100", "-ac", "1", "-b:a", "128k",
            out_mp4,
        )
        print(f"[part_{n}] wrote {out_mp4.name} ({ffdur(out_mp4):.2f}s)")


def render_transition_overlay(out_png: Path, card_num: str, card_line: str) -> None:
    """Render crisp transparent RGBA overlay with top/bottom bars, small part number,
    and large transition line."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dr = ImageDraw.Draw(img)

    bar_h = max(6, H // 160)
    dr.rectangle([0, 0, W, bar_h], fill=(*P.TEAL, 255))
    dr.rectangle([0, H - bar_h, W, H], fill=(*P.RED, 255))

    font_num = ImageFont.truetype(P.FONT_PATH, 38)
    font_line = ImageFont.truetype(P.FONT_PATH, 76)

    wrapped = textwrap.wrap(card_line, width=28)
    line_metrics = []
    for ln in wrapped:
        asc, desc = font_line.getmetrics()
        line_metrics.append((ln, asc + desc))

    num_asc, num_desc = font_num.getmetrics()
    num_h = num_asc + num_desc
    gap_after_num = 36
    line_gap = 18

    total_h = num_h + gap_after_num + sum(h for _, h in line_metrics) + line_gap * max(0, len(line_metrics) - 1)
    y = (H - total_h) / 2

    label = f"PART {card_num}"
    dr.text((W / 2, y), label, font=font_num, fill=(*P.TEAL, 255), anchor="ma")
    y += num_h + gap_after_num

    for i, (ln, lh) in enumerate(line_metrics):
        if i > 0:
            y += line_gap
        dr.text((W / 2, y), ln, font=font_line, fill=(*P.WHITE, 255), anchor="ma")
        y += lh

    img.save(str(out_png))


def build_transition_cards() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for part in PARTS:
        n = part["num"]
        if not part["card_num"]:
            continue
        card_mp4 = OUT_DIR / f"card_{n}.mp4"
        if card_mp4.exists() and card_mp4.stat().st_size > 50_000:
            print(f"[card_{n}] reusing {card_mp4.name} ({ffdur(card_mp4):.2f}s)")
            continue

        raw_still = OUT_DIR / f"_card_{n}_raw_still.png"
        dim_still = OUT_DIR / f"_card_{n}_dim_still.png"
        ovl_png = OUT_DIR / f"_card_{n}_overlay.png"

        sample_t = part["in"] + 8.0
        ff("-ss", f"{sample_t:.2f}", "-i", part["path"], "-frames:v", "1", raw_still)

        im = Image.open(raw_still).convert("RGB").resize((W, H), Image.LANCZOS)
        im = im.filter(ImageFilter.GaussianBlur(radius=3))
        ink_bg = Image.new("RGB", (W, H), P.INK)
        dimmed = Image.blend(ink_bg, im, alpha=0.22)
        dimmed.save(str(dim_still))

        render_transition_overlay(ovl_png, part["card_num"], part["card_line"])

        print(f"[card_{n}] rendering 4s transition card: {part['card_num']} — {part['card_line']}")
        fc = (
            f"[0:v]scale=2304:1296:flags=lanczos,"
            f"zoompan=z='min(zoom+0.0005,1.06)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=120:s={W}x{H}:fps={FPS}[bg];"
            f"[bg][1:v]overlay=0:0,"
            f"fade=t=in:st=0:d=0.5,fade=t=out:st=3.5:d=0.5,format=yuv420p[v]"
        )
        ff(
            "-loop", "1", "-t", "4", "-i", dim_still,
            "-loop", "1", "-t", "4", "-i", ovl_png,
            "-f", "lavfi", "-t", "4", "-i", "anullsrc=r=44100:cl=mono",
            "-filter_complex", fc,
            "-map", "[v]", "-map", "2:a",
            "-t", "4", "-r", str(FPS),
            "-c:v", "libx264", "-preset", "fast", "-crf", "18", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-ar", "44100", "-ac", "1", "-b:a", "128k",
            card_mp4,
        )
        for tmp in (raw_still, dim_still, ovl_png):
            tmp.unlink(missing_ok=True)
        print(f"[card_{n}] wrote {card_mp4.name} ({ffdur(card_mp4):.2f}s)")


def build_outro() -> None:
    outro_mp4 = OUT_DIR / "outro.mp4"
    if outro_mp4.exists() and outro_mp4.stat().st_size > 20_000:
        print(f"[outro] reusing {outro_mp4.name} ({ffdur(outro_mp4):.2f}s)")
        return
    outro_png = P.build_outro_card({}, OUT_DIR, W, H)
    ff(
        "-loop", "1", "-i", outro_png,
        "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono",
        "-t", "5",
        "-vf", "fade=t=in:st=0:d=0.3,fade=t=out:st=4.6:d=0.4,format=yuv420p",
        "-r", str(FPS),
        "-c:v", "libx264", "-preset", "fast", "-crf", "18", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-ar", "44100", "-ac", "1", "-b:a", "128k",
        outro_mp4,
    )
    print(f"[outro] wrote {outro_mp4.name} ({ffdur(outro_mp4):.2f}s)")


def image_to_data_uri(filepath: Path, max_size: int = 1536) -> str:
    img = Image.open(filepath)
    if img.width > max_size or img.height > max_size:
        img.thumbnail((max_size, max_size), Image.LANCZOS)
    buf = io.BytesIO()
    img_rgb = img.convert("RGB") if img.mode != "RGB" else img
    img_rgb.save(buf, format="JPEG", quality=88)
    data = base64.b64encode(buf.getvalue()).decode("utf-8")
    return f"data:image/jpeg;base64,{data}"


def generate_motion_clips() -> tuple[Path, Path]:
    """Generate two 10s motion clips via Runway gen4_turbo image-to-video from seed
    frames (or text-to-video gen4.5 if seed frames are absent)."""
    clip_a = OUT_DIR / "clip_a.mp4"
    clip_b = OUT_DIR / "clip_b.mp4"
    if clip_a.exists() and clip_b.exists() and clip_a.stat().st_size > 200_000 and clip_b.stat().st_size > 200_000:
        print(f"[intro] reusing {clip_a.name} ({ffdur(clip_a):.2f}s) and {clip_b.name} ({ffdur(clip_b):.2f}s)")
        return clip_a, clip_b

    from dotenv import load_dotenv
    load_dotenv(P.MUSIC_VIDEO_TOOL / ".env")
    sys.path.insert(0, str(HERE.parent / "vault"))
    from vault import get_secret
    from runwayml import RunwayML
    import requests

    api_key = get_secret("RUNWAYML_API_SECRET")
    if not api_key:
        raise RuntimeError("RUNWAYML_API_SECRET not found in vault")
    client = RunwayML(api_key=api_key)

    specs = [
        ("clip_a", clip_a, OUT_DIR / "clip_a_seed.png", CLIP_A_PROMPT),
        ("clip_b", clip_b, OUT_DIR / "clip_b_seed.png", CLIP_B_PROMPT),
    ]
    tasks = []
    for label, out_path, seed_png, prompt in specs:
        if out_path.exists() and out_path.stat().st_size > 200_000:
            continue
        if seed_png.exists():
            print(f"[{label}] submitting Runway gen4_turbo (10s, 1280:720) with seed {seed_png.name}...")
            t = client.image_to_video.create(
                model="gen4_turbo",
                prompt_image=image_to_data_uri(seed_png),
                prompt_text=prompt[:990],
                ratio="1280:720",
                duration=10,
            )
        else:
            print(f"[{label}] submitting Runway gen4.5 text-to-video (10s, 1280:720)...")
            t = client.text_to_video.create(
                model="gen4.5",
                prompt_text=prompt[:990],
                ratio="1280:720",
                duration=10,
            )
        tasks.append((label, out_path, t.id))

    for label, out_path, tid in tasks:
        print(f"[{label}] polling Runway task {tid}...")
        while True:
            time.sleep(8)
            st = client.tasks.retrieve(tid)
            print(f"  [{label}] status={st.status}")
            if st.status == "SUCCEEDED":
                url = st.output[0]
                r = requests.get(url, timeout=120)
                r.raise_for_status()
                raw_dl = OUT_DIR / f"_{label}_raw.mp4"
                raw_dl.write_bytes(r.content)
                ff(
                    "-i", raw_dl,
                    "-t", "10",
                    "-vf", f"scale={W}:{H}:flags=lanczos,fps={FPS},format=yuv420p",
                    "-an",
                    "-c:v", "libx264", "-preset", "fast", "-crf", "18", "-pix_fmt", "yuv420p",
                    out_path,
                )
                raw_dl.unlink(missing_ok=True)
                print(f"[{label}] downloaded & normalized -> {out_path.name} ({ffdur(out_path):.2f}s)")
                break
            elif st.status in ("FAILED", "CANCELLED"):
                raise RuntimeError(f"Runway task {tid} failed: {st}")

    return clip_a, clip_b


def render_intro_title_overlay(out_png: Path) -> None:
    """Render translucent channel title card overlay to composite over Clip B (§3.2)."""
    img = Image.new("RGBA", (W, H), (11, 29, 38, 155))
    dr = ImageDraw.Draw(img)

    bar_h = max(6, H // 160)
    dr.rectangle([0, 0, W, bar_h], fill=(*P.TEAL, 255))
    dr.rectangle([0, H - bar_h, W, H], fill=(*P.RED, 255))

    lines = [
        ("IF AI DOES THE WORK,", P.WHITE, 96, None),
        ("WHO GETS PAID NEXT?", P.RED, 96, 0.015),
        ("Volume 2 · Six Deep Dives on Jobs, Growth & the AI Economy", P.WHITE, 46, 0.05),
        ("The Classical Remix", P.TEAL, 38, 0.045),
    ]

    max_w = W * 0.90
    prepared = []
    total = 0.0
    for i, (text, color, size, gap_frac) in enumerate(lines):
        font = ImageFont.truetype(P.FONT_PATH, size)
        while size > 14 and dr.textlength(text, font=font) > max_w:
            size -= 2
            font = ImageFont.truetype(P.FONT_PATH, size)
        asc, desc = font.getmetrics()
        lh = asc + desc
        gap = 0.0 if i == 0 else (gap_frac or 0.02) * H
        prepared.append((text, color, font, lh, gap))
        total += lh + gap

    y = (H - total) / 2
    for text, color, font, lh, gap in prepared:
        y += gap
        dr.text((W / 2, y), text, font=font, fill=(*color, 255), anchor="ma")
        y += lh

    img.save(str(out_png))


def build_intro() -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    intro_mp4 = OUT_DIR / "intro.mp4"
    gemini_raw = OUT_DIR / "gemini_intro_20s.mp4"

    vo_mp3 = OUT_DIR / "c1_hook_vo.mp3"
    if not vo_mp3.exists():
        generate_kokoro_vo(HOOK_VO_TEXT, vo_mp3)

    vo_dur = ffdur(vo_mp3)
    print(f"[intro] hook VO duration: {vo_dur:.2f}s")

    title_ovl = OUT_DIR / "_intro_title_overlay.png"
    render_intro_title_overlay(title_ovl)

    if gemini_raw.exists() and gemini_raw.stat().st_size > 200_000:
        fc = (
            f"[0:v]scale={W}:{H}:flags=lanczos,fps={FPS},format=yuv420p,fade=t=in:st=0:d=0.4[base];"
            f"[1:v]fade=t=in:st=11.0:d=0.8:alpha=1[ovl];"
            f"[base][ovl]overlay=0:0:enable='gte(t,10.8)',fade=t=out:st=19.5:d=0.5,format=yuv420p[v];"
            f"[2:a]aresample=44100,pan=mono|c0=c0,apad=whole_dur=20.0,atrim=0:20.0,afade=t=out:st=19.5:d=0.5[a]"
        )
        ff(
            "-i", gemini_raw,
            "-loop", "1", "-t", "20", "-i", title_ovl,
            "-i", vo_mp3,
            "-filter_complex", fc,
            "-map", "[v]", "-map", "[a]",
            "-t", "20", "-r", str(FPS),
            "-c:v", "libx264", "-preset", "fast", "-crf", "18", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-ar", "44100", "-ac", "1", "-b:a", "128k",
            intro_mp4,
        )
        title_ovl.unlink(missing_ok=True)
        print(f"[intro] wrote {intro_mp4.name} from gemini_intro_20s.mp4 ({ffdur(intro_mp4):.2f}s)")
        return intro_mp4

    clip_a, clip_b = generate_motion_clips()
    clip_b_titled = OUT_DIR / "_clip_b_titled.mp4"
    fc_b = (
        f"[1:v]fade=t=in:st=1.0:d=0.8:alpha=1[ovl];"
        f"[0:v][ovl]overlay=0:0,fade=t=out:st=9.5:d=0.5,format=yuv420p[v]"
    )
    ff(
        "-i", clip_b,
        "-loop", "1", "-t", "10", "-i", title_ovl,
        "-filter_complex", fc_b,
        "-map", "[v]", "-t", "10", "-r", str(FPS),
        "-c:v", "libx264", "-preset", "fast", "-crf", "18", "-pix_fmt", "yuv420p",
        clip_b_titled,
    )

    fc_intro = (
        f"[0:v]fade=t=in:st=0:d=0.4[va];"
        f"[va][1:v]concat=n=2:v=1:a=0[v];"
        f"[2:a]aresample=44100,pan=mono|c0=c0,apad=whole_dur=20.0,atrim=0:20.0,afade=t=out:st=19.5:d=0.5[a]"
    )
    ff(
        "-i", clip_a,
        "-i", clip_b_titled,
        "-i", vo_mp3,
        "-filter_complex", fc_intro,
        "-map", "[v]", "-map", "[a]",
        "-t", "20", "-r", str(FPS),
        "-c:v", "libx264", "-preset", "fast", "-crf", "18", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-ar", "44100", "-ac", "1", "-b:a", "128k",
        intro_mp4,
    )
    title_ovl.unlink(missing_ok=True)
    clip_b_titled.unlink(missing_ok=True)
    print(f"[intro] wrote {intro_mp4.name} ({ffdur(intro_mp4):.2f}s)")
    return intro_mp4


def assemble_compilation() -> Path:
    final_mp4 = OUT_DIR / "final_comp.mp4"
    segments = [OUT_DIR / "intro.mp4", OUT_DIR / "part_1.mp4"]
    for n in range(2, 7):
        segments.append(OUT_DIR / f"card_{n}.mp4")
        segments.append(OUT_DIR / f"part_{n}.mp4")
    segments.append(OUT_DIR / "outro.mp4")

    parts_txt = OUT_DIR / "parts.txt"
    parts_txt.write_text("".join(f"file '{s.resolve()}'\n" for s in segments))

    t_cursor = 0.0
    chapters = [("00:00", "Intro — If AI Does the Work, Who Gets Paid Next?")]
    t_cursor += ffdur(OUT_DIR / "intro.mp4")
    for part in PARTS:
        n = part["num"]
        if n > 1:
            mm, ss = int(t_cursor // 60), int(round(t_cursor % 60))
            if ss == 60:
                mm += 1
                ss = 0
            chapters.append((f"{mm:02d}:{ss:02d}", part["short_title"]))
            t_cursor += ffdur(OUT_DIR / f"card_{n}.mp4")
            t_cursor += ffdur(OUT_DIR / f"part_{n}.mp4")
        else:
            mm, ss = int(t_cursor // 60), int(round(t_cursor % 60))
            chapters.append((f"{mm:02d}:{ss:02d}", part["short_title"]))
            t_cursor += ffdur(OUT_DIR / "part_1.mp4")

    print("\n=== CHAPTER TIMESTAMPS ===")
    for ts, label in chapters:
        print(f"{ts} {label}")
    (OUT_DIR / "chapters.json").write_text(json.dumps(chapters, indent=2, ensure_ascii=False) + "\n")

    print(f"\n[assemble] concatenating {len(segments)} segments -> {final_mp4.name}...")
    ff(
        "-f", "concat", "-safe", "0", "-i", parts_txt,
        "-c:v", "libx264", "-preset", "fast", "-crf", "20", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-ar", "44100", "-ac", "1", "-b:a", "128k",
        final_mp4,
    )
    total_d = ffdur(final_mp4)
    print(f"[assemble] DONE: {final_mp4} ({total_d:.2f}s = {int(total_d//60)}m{int(total_d%60):02d}s)")
    return final_mp4


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", choices=["parts", "cards", "intro", "assemble", "all"], default="all")
    args = ap.parse_args()

    if args.stage in ("parts", "all"):
        trim_parts()
    if args.stage in ("cards", "all"):
        build_transition_cards()
        build_outro()
    if args.stage in ("intro", "all"):
        build_intro()
    if args.stage in ("assemble", "all"):
        assemble_compilation()


if __name__ == "__main__":
    main()
