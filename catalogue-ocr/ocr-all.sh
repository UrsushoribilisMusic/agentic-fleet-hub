#!/usr/bin/env bash
# OCR every image-only PDF in the shipment. English: all six are English-language
# scans despite the Spanglish filenames (verified by sampling page 30 of each).
SC="$(cd "$(dirname "$0")" && pwd)"
D="/Users/miguelrodriguez/Downloads/drive-download-20261021T092031Z-1-001"
O="/Users/miguelrodriguez/Downloads/sm-catalogues-assessment/ocr"
mkdir -p "$O"
# smallest first, so failures surface early
FILES=(
  "abrasives for man made board sanding-001"
  "coated abrasives training basic"
  "coated abrasives training application"
  "especification manual verde"
  "norton distributors manual"
  "especification manual rojo"
)
echo "=== OCR run started $(date '+%H:%M:%S') ==="
for f in "${FILES[@]}"; do
  [ -s "$O/$f.txt" ] && { echo "[$f] already done, skipping"; continue; }
  "$SC/ocr.sh" "$D/$f.pdf" "$O" eng
done
echo "=== OCR run finished $(date '+%H:%M:%S') ==="
ls -la "$O"
