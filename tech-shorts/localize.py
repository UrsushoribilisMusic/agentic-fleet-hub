#!/usr/bin/env python3
"""
tech-shorts localizer — produces per-language dub audio + subtitles + translated
title/description for a built tech-short.

Runs UNDER the whisper venv (has whisper + anthropic + elevenlabs installed):
    .venv312/bin/python3 localize.py <job_id> <out_dir> <final_video> <langs>

- ASR (Whisper small.en) on the FINAL video (so the dub track lines up with the
  intro hook + content + outro exactly).
- Merge into sentence chunks.
- Per language: Claude translate → ElevenLabs native voice → per-chunk timeslot
  align (atempo<=1.6 + pad to the slot) → concat to an .m4a track matching the
  video duration. Also writes an .srt.
- Writes an English .srt (the default-language caption source).
- Translates the YouTube title + description per language.

Prints one line `RESULT_JSON:{...}` with all produced paths + translated metadata,
which pipeline.py captures and merges into the job. This keeps heavy ML deps in
the venv and out of the pipeline's system-python process.
"""
import json, re, subprocess, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
JOBS_FILE = HERE / "jobs.json"
ENV_FILE = Path("/Users/miguelrodriguez/projects/music-video-tool/.env")

# Native voices (kept identical to the hand-run dubs so a channel's voice is
# consistent across every video): Sophia (DE), Nathalie (FR).
VOICES = {"de": "QT6va3HQK8j63EC2r9cw", "fr": "rS7c1woNY04WT3UAS83Y"}
LANGNAME = {"de": "German", "fr": "French"}
MODEL_TTS = "eleven_multilingual_v2"
TRANS_MODEL = "claude-haiku-4-5-20251001"


def env(k: str) -> str:
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            if line.startswith(k + "="):
                return line.split("=", 1)[1].strip()
    return ""


def log(*a):
    print(f"[{time.strftime('%H:%M:%S')}]", *a, flush=True)


def ffdur(p) -> float:
    return float(subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)],
        capture_output=True, text=True).stdout.strip() or 0)


def asr(video: Path):
    import whisper
    model = whisper.load_model("small.en")
    r = model.transcribe(str(video), language="en", verbose=False)
    return [{"start": round(s["start"], 2), "end": round(s["end"], 2), "text": s["text"].strip()}
            for s in r["segments"]]


def merge(segs):
    chunks, cur = [], None
    for s in segs:
        if cur is None:
            cur = {"start": s["start"], "end": s["end"], "text": s["text"]}
        else:
            cur["end"] = s["end"]; cur["text"] += " " + s["text"]
        dur = cur["end"] - cur["start"]
        if (re.search(r"[.!?]$", cur["text"].strip()) and dur >= 5.0) or dur >= 22.0:
            cur["text"] = re.sub(r"\s+", " ", cur["text"]).strip()
            chunks.append(cur); cur = None
    if cur:
        cur["text"] = re.sub(r"\s+", " ", cur["text"]).strip()
        chunks.append(cur)
    return chunks


def translate_chunks(an, texts, lang):
    ln = LANGNAME[lang]
    SYS = (f"You are a professional dub/subtitle translator. Translate each numbered English segment into "
           f"natural, spoken {ln} suitable for a voice-over. Keep technical terms accurate. Spell out numbers "
           f"and percentages as words in {ln} for text-to-speech. Do not use em-dashes. Return ONLY a JSON "
           f"array of strings, one per input segment, same count and order, no commentary.")
    out = []
    B = 15
    for i in range(0, len(texts), B):
        batch = texts[i:i + B]
        prompt = "\n".join(f"{j}. {t}" for j, t in enumerate(batch))
        for attempt in range(2):
            msg = an.messages.create(model=TRANS_MODEL, max_tokens=8000, system=SYS,
                                     messages=[{"role": "user", "content": prompt}])
            raw = re.sub(r"^```(json)?|```$", "", msg.content[0].text.strip(), flags=re.M).strip()
            m = re.search(r"\[.*\]", raw, re.S)
            try:
                arr = json.loads(m.group(0) if m else raw)
                if len(arr) == len(batch):
                    out += [str(x) for x in arr]; break
            except Exception:
                pass
            if attempt == 1:  # one-by-one fallback
                for t in batch:
                    mm = an.messages.create(model=TRANS_MODEL, max_tokens=1000, system=SYS,
                                            messages=[{"role": "user", "content": "0. " + t}])
                    r2 = re.sub(r"^```(json)?|```$", "", mm.content[0].text.strip(), flags=re.M).strip()
                    mx = re.search(r"\[.*\]", r2, re.S)
                    out.append(str(json.loads(mx.group(0) if mx else r2)[0]))
                break
    return out


