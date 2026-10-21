import sys, os, re, html, glob, subprocess, time, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from builddoc import do_page
from img2table.ocr import TesseractOCR

pdf, out_html, title = sys.argv[1], sys.argv[2], sys.argv[3]
first = int(sys.argv[4]) if len(sys.argv) > 4 else 1
last  = int(sys.argv[5]) if len(sys.argv) > 5 else 0

slug = re.sub(r'[^a-z0-9]+', '-', os.path.basename(pdf).lower())
work = os.path.join(os.environ.get("RENDER_CACHE",
       os.path.join(tempfile.gettempdir(), "doc-render-cache")), f"{slug}-{first}-{last}")
os.makedirs(work, exist_ok=True)
pages = sorted(glob.glob(f"{work}/p-*.png"))
if pages:
    print(f"reusing {len(pages)} cached page renders", flush=True)
else:
    rng = ["-f", str(first)] + (["-l", str(last)] if last else [])
    print(f"rendering {os.path.basename(pdf)} at 400dpi…", flush=True)
    subprocess.run(["pdftoppm", "-r", "400", "-gray", "-png", *rng, pdf, f"{work}/p"], check=True)
    pages = sorted(glob.glob(f"{work}/p-*.png"))
print(f"{len(pages)} pages", flush=True)

figdir = os.path.join(os.path.dirname(os.path.abspath(out_html)), "figuras")
stem = re.sub(r'[^a-z0-9]+', '-', os.path.splitext(os.path.basename(out_html))[0].lower())
ocr = TesseractOCR(n_threads=4, lang="eng", psm=4)
parts, ntab, nfig, lasth, t0 = [], 0, 0, "", time.time()
for i, png in enumerate(pages, start=first):
    tables, text, figs = do_page(png, ocr, figdir, stem, i)
    parts.append(f'\n<section class="pg" id="p{i}"><div class="pn">page {i}</div>')
    blocks = ([(y, "t", g) for y, g in tables]
              + [(y, k, v) for k, v, y in text]
              + [(y, "f", (nm, cap, w, h)) for y, nm, cap, w, h in figs])
    for _, kind, payload in sorted(blocks, key=lambda b: b[0]):
        if kind == "t":
            ntab += 1
            rows = payload
            parts.append('<table>')
            for r, row in enumerate(rows):
                tag = "th" if r == 0 else "td"
                cells, c = [], 0
                while c < len(row):
                    # img2table repeats a merged cell's text across the span
                    span = 1
                    while (c + span < len(row) and row[c]
                           and row[c + span] == row[c]):
                        span += 1
                    at = f' colspan="{span}"' if span > 1 else ""
                    cells.append(f"<{tag}{at}>{html.escape(row[c])}</{tag}>")
                    c += span
                parts.append("<tr>" + "".join(cells) + "</tr>")
            parts.append('</table>')
        elif kind == "f":
            nfig += 1
            nm, cap, w, h = payload
            parts.append(
                f'<figure><img src="figuras/{nm}" alt="{html.escape(cap or "figura")}" '
                f'loading="lazy">'
                + (f"<figcaption>{html.escape(cap)}</figcaption>" if cap else "")
                + "</figure>")
        elif kind == "h":
            # running heads and side tabs repeat on every page; keep the first
            norm = re.sub(r'[^a-z]', '', payload.lower())
            if norm and norm == lasth: continue
            lasth = norm
            parts.append(f"<h2>{html.escape(payload)}</h2>")
        else:
            parts.append(f"<p>{html.escape(payload)}</p>")
    parts.append("</section>")
    if i % 5 == 0 or i == first:
        el = time.time() - t0
        print(f"  page {i}/{first+len(pages)-1}  tables={ntab} figs={nfig}  {el:.0f}s "
              f"({el/max(1,i-first+1):.1f}s/pg)", flush=True)

CSS = """
:root{--ink:#16212b;--mut:#5d6b78;--line:#c9d3db;--bg:#fff;--hd:#eef3f6;--acc:#1f5c8b}
*{box-sizing:border-box}
body{font:14px/1.5 -apple-system,Segoe UI,Roboto,sans-serif;color:var(--ink);
background:var(--bg);margin:0;padding:28px 34px;max-width:1180px}
h1{font-size:26px;border-bottom:3px solid var(--acc);padding-bottom:10px;margin:0 0 6px}
.sub{color:var(--mut);margin:0 0 26px;font-size:13px}
h2{font-size:16px;color:var(--acc);margin:22px 0 8px;font-weight:700}
p{margin:6px 0;max-width:62em}
.pg{border-top:1px solid var(--line);padding-top:16px;margin-top:26px}
.pn{float:right;color:var(--mut);font-size:11px;letter-spacing:.08em;text-transform:uppercase}
table{border-collapse:collapse;margin:12px 0 18px;font-size:12.5px;page-break-inside:avoid}
th,td{border:1px solid var(--line);padding:3px 8px;text-align:left;vertical-align:top}
th{background:var(--hd);font-weight:700}
tr:nth-child(even) td{background:#fafcfd}
figure{margin:14px 0;display:inline-block;vertical-align:top;max-width:100%}
figure img{max-width:420px;width:100%;height:auto;border:1px solid var(--line);
background:#fff}
figcaption{font-size:11.5px;color:var(--mut);text-transform:uppercase;
letter-spacing:.04em;margin-top:4px;max-width:420px}
@media print{body{padding:0;max-width:none}.pg{page-break-before:auto}
 h1,h2{page-break-after:avoid}}
"""
open(out_html, "w").write(
    f"<!doctype html><html lang='en'><head><meta charset='utf-8'>"
    f"<title>{html.escape(title)}</title><style>{CSS}</style></head><body>"
    f"<h1>{html.escape(title)}</h1>"
    f"<p class='sub'>Reconstructed from scan by OCR with geometric table recovery · "
    f"{len(pages)} pages · {ntab} tables · {nfig} figures · generated {time.strftime('%Y-%m-%d')}. "
    f"Verify figures against the source scan before commercial use.</p>"
    + "".join(parts) + "</body></html>")
print(f"DONE {out_html}  pages={len(pages)} tables={ntab} figs={nfig} "
      f"elapsed={(time.time()-t0)/60:.1f}min", flush=True)
