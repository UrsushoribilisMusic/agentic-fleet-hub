"""Pull product imagery out of born-digital catalogues.

pdfimages gives every embedded image including logos, rules and background
furniture. Three filters separate product photography from page chrome:
size, aspect ratio, and repetition (anything that appears on many pages is
branding, not a product).
"""
import sys, os, re, csv, glob, hashlib, subprocess, shutil
from collections import defaultdict

MIN_PX      = 200     # smaller than this is an icon
MAX_ASPECT  = 8.0     # banners and rules
CHROME_PAGES = 4      # same image on more pages than this = furniture
PAGE_COVER  = 0.80    # covers this much of the page = flattened page scan

def page_box(pdf):
    """page size in points, to tell a product photo from a whole flattened page"""
    try:
        out = subprocess.run(["pdfinfo", pdf], capture_output=True, text=True,
                             timeout=30).stdout
        m = re.search(r'Page size:\s+([\d.]+) x ([\d.]+)', out)
        return (float(m.group(1)), float(m.group(2))) if m else None
    except Exception:
        return None

def listed(pdf):
    """pdfimages -list: page, w, h and ppi for every image, in one call"""
    try:
        out = subprocess.run(["pdfimages", "-list", pdf], capture_output=True,
                             text=True, timeout=120).stdout
    except Exception:
        return {}
    info = {}
    for ln in out.splitlines()[2:]:
        f = ln.split()
        if len(f) < 15 or not f[0].isdigit(): continue
        try:
            pg, num, w, h = int(f[0]), int(f[1]), int(f[3]), int(f[4])
            xp, yp = float(f[12]), float(f[13])
        except ValueError:
            continue
        info[(pg, num)] = (w, h, xp, yp)
    return info

def sku_index(txtdir):
    """article numbers per page, from the pdftotext extraction we already have"""
    idx = {}
    for t in glob.glob(os.path.join(txtdir, "*.txt")):
        stem = os.path.splitext(os.path.basename(t))[0]
        pages = open(t, errors="ignore").read().split("\f")
        idx[stem] = [sorted(set(re.findall(r'\b\d{2}[A-Z0-9]{4,}\b|\b[A-Z]{2,4}-?\d{3,6}\b', p)))[:12]
                     for p in pages]
    return idx

def run(pdf, outroot, skus):
    stem = os.path.splitext(os.path.basename(pdf))[0]
    slug = re.sub(r'[^a-zA-Z0-9]+', '-', stem).strip('-').lower()[:60]
    raw  = os.path.join(outroot, ".raw", slug)
    dest = os.path.join(outroot, slug)
    os.makedirs(raw, exist_ok=True); os.makedirs(dest, exist_ok=True)
    subprocess.run(["pdfimages", "-png", "-p", pdf, f"{raw}/im"],
                   check=False, capture_output=True)

    files = sorted(glob.glob(f"{raw}/im-*.png"))
    box, info = page_box(pdf), listed(pdf)
    seen = defaultdict(set); meta = {}; nfull = 0
    for f in files:
        m = re.search(r'im-(\d+)-(\d+)\.png$', f)
        if not m: continue
        page, num = int(m.group(1)), int(m.group(2))
        if (page, num) not in info: continue
        w, h, xp, yp = info[(page, num)]
        if w < MIN_PX or h < MIN_PX: continue
        if max(w, h) / max(1, min(w, h)) > MAX_ASPECT: continue
        if box and xp > 0 and yp > 0:
            # how much of the page does this image actually cover?
            if (w / xp * 72) >= PAGE_COVER * box[0] and \
               (h / yp * 72) >= PAGE_COVER * box[1]:
                nfull += 1; continue        # flattened page, not a product
        d = hashlib.md5(open(f, "rb").read()).hexdigest()
        seen[d].add(page); meta[f] = (page, w, h, d)

    rows, kept_hash = [], set()
    for f, (page, w, h, d) in sorted(meta.items(), key=lambda kv: kv[1][0]):
        if len(seen[d]) > CHROME_PAGES: continue          # logo / watermark
        if d in kept_hash: continue                        # duplicate
        kept_hash.add(d)
        name = f"{slug}_p{page:03d}_{len(kept_hash):04d}.png"
        shutil.copyfile(f, os.path.join(dest, name))
        arts = skus.get(stem, [])
        rows.append([name, stem, page, w, h,
                     " ".join(arts[page-1]) if page-1 < len(arts) else ""])
    shutil.rmtree(raw, ignore_errors=True)
    return slug, rows, len(files), nfull

if __name__ == "__main__":
    srcdir, outroot, txtdir = sys.argv[1], sys.argv[2], sys.argv[3]
    os.makedirs(outroot, exist_ok=True)
    skus = sku_index(txtdir)
    allrows = []
    for pdf in sorted(glob.glob(os.path.join(srcdir, "*.pdf"))):
        slug, rows, nraw, nfull = run(pdf, outroot, skus)
        allrows += rows
        flag = "  <- flattened page scan" if nfull and not rows else ""
        print(f"{slug:<52} raw={nraw:>5} pagescans={nfull:>4} kept={len(rows):>4}{flag}",
              flush=True)
    with open(os.path.join(outroot, "indice-imagenes.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["imagen", "catalogo", "pagina", "ancho", "alto", "articulos_en_pagina"])
        w.writerows(allrows)
    print(f"\nTOTAL kept={len(allrows)}  index -> {outroot}/indice-imagenes.csv")
