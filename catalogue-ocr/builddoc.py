"""Scanned technical manual -> structured HTML (headings + real tables) + XLSX.

Structure comes from OpenCV line detection (img2table); cell content from
per-cell Tesseract with a character whitelist; non-table text is recovered from
a page-level TSV pass with table regions masked out, and lines are promoted to
headings by relative glyph height.
"""
import sys, os, re, html, subprocess, tempfile, csv, io, json
from concurrent.futures import ThreadPoolExecutor
import cv2
from img2table.document import Image as I2TImage
from img2table.ocr import TesseractOCR

WL = "0123456789/.,-ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz ()*+#&%\"'"
FRACTION = re.compile(r'^\d{0,2}[-\s]?\d{0,2}/\d{1,3}$|^\.\d+$|^\d{1,3}$|^\d{1,2}-\d{1,2}/\d{1,2}$')

def _tess(path, psm, whitelist=True, tsv=False):
    cmd = ["tesseract", path, "-", "--oem", "1", "--psm", str(psm)]
    if whitelist: cmd += ["-c", f"tessedit_char_whitelist={WL}"]
    if tsv: cmd += ["tsv"]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
        return r.stdout
    except Exception:
        return ""

# ---------- cell content ----------
def ocr_cell(job):
    img, (x1, y1, x2, y2) = job
    crop = img[y1+3:y2-3, x1+3:x2-3]
    if crop.size == 0 or crop.shape[0] < 8 or crop.shape[1] < 8: return ""
    if crop.shape[0] < 44:
        f = max(2, int(44 / crop.shape[0]))
        crop = cv2.resize(crop, None, fx=f, fy=f, interpolation=cv2.INTER_CUBIC)
    fd, p = tempfile.mkstemp(suffix=".png"); os.close(fd)
    cv2.imwrite(p, crop)
    try:    return " ".join(_tess(p, 7).split())
    finally: os.unlink(p)

EDGE_L = " .,|_~`^'\u2018\u2019)]}/\\"
EDGE_R = " .,|_~`^'\u2018\u2019([{\\"

def tidy_edges(v):
    """Ruling lines OCR as stray punctuation glued to the cell edge. Strip it,
    but keep inch marks, and keep brackets that actually pair up."""
    v = v.strip()
    while v and v[0] in EDGE_L:
        if v[0] in ")]}" and v.count(v[0]) > 1: break
        v = v[1:].lstrip()
    while v and v[-1] in EDGE_R:
        if v[-1] in "([{" and v.count(v[-1]) > 1: break
        v = v[:-1].rstrip()
    for o, c in (("(", ")"), ("[", "]")):
        if v.endswith(c) and o not in v: v = v[:-1].rstrip()
        if v.startswith(o) and c not in v: v = v[1:].lstrip()
    return v

def clean(v, col_profile):
    """Drop scanner speckle; snap bond-code columns to their small vocabulary."""
    v = tidy_edges(v)
    if len(v) <= 2 and not re.search(r'[0-9A-Z]', v): return ""
    if v.lower() in {"ee", "ae", "oe", "se", "ce", "aa"}: return ""
    if col_profile == "bond":
        letters = re.findall(r'[BMV]', v.upper())
        return ", ".join(dict.fromkeys(letters)) if letters else ""
    if col_profile == "frac":
        v = v.replace("V/", "1/").replace("l/", "1/").replace("I/", "1/")
        v = re.sub(r'^([0-9]+)/([0-9])([0-9])$', lambda m: f"{m.group(1)}/{m.group(2)}{m.group(3)}", v)
    return v

def profile_columns(grid):
    """Label each column so cleanup knows what it's looking at."""
    ncol = len(grid[0]) if grid else 0
    profs = []
    for c in range(ncol):
        vals = [grid[r][c] for r in range(len(grid)) if grid[r][c]]
        if not vals: profs.append("text"); continue
        bondish = sum(1 for v in vals if re.fullmatch(r'[BMV\s,.&L]{1,8}', v.upper())) / len(vals)
        fracish = sum(1 for v in vals if FRACTION.match(v)) / len(vals)
        profs.append("bond" if bondish > .6 else "frac" if fracish > .5 else "text")
    return profs