def translate_meta(an, title, desc, lang):
    ln = LANGNAME[lang]
    sysp = (f"Translate the title and description below into natural, fluent {ln}. Keep ALL URLs and "
            f"#hashtags EXACTLY as they are (do not translate or alter them). Keep the title concise, under "
            f"100 characters. Keep technical terms accurate. Do not use em-dashes. Output EXACTLY in this "
            f"format, nothing else:\n<<<TITLE>>>\n(translated title, one line)\n<<<DESC>>>\n(translated "
            f"description, may span lines)")
    msg = an.messages.create(model=TRANS_MODEL, max_tokens=4000, system=sysp,
                             messages=[{"role": "user", "content": f"TITLE:\n{title}\n\nDESCRIPTION:\n{desc}"}])
    after = msg.content[0].text.split("<<<TITLE>>>", 1)[1]
    tpart, dpart = after.split("<<<DESC>>>", 1)
    return tpart.strip()[:100], dpart.strip()[:4900]


def tts(el, text, out, voice):
    it = el.text_to_speech.convert(voice_id=voice, text=text, model_id=MODEL_TTS, output_format="mp3_44100_128")
    with open(out, "wb") as f:
        for c in it:
            f.write(c)


def assemble(el, chunks, texts, voice, video_dur, out_m4a, tmp):
    tmp.mkdir(parents=True, exist_ok=True)
    starts = [c["start"] for c in chunks]
    slots = [(starts[i + 1] - starts[i]) if i + 1 < len(starts) else max(video_dur - starts[i], 1.0)
             for i in range(len(starts))]
    pieces = []
    for i, t in enumerate(texts):
        raw = tmp / f"{i:03d}.mp3"; tts(el, t, raw, voice)
        di = ffdur(raw); sl = slots[i]
        tempo = 1.0 if di <= sl else min(di / sl, 1.6)
        piece = tmp / f"p{i:03d}.wav"
        subprocess.run(["ffmpeg", "-y", "-i", str(raw), "-af", f"atempo={tempo:.4f},apad",
                        "-t", f"{sl:.3f}", "-ar", "44100", "-ac", "2", str(piece)], capture_output=True)
        pieces.append(piece)
    lst = tmp / "list.txt"; lst.write_text("".join(f"file '{p}'\n" for p in pieces))
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lst),
                    "-c:a", "aac", "-b:a", "192k", str(out_m4a)], capture_output=True)


def _ts(s):
    h = int(s // 3600); m = int((s % 3600) // 60); sec = s % 60
    return f"{h:02d}:{m:02d}:{sec:06.3f}".replace(".", ",")


def write_srt(chunks, texts, path):
    Path(path).write_text("\n".join(
        f"{i}\n{_ts(c['start'])} --> {_ts(c['end'])}\n{t}\n" for i, (c, t) in enumerate(zip(chunks, texts), 1)),
        encoding="utf-8")


def main():
    job_id, out_dir, final_video, langs_csv = sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3]), sys.argv[4]
    langs = [l.strip() for l in langs_csv.split(",") if l.strip()]
    out_dir.mkdir(parents=True, exist_ok=True)

    data = json.load(open(JOBS_FILE))
    job = next(j for j in data["jobs"] if j["id"] == job_id or j.get("slug") == job_id)
    yt = job.get("youtube", {})
    title = yt.get("title_long") or job["title"]
    desc = yt.get("description") or job.get("idea_notes", "")

    from elevenlabs.client import ElevenLabs
    import anthropic
    el = ElevenLabs(api_key=env("ELEVENLABS_API_KEY"))
    an = anthropic.Anthropic(api_key=env("ANTHROPIC_API_KEY"), timeout=90.0, max_retries=4)

    dur = ffdur(final_video)
    log(f"ASR on {final_video.name} ({dur:.0f}s)...")
    chunks = merge(asr(final_video))
    log(f"{len(chunks)} chunks")

    en_srt = out_dir / f"{job['slug']}_en.srt"
    write_srt(chunks, [c["text"] for c in chunks], en_srt)

    result = {"captions_en_srt": str(en_srt), "localizations": {}}
    for lang in langs:
        if lang not in VOICES:
            log(f"skip unknown lang {lang}"); continue
        tr = translate_chunks(an, [c["text"] for c in chunks], lang)
        log(f"translated narration {lang} ({len(tr)})")
        m4a = out_dir / f"{job['slug']}_audio_{lang}.m4a"
        assemble(el, chunks, tr, VOICES[lang], dur, m4a, out_dir / f"_dubtmp_{lang}")
        srt = out_dir / f"{job['slug']}_{lang}.srt"
        write_srt(chunks, tr, srt)
        t_title, t_desc = translate_meta(an, title, desc, lang)
        result["localizations"][lang] = {
            "title": t_title, "description": t_desc,
            "audio": str(m4a), "srt": str(srt),
        }
        log(f"DONE {lang}: audio={m4a.name} ({ffdur(m4a):.0f}s) srt={srt.name} title={t_title!r}")

    print("RESULT_JSON:" + json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
