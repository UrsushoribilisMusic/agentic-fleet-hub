#!/usr/bin/env bash
# OCR one image-only PDF -> searchable PDF + plain text.
#   ocr.sh <input.pdf> <outdir> [langs]
set -uo pipefail
IN="$1"; OUTDIR="$2"; LANGS="${3:-eng}"
B="$(basename "$IN" .pdf)"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
mkdir -p "$OUTDIR"

echo "[$B] rendering pages at 300dpi…"
pdftoppm -r 300 -gray -png "$IN" "$WORK/pg" 2>/dev/null
N=$(ls "$WORK"/pg-*.png 2>/dev/null | wc -l | tr -d ' ')
echo "[$B] $N pages -> OCR ($LANGS)"

# -c preserve_interword_spaces=1 keeps the column gaps that dimension tables rely on.
ls "$WORK"/pg-*.png | xargs -P 8 -I{} sh -c \
  'tesseract "$1" "${1%.png}" -l '"$LANGS"' --oem 1 --psm 1 \
     -c preserve_interword_spaces=1 txt pdf >/dev/null 2>&1' _ {}

cat $(ls "$WORK"/pg-*.txt 2>/dev/null | sort) > "$OUTDIR/$B.txt" 2>/dev/null
PDFS=$(ls "$WORK"/pg-*.pdf 2>/dev/null | sort | tr '\n' ' ')
if [ -n "$PDFS" ]; then
  pdfunite $PDFS "$OUTDIR/$B.searchable.pdf" 2>/dev/null \
    && echo "[$B] pdf ok" || echo "[$B] pdfunite FAILED"
fi
CH=$(wc -c < "$OUTDIR/$B.txt" 2>/dev/null | tr -d ' ')
echo "[$B] DONE  pages=$N  chars=$CH  ($((CH/(N>0?N:1))) per page)"
