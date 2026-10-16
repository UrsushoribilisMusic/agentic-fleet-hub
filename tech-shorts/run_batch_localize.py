#!/usr/bin/env python3
"""
Batch localizer for Job 1 (Convergence Point) and Job 2 (How to Be More Ambitious).
Generates:
  - English SRT
  - German, French, Japanese SRTs
  - German and French ElevenLabs audio dubs (.m4a)
  - Stages all files into ~/Downloads/tech-shorts-captions/<slug>/
  - Updates jobs.json with localization metadata
"""
import json, os, re, subprocess, sys, time, shutil
from pathlib import Path
from dotenv import load_dotenv

# Load Infisical credentials
load_dotenv("/Users/miguelrodriguez/projects/music-video-tool/.env")
sys.path.insert(0, "/Users/miguelrodriguez/projects/agentic-fleet-hub/vault")
from vault import get_secret
API_KEY = get_secret("ELEVENLABS_API_KEY")
if not API_KEY:
    sys.exit("ELEVENLABS_API_KEY not found in vault")

from elevenlabs.client import ElevenLabs
el = ElevenLabs(api_key=API_KEY)

VOICE_DE = "QT6va3HQK8j63EC2r9cw"
VOICE_FR = "rS7c1woNY04WT3UAS83Y"
MODEL_TTS = "eleven_multilingual_v2"
DOWNLOADS_STAGING = Path("/Users/miguelrodriguez/Downloads/tech-shorts-captions")

def log(*args):
    print(f"[{time.strftime('%H:%M:%S')}]", *args, flush=True)

def ffdur(p) -> float:
    return float(subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)],
        capture_output=True, text=True).stdout.strip() or 0)

def _ts(s):
    h = int(s // 3600); m = int((s % 3600) // 60); sec = s % 60
    return f"{h:02d}:{m:02d}:{sec:06.3f}".replace(".", ",")

def write_srt(chunks, texts, path):
    Path(path).write_text("\n".join(
        f"{i}\n{_ts(c['start'])} --> {_ts(c['end'])}\n{t}\n" for i, (c, t) in enumerate(zip(chunks, texts), 1)),
        encoding="utf-8")

def tts(text, out_mp3, voice_id):
    it = el.text_to_speech.convert(voice_id=voice_id, text=text, model_id=MODEL_TTS, output_format="mp3_44100_128")
    with open(out_mp3, "wb") as f:
        for c in it: f.write(c)
    return out_mp3

def assemble_dub(chunks, texts, voice_id, video_dur, out_m4a, tmp_dir):
    tmp_dir.mkdir(parents=True, exist_ok=True)
    starts = [c["start"] for c in chunks]
    slots = [(starts[i + 1] - starts[i]) if i + 1 < len(starts) else max(video_dur - starts[i], 1.0)
             for i in range(len(starts))]
    pieces = []
    log(f"  Generating {len(texts)} audio segments with voice {voice_id}...")
    for i, t in enumerate(texts):
        raw_mp3 = tmp_dir / f"{i:03d}.mp3"
        if not raw_mp3.exists() or raw_mp3.stat().st_size == 0:
            tts(t, raw_mp3, voice_id)
            time.sleep(0.1)
        di = ffdur(raw_mp3)
        sl = slots[i]
        tempo = 1.0 if di <= sl else min(di / sl, 1.6)
        piece = tmp_dir / f"p{i:03d}.wav"
        subprocess.run(["ffmpeg", "-y", "-i", str(raw_mp3), "-af", f"atempo={tempo:.4f},apad",
                        "-t", f"{sl:.3f}", "-ar", "44100", "-ac", "2", str(piece)],
                       capture_output=True, check=True)
        pieces.append(piece)
        if (i + 1) % 10 == 0 or (i + 1) == len(texts):
            log(f"    progress: {i + 1}/{len(texts)} segments ready")
    lst = tmp_dir / "list.txt"
    lst.write_text("".join(f"file '{p}'\n" for p in pieces))
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lst),
                    "-c:a", "aac", "-b:a", "192k", str(out_m4a)], capture_output=True, check=True)
    log(f"  Dub track written: {out_m4a} ({ffdur(out_m4a):.1f}s)")