def heading_ok(txt):
    """Section titles in these manuals are set in caps. Everything else the
    glyph-height test flags is diagram labelling or scanner speckle."""
    t = txt.strip()
    alpha = [ch for ch in t if ch.isalpha()]
    if len(t) < 4 or len(alpha) < 4: return False
    if len(alpha) / len(t) < 0.55: return False
    if sum(ch.isupper() for ch in alpha) / len(alpha) < 0.6: return False
    return bool(re.search(r'[A-Z]{3}', t))

def text_ok(txt):
    t = txt.strip()
    if len(t) < 3: return False
    useful = sum(ch.isalnum() for ch in t)
    return useful >= 2 and useful / len(t) >= 0.35

# ---------- page text outside tables ----------
def page_words(png):
    """every word on the page with its box: (L, T, W, H, text)"""
    tsv = _tess(png, 6, whitelist=False, tsv=True)
    rows = list(csv.DictReader(io.StringIO(tsv), delimiter="\t", quoting=csv.QUOTE_NONE))
    out = []
    for r in rows:
        try:
            if not r.get("text") or not r["text"].strip(): continue
            if float(r.get("conf", -1)) < 40: continue
            out.append((int(r["left"]), int(r["top"]), int(r["width"]),
                        int(r["height"]), r["text"], int(r["block_num"]),
                        int(r["par_num"]), int(r["line_num"])))
        except (ValueError, TypeError, KeyError): continue
    return out

