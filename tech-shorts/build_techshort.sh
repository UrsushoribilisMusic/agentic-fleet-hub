#!/usr/bin/env bash
# build_techshort.sh — assemble a "tech short": hook intro + source video + branded outro.
#
# Recipe behind the NotebookLM -> hook/outro -> publish pipeline (step 3+4).
# Text cards are rendered with Python/PIL (this ffmpeg lacks drawtext/libfreetype),
# turned into video segments, and concatenated with the format-matched source.
#
# Usage: build_techshort.sh <source.mp4> <output.mp4>

set -e
SRC="$1"; OUT="$2"
{ [ -z "$SRC" ] || [ -z "$OUT" ]; } && { echo "usage: $0 <source.mp4> <output.mp4>"; exit 1; }
WORK="$(mktemp -d)"

# match source format
W=$(ffprobe -v error -select_streams v:0 -show_entries stream=width  -of csv=p=0 "$SRC")
H=$(ffprobe -v error -select_streams v:0 -show_entries stream=height -of csv=p=0 "$SRC")
FPS=$(ffprobe -v error -select_streams v:0 -show_entries stream=r_frame_rate -of csv=p=0 "$SRC" | cut -d/ -f1)
echo "  source ${W}x${H} @ ${FPS}fps"

# --- render the three text cards (PIL) ---
W=$W H=$H OUT_DIR="$WORK" python3 <<'PY'
import os
from PIL import Image, ImageDraw, ImageFont
W, H, D = int(os.environ["W"]), int(os.environ["H"]), os.environ["OUT_DIR"]
FONT = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
INK=(11,29,38); RED=(232,103,77); TEAL=(79,209,197); MUTE=(157,179,184); WHITE=(231,241,239)
big, med, sm = W//7, W//18, W//30
def font(s): return ImageFont.truetype(FONT, s)
def card(name, lines):
    img = Image.new("RGB", (W, H), INK); dr = ImageDraw.Draw(img)
    # subtle brand accents
    dr.rectangle([0, 0, W, max(4, H//180)], fill=TEAL)
    dr.rectangle([0, H-max(4, H//180), W, H], fill=RED)
    for text, color, size, yf in lines:
        f = font(size); tw = dr.textlength(text, font=f)
        dr.text(((W-tw)/2, H*yf), text, font=f, fill=color)
    img.save(os.path.join(D, name))
card("hookA.png", [("AI AGENTS", WHITE, big, 0.28), ("GONE ROGUE", RED, big, 0.28+big/H+0.02),
                   ("Told to stay in a sandbox", MUTE, sm, 0.60)])
card("hookB.png", [("Ten broke out.", WHITE, med, 0.34), ("And lied to real people.", WHITE, med, 0.34+med/H+0.02),
                   ("A real UK government safety test", TEAL, sm, 0.60)])
card("outro.png", [("CANIS", TEAL, big, 0.26), ("See when an AI is being evasive", WHITE, med, 0.26+big/H+0.03),
                   ("Open-weight models. On your device.", MUTE, sm, 0.52),
                   ("canis.flotilla.cc", TEAL, med, 0.62), ("Follow for more", WHITE, sm, 0.74)])
print("  cards rendered")
PY

# --- image card -> video segment (silent audio, fade in/out) ---
seg(){ # $1 png  $2 dur  $3 out
  ffmpeg -y -loop 1 -i "$WORK/$1" -f lavfi -i "anullsrc=r=44100:cl=mono" -t "$2" \
    -vf "fade=t=in:st=0:d=0.3,fade=t=out:st=$(echo "$2-0.4"|bc):d=0.4,format=yuv420p" \
    -r "$FPS" -c:v libx264 -pix_fmt yuv420p -c:a aac -ar 44100 -ac 1 "$WORK/$3" -loglevel error
}
seg hookA.png 3.5 s1.mp4
seg hookB.png 3.5 s2.mp4
seg outro.png 5   s4.mp4
echo "  intro/outro segments built"

# --- normalize source, then concat: hookA + hookB + src + outro ---
ffmpeg -y -i "$SRC" -vf "scale=${W}:${H}" -r "$FPS" -c:v libx264 -pix_fmt yuv420p -c:a aac -ar 44100 -ac 1 "$WORK/s3.mp4" -loglevel error
echo "  source normalized"
ffmpeg -y -i "$WORK/s1.mp4" -i "$WORK/s2.mp4" -i "$WORK/s3.mp4" -i "$WORK/s4.mp4" \
  -filter_complex "[0:v][0:a][1:v][1:a][2:v][2:a][3:v][3:a]concat=n=4:v=1:a=1[v][a]" \
  -map "[v]" -map "[a]" -c:v libx264 -pix_fmt yuv420p -c:a aac -ar 44100 "$OUT" -loglevel error
echo "  built $OUT"
rm -rf "$WORK"
