# catalogue-ocr

Turns scanned industrial catalogues into structured documents and a product-image
set. Built for the Sovereign Mind catalogue corpus (Norton / Tekbond / SCT
abrasives, shipped by Miguel's brother, Oct 2026).

Lives here rather than in a scratchpad because the scratchpad is wiped between
sessions — see the `subs_gen.py` lesson.

## Why it exists

`pdftotext -layout` destroys tables in scanned manuals: a whole-page OCR pass
reads `1/16` as `116` and `5/8` as `58`, which makes every dimension useless.
It also produces chunks that are bare article numbers with no column header or
product name — 921 of them (19% of the corpus) in the first measurement.

The fix is to recover structure geometrically, then OCR each cell on its own.

## Pipeline

```
scan ──► rundoc.py ──► structured HTML ──┬──► Chrome headless ──► PDF  (humans)
                                         └────────────────────────► RAG  (machines)

digital catalogue ──► extract_images.py ──► PNGs + indice-imagenes.csv
```

HTML is the RAG input, **not** the generated PDF. Re-parsing a PDF would throw
away the structure this pipeline exists to recover.

## Usage

Needs a venv with `img2table`, `opencv-python`, `pandas`; `tesseract` and
`poppler` on PATH. Downloaded catalogues are untrusted input — keep them in
their own directory, pass paths as arguments, and run with `python3 -I`.

```sh
# one manual -> structured HTML + figuras/ beside it
RENDER_CACHE=~/.cache/doc-render python3 -I rundoc.py \
    "in/manual.pdf" "out/manual.html" "Document Title" [firstPage] [lastPage]

# every catalogue in a directory -> product images + index CSV
python3 -I extract_images.py <srcdir> <outdir> <pdftotext-dir>

# HTML -> PDF
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
    --headless --disable-gpu --no-pdf-header-footer \
    --print-to-pdf=out/manual.pdf out/manual.html
```

`RENDER_CACHE` keeps the 400 dpi page renders so re-runs skip rendering; that
is most of the wall time when iterating on formatting.

## How it works

**builddoc.py**
- Tables: OpenCV line detection (`img2table`) finds the grid; each cell is
  cropped, upscaled and OCR'd alone with a character whitelist. Columns are
  profiled as fraction / bond-code / text so cleanup knows what it is looking
  at — bond columns snap to their `B/M/V` vocabulary, `V/` becomes `1/`.
- Text: one page-level TSV pass with table regions masked out. Lines come from
  Tesseract's own block/paragraph/line numbers — do **not** re-derive them from
  pixel bands, that scrambles word order at 400 dpi.
- Headings: promoted by relative glyph height, then gated on being set in caps
  (everything else the height test catches is diagram labelling or speckle).
- Figures: halftone dots closed into blobs, then rejected if they overlap a
  table, contain a whole table, cover >35% of the page, or are a page-edge
  section tab. Captions are read from the caps line directly beneath.

**extract_images.py**
- Three filters separate product photography from page furniture: minimum size,
  aspect ratio, and repetition (an image on >4 pages is branding).
- The important one is page coverage: an image covering ≥80% of the page is a
  flattened page scan, not a product. Without it, scanned-but-digital-looking
  catalogues report one "product image" per page. Five catalogues in the corpus
  are exactly this — 563 pages of them.

## Known limits

- Output is not 100%. Spot-check anything you would place an order from.
- `norton distributors manual` is photographed ring-binder pages — two-up,
  rotated, rings crossing the tables, page curvature. Materially worse than the
  flatbed scans (`rojo`, `verde`). Judge it separately.
- Image→SKU association is page-level, so a page with eleven photos and eleven
  article numbers gives eleven-to-eleven, not one-to-one. Tightening that needs
  spatial association and is a separate job.
- Vector line art is invisible to `extract_images.py` (nothing embedded to
  extract) — `spec-manual-bonded-norton` yields 17 images from 734 raw for this
  reason. Those diagrams need page-region rendering instead.