def page_lines(allwords, boxes):
    words = []
    for L, T, W, H, txt, bn, pn, ln in allwords:
        cx, cy = L + W//2, T + H//2
        if any(x1 <= cx <= x2 and y1 <= cy <= y2 for x1, y1, x2, y2 in boxes): continue
        words.append((bn, pn, ln, L, T, H, txt))
    if not words: return []
    heights = sorted(w[5] for w in words)
    med = heights[len(heights)//2] or 1
    groups = {}
    for w in words:
        groups.setdefault((w[0], w[1], w[2]), []).append(w)
    lines = [sorted(g, key=lambda w: w[3])          # words left to right
             for g in groups.values()]
    lines.sort(key=lambda g: (g[0][4], g[0][3]))     # lines top to bottom
    out = []
    for ln in lines:
        txt = " ".join(w[6] for w in ln).strip()
        if len(txt) < 2: continue
        h = sorted(w[5] for w in ln)[len(ln)//2]
        big = h >= med * 1.45 and len(txt) < 80
        if big and heading_ok(txt):
            out.append(("h", txt, ln[0][4], h, ln[0][3]))
        elif text_ok(txt):
            out.append(("p", txt, ln[0][4], h, ln[0][3]))
    # a title wrapped over two lines is one heading, not two
    merged = []
    for kind, txt, y, h, x in out:
        if (merged and kind == "h" and merged[-1][0] == "h"
                and 0 <= y - merged[-1][2] < 2.4 * max(h, merged[-1][3])
                and abs(x - merged[-1][4]) < 6 * h):
            pk, pt, py, ph, px = merged.pop()
            merged.append((pk, f"{pt} {txt}", py, max(ph, h), px))
        else:
            merged.append((kind, txt, y, h, x))
    return [(k, t, y) for k, t, y, _, _ in merged]

# ---------- figures ----------
MIN_FIG_FRAC = 0.004   # of page area
CAPTION_GAP  = 2.6     # line heights below a figure to look for its label

def find_figures(img, boxes, words, outdir, stem, page):
    """Photographs and line art are regions with heavy ink and almost no words.
    Close the halftone dots into solid blobs, then reject anything that is a
    table or is mostly covered by text."""
    H, W = img.shape[:2]
    sc = 4
    small = cv2.resize(img, (W//sc, H//sc), interpolation=cv2.INTER_AREA)
    ink = (small < 205).astype("uint8")
    ink = cv2.morphologyEx(ink, cv2.MORPH_CLOSE,
                           cv2.getStructuringElement(cv2.MORPH_RECT, (19, 19)))
    n, lab, stats, _ = cv2.connectedComponentsWithStats(ink, 8)
    figs = []
    for i in range(1, n):
        x, y, w, h, area = stats[i]
        X1, Y1, X2, Y2 = x*sc, y*sc, (x+w)*sc, (y+h)*sc
        if (w*h*sc*sc) < MIN_FIG_FRAC * W * H: continue
        if w*sc < 180 or h*sc < 180: continue
        if area / max(1, w*h) < 0.45: continue              # sparse = text column
        rw, rh = X2 - X1, Y2 - Y1
        if rw * rh > 0.35 * W * H: continue                 # half the page is not a figure
        # a side tab sits flush to the trim edge and is far taller than wide
        if rh > 2.5 * rw and (X1 < 0.06 * W or X2 > 0.94 * W): continue
        # a blob that swallowed a column of tables: measure overlap in total,
        # and never let a whole table sit inside a "figure"
        over = 0
        for bx1, by1, bx2, by2 in boxes:
            ox = min(X2, bx2) - max(X1, bx1); oy = min(Y2, by2) - max(Y1, by1)
            if ox > 0 and oy > 0: over += ox * oy
            if X1 <= (bx1+bx2)//2 <= X2 and Y1 <= (by1+by2)//2 <= Y2:
                over = rw * rh; break
        if over > 0.25 * rw * rh: continue
        wordarea = sum(ww*wh for wl, wt, ww, wh, *_ in words
                       if X1 <= wl+ww//2 <= X2 and Y1 <= wt+wh//2 <= Y2)
        if wordarea > 0.18 * (X2-X1) * (Y2-Y1): continue    # that is a text block
        figs.append([X1, Y1, X2, Y2])

    saved = []
    for j, (X1, Y1, X2, Y2) in enumerate(sorted(figs, key=lambda f: (f[1], f[0])), 1):
        m = 12
        crop = img[max(0,Y1-m):min(H,Y2+m), max(0,X1-m):min(W,X2+m)]
        if crop.size == 0: continue
        name = f"{stem}_p{page:03d}_f{j}.png"
        os.makedirs(outdir, exist_ok=True)
        cv2.imwrite(os.path.join(outdir, name), crop,
                    [cv2.IMWRITE_PNG_COMPRESSION, 6])
        saved.append((Y1, name, caption_for(words, X1, X2, Y2), X2-X1, Y2-Y1))
    return saved

def caption_for(words, X1, X2, Y2):
    """these manuals label figures in caps on the line directly beneath"""
    if not words: return ""
    hs = sorted(w[3] for w in words)
    lh = hs[len(hs)//2] or 40
    pad = max(60, (X2 - X1) // 6)
    cand = [(wt, wl, txt) for wl, wt, ww, wh, txt, *_ in words
            if X1 - pad <= wl + ww//2 <= X2 + pad and 0 < wt - Y2 < CAPTION_GAP * lh]
    if not cand: return ""
    top = min(t for t, _, _ in cand)
    line = sorted((c for c in cand if c[0] - top < lh), key=lambda c: c[1])
    txt = " ".join(t for _, _, t in line).strip()
    alpha = [c for c in txt if c.isalpha()]
    if len(alpha) < 3 or len(txt) > 70: return ""
    if sum(c.isupper() for c in alpha) / len(alpha) < 0.7: return ""
    return txt

# ---------- per page ----------
def do_page(png, ocr, figdir=None, stem="doc", page=0):
    img = cv2.imread(png, cv2.IMREAD_GRAYSCALE)
    try:
        tables = I2TImage(png, detect_rotation=False).extract_tables(
            ocr=ocr, implicit_rows=True, min_confidence=20)
    except Exception:
        tables = []
    boxes, rendered = [], []
    for t in tables:
        b = t.bbox; boxes.append((b.x1, b.y1, b.x2, b.y2))
        rows = sorted(t.content.keys())
        jobs, idx = [], []
        for r in rows:
            for c, cell in enumerate(t.content[r]):
                cb = cell.bbox
                jobs.append((img, (cb.x1, cb.y1, cb.x2, cb.y2))); idx.append((r, c))
        if not jobs: continue
        with ThreadPoolExecutor(max_workers=10) as ex:
            vals = list(ex.map(ocr_cell, jobs))
        ncol = max(c for _, c in idx) + 1
        grid = [["" for _ in range(ncol)] for _ in rows]
        rpos = {r: i for i, r in enumerate(rows)}
        for (r, c), v in zip(idx, vals): grid[rpos[r]][c] = v
        profs = profile_columns(grid)
        grid = [[clean(v, profs[c]) for c, v in enumerate(row)] for row in grid]
        if any(any(cell for cell in row) for row in grid):
            rendered.append((b.y1, grid))
    words = page_words(png)
    text = page_lines(words, boxes)
    figs = find_figures(img, boxes, words, figdir, stem, page) if figdir else []
    return rendered, text, figs
