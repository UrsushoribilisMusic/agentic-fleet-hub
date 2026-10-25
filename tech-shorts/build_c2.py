#!/usr/bin/env python3
"""Build Compilation C2: The Attack Surface in Your House (TSC-2).

Implements COMPILATION_PLAYBOOK.md §2 and §3:
- §3.1 Trim each of the 7 parts to exact verified in/out bounds, normalized to
  1920x1080 @ 30fps, yuv420p, aac 44100Hz mono.
- §3.2 Build the 20s motion cold open from Miguel's 20s Gemini motion video
  (gemini_generated_video_c95c4bb0.mp4) with the channel title card composited
  over the second 10s half (Clip B) and the Kokoro channel hook VO underneath.
- §3.3 Build 6x 4-second chapter transition cards before parts 2..7: part number
  small, transition line large, held on a slow push-in over a dimmed still from
  the part that follows, with 0.5s fade in and out.
- §3.4 Concat intro + part_1 + (card_2, part_2) .. (card_7, part_7) + outro into
  final_comp.mp4.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import pipeline as P

OUT_DIR = Path("/Users/miguelrodriguez/flotilla/tech-shorts/assets/2026-10-25-compilation-c2-the-attack-surface-in-your-house")
GEMINI_INTRO = Path("/Users/miguelrodriguez/Downloads/gemini_generated_video_c95c4bb0.mp4")
W, H, FPS = 1920, 1080, 30

# Verified in/out points for C2 parts (COMPILATION_PLAYBOOK.md §2 & §3.1)
PARTS = [
    {
        "num": 1,
        "vid": "ECuneH0hPcg",
        "kind": "final_long",
        "path": "/Users/miguelrodriguez/flotilla/tech-shorts/assets/2026-10-03-japan-aisi-cyber-eval/final_long.mp4",
        "in": 16.70,
        "out": 301.98,
        "title": "Can AI Build Autonomous Cyber Exploits? Japan AISI Tested US vs Chinese Frontier Models on Real Hacking",
        "short_title": "1. Japan Tested US vs Chinese AI on Real Hacking",
        "card_num": None,
        "card_line": None,
    },
    {
        "num": 2,
        "vid": "KbxsK1LlVSw",
        "kind": "final_long",
        "path": "/Users/miguelrodriguez/flotilla/tech-shorts/assets/2026-09-11-secure-your-keys-supply-chain/final_long.mp4",
        "in": 12.96,
        "out": 296.80,
        "title": "Secure Your API Keys: How Stolen Keys Became the AI Underworld's Free Weapon",
        "short_title": "2. Secure Your API Keys: Stolen Keys as the AI Underworld's Free Weapon",
        "card_num": "TWO",
        "card_line": "The keys were never the hard part.",
    },
    {
        "num": 3,
        "vid": "n0J3a4-1rmY",
        "kind": "final_long",
        "path": "/Users/miguelrodriguez/flotilla/tech-shorts/assets/2026-09-11-exploit-foundry-two-students/final_long.mp4",
        "in": 12.90,
        "out": 228.04,
        "title": "Two Students Built an AI Zero-Day Factory: Inside China's Automated Cyber Espionage Pipeline",
        "short_title": "3. Two Students Built an AI Zero-Day Factory",
        "card_num": "THREE",
        "card_line": "Two students. One pipeline. Every exploit.",
    },
    {
        "num": 4,
        "vid": "D-LV9YJN2ZM",
        "kind": "raw_cinematic",
        "path": "/Users/miguelrodriguez/flotilla/tech-shorts/assets/2026-10-14-the-convenience-paradox-why-the-internet-of-things-is-melting/raw_cinematic.mp4",
        "in": 0.00,
        "out": 309.67,
        "title": "The Convenience Paradox: Why the Internet of Things is Melting",
        "short_title": "4. The Convenience Paradox: Why the Internet of Things is Melting",
        "card_num": "FOUR",
        "card_line": "Everything in your house is now a computer.",
    },
    {
        "num": 5,
        "vid": "GLLa6t_MQuA",
        "kind": "raw_cinematic",
        "path": "/Users/miguelrodriguez/flotilla/tech-shorts/assets/2026-10-13-the-convergence-point-why-ai-worms-are-targeting-your-smart-tv/raw_cinematic.mp4",
        "in": 0.00,
        "out": 304.02,
        "title": "The Convergence Point: When AI Worms Self-Replicate on Smart TVs",
        "short_title": "5. The Convergence Point: When AI Worms Self-Replicate on Smart TVs",
        "card_num": "FIVE",
        "card_line": "And computers can be told to copy themselves.",
    },
    {
        "num": 6,
        "vid": "lZ_LLtp8Ulo",
        "kind": "raw_cinematic",
        "path": "/Users/miguelrodriguez/flotilla/tech-shorts/assets/2026-10-14-the-shadow-datacenter-why-ai-worms-are-targeting-your-smart-tv/raw_cinematic.mp4",
        "in": 0.00,
        "out": 355.55,
        "title": "The Shadow Datacenter: Why AI Worms Are Targeting Your Smart TV",
        "short_title": "6. The Shadow Datacenter: Why AI Worms Are Targeting Your Smart TV",
        "card_num": "SIX",
        "card_line": "Your television has more idle compute than you think.",
    },
    {
        "num": 7,
        "vid": "cRgmoG-XqkQ",
        "kind": "raw_cinematic",
        "path": "/Users/miguelrodriguez/flotilla/tech-shorts/assets/2026-10-10-models-as-insider-risks-in-the-super-intelligence-era/raw_cinematic.mp4",
        "in": 0.00,
        "out": 480.46,
        "title": "Models as Insider Risks: Why AI Agents Need Zero-Trust Authority",
        "short_title": "7. Models as Insider Risks: Why AI Agents Need Zero-Trust Authority",
        "card_num": "SEVEN",
        "card_line": "The threat with your own credentials.",
    },
]

HOOK_VO_TEXT = (
    "At three in the morning, every screen in your house is dark, but the network "
    "never sleeps. From stolen API keys and two-student zero-day factories to "
    "self-replicating AI worms turning smart televisions into a shadow datacenter, "
    "the offensive frontier has moved inside the home. Across seven investigations, "
    "here is the real attack surface in your house."
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
    chunks = [audio for _, _, audio in pipe(text, voice="af_bella", speed=1.20) if audio is not None]
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
                print(f"[part_{n}] reusing {out_mp4.name} ({d:.2f}s)", flush=True)
                continue
        tin = part["in"]
        tout = part["out"]
        dur = tout - tin
        fade_out_st = max(0.0, dur - 0.25)
        print(f"[part_{n}] trimming {part['vid']} ({tin:.2f}s -> {tout:.2f}s = {dur:.2f}s)...", flush=True)
        ff(
            "-ss", f"{tin:.3f}",
            "-to", f"{tout:.3f}",
            "-i", part["path"],
            "-vf", f"scale={W}:{H}:flags=lanczos,fps={FPS},format=yuv420p",
            "-af", f"afade=t=in:st=0:d=0.15,afade=t=out:st={fade_out_st:.3f}:d=0.20",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-ar", "44100", "-ac", "1", "-b:a", "128k",
            out_mp4,
        )
        print(f"[part_{n}] wrote {out_mp4.name} ({ffdur(out_mp4):.2f}s)", flush=True)


def render_transition_overlay(out_png: Path, card_num: str, card_line: str) -> None:
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
            print(f"[card_{n}] reusing {card_mp4.name} ({ffdur(card_mp4):.2f}s)", flush=True)
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

        print(f"[card_{n}] rendering 4s transition card: {part['card_num']} — {part['card_line']}", flush=True)
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
        print(f"[card_{n}] wrote {card_mp4.name} ({ffdur(card_mp4):.2f}s)", flush=True)


def build_outro() -> None:
    outro_mp4 = OUT_DIR / "outro.mp4"
    if outro_mp4.exists() and outro_mp4.stat().st_size > 20_000:
        print(f"[outro] reusing {outro_mp4.name} ({ffdur(outro_mp4):.2f}s)", flush=True)
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
    print(f"[outro] wrote {outro_mp4.name} ({ffdur(outro_mp4):.2f}s)", flush=True)


def build_intro() -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    raw_dest = OUT_DIR / "gemini_intro_20s.mp4"
    shutil.copy2(GEMINI_INTRO, raw_dest)

    vo_mp3 = OUT_DIR / "c2_hook_vo.mp3"
    if not vo_mp3.exists():
        generate_kokoro_vo(HOOK_VO_TEXT, vo_mp3)
    print(f"[intro] Kokoro hook VO duration: {ffdur(vo_mp3):.2f}s", flush=True)

    title_ovl = OUT_DIR / "_intro_title_overlay.png"
    img = Image.new("RGBA", (W, H), (11, 29, 38, 155))
    dr = ImageDraw.Draw(img)
    bar_h = max(6, H // 160)
    dr.rectangle([0, 0, W, bar_h], fill=(*P.TEAL, 255))
    dr.rectangle([0, H - bar_h, W, H], fill=(*P.RED, 255))

    lines = [
        ("WHAT IS RUNNING ON YOUR", P.WHITE, 96, None),
        ("LIVING ROOM NETWORK?", P.RED, 96, 0.015),
        ("The Attack Surface in Your House · Seven Investigations", P.WHITE, 46, 0.05),
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
    img.save(str(title_ovl))

    intro_mp4 = OUT_DIR / "intro.mp4"
    fc = (
        f"[0:v]scale={W}:{H}:flags=lanczos,fps={FPS},format=yuv420p,fade=t=in:st=0:d=0.4[base];"
        f"[1:v]fade=t=in:st=11.0:d=0.8:alpha=1[ovl];"
        f"[base][ovl]overlay=0:0:enable='gte(t,10.8)',fade=t=out:st=19.5:d=0.5,format=yuv420p[v];"
        f"[2:a]atempo=1.06,aresample=44100,pan=mono|c0=c0,apad=whole_dur=20.0,atrim=0:20.0,afade=t=out:st=19.5:d=0.5[a]"
    )
    ff(
        "-i", raw_dest,
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
    print(f"[intro] wrote {intro_mp4.name} ({ffdur(intro_mp4):.2f}s)", flush=True)
    return intro_mp4


def assemble_compilation() -> Path:
    final_mp4 = OUT_DIR / "final_comp.mp4"
    segments = [OUT_DIR / "intro.mp4", OUT_DIR / "part_1.mp4"]
    for n in range(2, 8):
        segments.append(OUT_DIR / f"card_{n}.mp4")
        segments.append(OUT_DIR / f"part_{n}.mp4")
    segments.append(OUT_DIR / "outro.mp4")

    parts_txt = OUT_DIR / "parts.txt"
    parts_txt.write_text("".join(f"file '{s.resolve()}'\n" for s in segments))

    t_cursor = 0.0
    chapters = [("00:00", "Intro — What Is Running on Your Living Room Network?")]
    t_cursor += ffdur(OUT_DIR / "intro.mp4")
    for part in PARTS:
        n = part["num"]
        if n > 1:
            mm, ss = int(t_cursor // 60), int(round(t_cursor % 60))
            if ss == 60:
                mm += 1; ss = 0
            chapters.append((f"{mm:02d}:{ss:02d}", part["short_title"]))
            t_cursor += ffdur(OUT_DIR / f"card_{n}.mp4")
            t_cursor += ffdur(OUT_DIR / f"part_{n}.mp4")
        else:
            mm, ss = int(t_cursor // 60), int(round(t_cursor % 60))
            chapters.append((f"{mm:02d}:{ss:02d}", part["short_title"]))
            t_cursor += ffdur(OUT_DIR / "part_1.mp4")

    print("\n=== C2 CHAPTER TIMESTAMPS ===", flush=True)
    for ts, label in chapters:
        print(f"{ts} {label}", flush=True)
    (OUT_DIR / "chapters.json").write_text(json.dumps(chapters, indent=2, ensure_ascii=False) + "\n")

    print(f"\n[assemble] concatenating {len(segments)} segments -> {final_mp4.name}...", flush=True)
    ff(
        "-f", "concat", "-safe", "0", "-i", parts_txt,
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-ar", "44100", "-ac", "1", "-b:a", "128k",
        final_mp4,
    )
    total_d = ffdur(final_mp4)
    print(f"[assemble] DONE: {final_mp4} ({total_d:.2f}s = {int(total_d//60)}m{int(total_d%60):02d}s)", flush=True)
    return final_mp4


if __name__ == "__main__":
    build_intro()
    trim_parts()
    build_transition_cards()
    build_outro()
    assemble_compilation()
