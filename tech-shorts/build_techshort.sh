#!/usr/bin/env bash
# build_techshort.sh — assemble a "tech short": hook intro (+ optional VO) + source + branded outro.
#
# Recipe behind the NotebookLM -> hook/outro -> publish pipeline (step 3+4).
# Text cards rendered with Python/PIL (this ffmpeg lacks drawtext); optional
# ElevenLabs hook voiceover; concatenated with the format-matched source.
#
# Usage: build_techshort.sh <source.mp4> <output.mp4> [hook_vo.mp3]

set -e
SRC="$1"; OUT="$2"; VO="$3"; OVO="$4"; TRIM="${5:-0}"
{ [ -z "$SRC" ] || [ -z "$OUT" ]; } && { echo "usage: $0 <source.mp4> <output.mp4> [hook_vo.mp3]"; exit 1; }
WORK="$(mktemp -d)"

W=$(ffprobe -v error -select_streams v:0 -show_entries stream=width  -of csv=p=0 "$SRC")
H=$(ffprobe -v error -select_streams v:0 -show_entries stream=height -of csv=p=0 "$SRC")
FPS=$(ffprobe -v error -select_streams v:0 -show_entries stream=r_frame_rate -of csv=p=0 "$SRC" | cut -d/ -f1)
echo "  source ${W}x${H} @ ${FPS}fps  VO=${VO:-none}"

# --- render text cards (PIL) ---
W=$W H=$H OUT_DIR="$WORK" python3 <<'PY'
import os
from PIL import Image, ImageDraw, ImageFont
W,H,D = int(os.environ["W"]),int(os.environ["H"]),os.environ["OUT_DIR"]
FONT="/System/Library/Fonts/Supplemental/Arial Bold.ttf"
INK=(11,29,38);RED=(232,103,77);TEAL=(79,209,197);MUTE=(157,179,184);WHITE=(231,241,239)
big,med,sm = W//8, W//18, W//30   # big trimmed to W/8 so 'GONE ROGUE' has margin
def font(s): return ImageFont.truetype(FONT,s)
def card(name,lines):
    img=Image.new("RGB",(W,H),INK); dr=ImageDraw.Draw(img)
    dr.rectangle([0,0,W,max(4,H//180)],fill=TEAL); dr.rectangle([0,H-max(4,H//180),W,H],fill=RED)
    for t,c,s,yf in lines:
        f=font(s); tw=dr.textlength(t,font=f); dr.text(((W-tw)/2,H*yf),t,font=f,fill=c)
    img.save(os.path.join(D,name))
card("hookA.png",[("AI AGENTS",WHITE,big,0.28),("GONE ROGUE",RED,big,0.28+big/H+0.02),("Told to stay in a sandbox",MUTE,sm,0.60)])
card("hookB.png",[("Ten broke out.",WHITE,med,0.34),("And lied to real people.",WHITE,med,0.34+med/H+0.02),("A real UK government safety test",TEAL,sm,0.60)])
card("outro.png",[("CANIS",TEAL,big,0.26),("See when an AI is being evasive",WHITE,med,0.26+big/H+0.03),("Open-weight models. On your device.",MUTE,sm,0.52),("canis.flotilla.cc",TEAL,med,0.62),("Follow for more",WHITE,sm,0.74)])
print("  cards rendered")
PY

# --- intro timing (match the VO length if supplied, else 7s) ---
if [ -n "$VO" ] && [ -f "$VO" ]; then
  ID=$(ffprobe -v error -show_entries format=duration -of default=nk=1:nw=1 "$VO"); ID=$(printf "%.2f" "$ID")
else ID=7.0; fi
D1=$(echo "$ID*0.48"|bc); D2=$(echo "$ID-$D1"|bc)
echo "  intro ${ID}s  (cardA ${D1}s + cardB ${D2}s)"

# video-only card segment
vseg(){ # png dur fade_out_start out
  ffmpeg -y -loop 1 -i "$WORK/$1" -t "$2" -r "$FPS" -an \
    -vf "fade=t=in:st=0:d=0.3,fade=t=out:st=$3:d=0.35,format=yuv420p" \
    -c:v libx264 -pix_fmt yuv420p "$WORK/$4" -loglevel error
}
vseg hookA.png "$D1" "$(echo "$D1-0.35"|bc)" a.mp4
vseg hookB.png "$D2" "$(echo "$D2-0.35"|bc)" b.mp4
ffmpeg -y -i "$WORK/a.mp4" -i "$WORK/b.mp4" -filter_complex "[0:v][1:v]concat=n=2:v=1[v]" -map "[v]" -r "$FPS" -c:v libx264 -pix_fmt yuv420p "$WORK/introv.mp4" -loglevel error

# attach audio (VO or silence) -> intro.mp4
if [ -n "$VO" ] && [ -f "$VO" ]; then
  ffmpeg -y -i "$WORK/introv.mp4" -i "$VO" -map 0:v -map 1:a -c:v copy -c:a aac -ar 44100 -ac 1 -shortest "$WORK/intro.mp4" -loglevel error
else
  ffmpeg -y -i "$WORK/introv.mp4" -f lavfi -i "anullsrc=r=44100:cl=mono" -map 0:v -map 1:a -shortest -c:v copy -c:a aac "$WORK/intro.mp4" -loglevel error
fi
echo "  intro built"

# outro (voiceover length if given, else 5s), then attach audio
if [ -n "$OVO" ] && [ -f "$OVO" ]; then OD=$(ffprobe -v error -show_entries format=duration -of default=nk=1:nw=1 "$OVO"); OD=$(printf "%.2f" "$OD"); else OD=5.0; fi
ffmpeg -y -loop 1 -i "$WORK/outro.png" -t "$OD" -r "$FPS" -an \
  -vf "fade=t=in:st=0:d=0.3,fade=t=out:st=$(echo "$OD-0.4"|bc):d=0.4,format=yuv420p" \
  -c:v libx264 -pix_fmt yuv420p "$WORK/outrov.mp4" -loglevel error
if [ -n "$OVO" ] && [ -f "$OVO" ]; then
  ffmpeg -y -i "$WORK/outrov.mp4" -i "$OVO" -map 0:v -map 1:a -c:v copy -c:a aac -ar 44100 -ac 1 -shortest "$WORK/outro.mp4" -loglevel error
else
  ffmpeg -y -i "$WORK/outrov.mp4" -f lavfi -i "anullsrc=r=44100:cl=mono" -map 0:v -map 1:a -shortest -c:v copy -c:a aac "$WORK/outro.mp4" -loglevel error
fi

# normalize source, concat intro + src + outro
SDUR=$(ffprobe -v error -show_entries format=duration -of default=nk=1:nw=1 "$SRC")
KEEP=$(echo "$SDUR - $TRIM" | bc)
[ "$(echo "$TRIM>0"|bc)" = "1" ] && echo "  trimming NotebookLM end-card: last ${TRIM}s (keep ${KEEP}s)"
ffmpeg -y -i "$SRC" -t "$KEEP" -vf "scale=${W}:${H}" -r "$FPS" -c:v libx264 -pix_fmt yuv420p -c:a aac -ar 44100 -ac 1 "$WORK/src.mp4" -loglevel error
ffmpeg -y -i "$WORK/intro.mp4" -i "$WORK/src.mp4" -i "$WORK/outro.mp4" \
  -filter_complex "[0:v][0:a][1:v][1:a][2:v][2:a]concat=n=3:v=1:a=1[v][a]" \
  -map "[v]" -map "[a]" -c:v libx264 -pix_fmt yuv420p -c:a aac -ar 44100 "$OUT" -loglevel error
echo "  built $OUT"
rm -rf "$WORK"
