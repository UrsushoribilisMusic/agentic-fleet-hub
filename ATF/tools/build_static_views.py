#!/usr/bin/env python3
from __future__ import annotations

import html
import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path

ROOT = Path("/Users/miguelrodriguez/projects/agentic-fleet-hub/ATF")
WIKI_SRC = ROOT / "artifacts" / "wiki"
LEDGER_SRC = ROOT / "artifacts" / "ledger" / "mexico_events.jsonl"
WIKI_OUT = ROOT / "wiki-ui"
LEDGER_OUT = ROOT / "ledger-ui"
LANDING_OUT = ROOT / "index.html"

CSS = """
:root {
  --bg: #f5f1e8;
  --paper: #fffdfa;
  --ink: #1f2a2e;
  --muted: #6b7476;
  --line: #d6d0c6;
  --accent: #b54d2f;
  --accent-2: #2f6a73;
  --soft: #ede6da;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  font-family: Georgia, "Times New Roman", serif;
  color: var(--ink);
  background:
    radial-gradient(circle at top right, rgba(181,77,47,0.10), transparent 28%),
    linear-gradient(180deg, #f8f4ec 0%, #f1ece2 100%);
}
a { color: var(--accent-2); text-decoration: none; }
a:hover { text-decoration: underline; }
.shell {
  width: min(1180px, calc(100vw - 48px));
  margin: 24px auto 48px;
}
.hero {
  background: var(--paper);
  border: 1px solid var(--line);
  border-radius: 18px;
  padding: 28px 30px;
  box-shadow: 0 14px 36px rgba(31,42,46,0.08);
}
.eyebrow {
  margin: 0 0 8px;
  color: var(--accent);
  letter-spacing: .08em;
  text-transform: uppercase;
  font: 700 12px/1.2 system-ui, sans-serif;
}
h1 {
  margin: 0 0 12px;
  font-size: clamp(34px, 5vw, 56px);
  line-height: 1.02;
}
.lede {
  margin: 0;
  max-width: 72ch;
  color: var(--muted);
  font-size: 18px;
  line-height: 1.6;
}
.grid {
  display: grid;
  gap: 18px;
  margin-top: 22px;
}
.grid.cards { grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); }
.card {
  background: var(--paper);
  border: 1px solid var(--line);
  border-radius: 16px;
  padding: 20px;
  box-shadow: 0 10px 28px rgba(31,42,46,0.05);
}
.card h2, .card h3 { margin-top: 0; }
.nav {
  display: grid;
  grid-template-columns: 280px minmax(0, 1fr);
  gap: 20px;
  margin-top: 20px;
}
.sidebar {
  background: rgba(255,253,250,0.82);
  border: 1px solid var(--line);
  border-radius: 16px;
  padding: 18px;
  position: sticky;
  top: 18px;
  height: fit-content;
}
.sidebar h3 {
  margin: 0 0 12px;
  font: 700 14px/1.2 system-ui, sans-serif;
  letter-spacing: .06em;
  text-transform: uppercase;
  color: var(--muted);
}
.sidebar ul {
  list-style: none;
  margin: 0;
  padding: 0;
}
.sidebar li + li { margin-top: 8px; }
.article {
  background: var(--paper);
  border: 1px solid var(--line);
  border-radius: 16px;
  padding: 28px 34px;
  box-shadow: 0 12px 30px rgba(31,42,46,0.06);
}
.article h1, .article h2, .article h3 { line-height: 1.15; }
.article p, .article li {
  font-size: 17px;
  line-height: 1.7;
}
.article ul, .article ol { padding-left: 22px; }
.article pre {
  overflow-x: auto;
  background: #f1ece2;
  border: 1px solid var(--line);
  border-radius: 12px;
  padding: 14px;
}
.article code {
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  background: #f1ece2;
  border-radius: 4px;
  padding: 0 4px;
}
.kpis {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
  gap: 14px;
  margin-top: 18px;
}
.kpi {
  background: linear-gradient(180deg, #fffdfa 0%, #f4ede1 100%);
  border: 1px solid var(--line);
  border-radius: 14px;
  padding: 16px;
}
.kpi .value {
  font-size: 30px;
  font-weight: 700;
}
.kpi .label {
  color: var(--muted);
  font: 600 12px/1.3 system-ui, sans-serif;
  letter-spacing: .05em;
  text-transform: uppercase;
}
table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 16px;
}
th, td {
  border-bottom: 1px solid var(--line);
  padding: 10px 8px;
  text-align: left;
  vertical-align: top;
  font-size: 15px;
}
th {
  color: var(--muted);
  font: 700 12px/1.2 system-ui, sans-serif;
  letter-spacing: .05em;
  text-transform: uppercase;
}
.pill {
  display: inline-block;
  background: var(--soft);
  border: 1px solid var(--line);
  border-radius: 999px;
  padding: 5px 10px;
  margin: 0 8px 8px 0;
  font: 600 13px/1.1 system-ui, sans-serif;
}
@media (max-width: 900px) {
  .nav { grid-template-columns: 1fr; }
  .sidebar { position: static; }
  .shell { width: min(100vw - 24px, 1180px); }
  .article { padding: 22px 20px; }
}
"""


def slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def page_title(path: Path) -> str:
    return path.stem


def replace_inline(text: str) -> str:
    text = html.escape(text)
    text = re.sub(r"\[\[([^\]]+)\]\]", lambda m: f'<a href="{m.group(1)}.html">{html.escape(m.group(1))}</a>', text)
    text = re.sub(r"`([^`]+)`", lambda m: f"<code>{m.group(1)}</code>", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", text)
    return text


def markdown_to_html(md: str) -> str:
    lines = md.splitlines()
    out: list[str] = []
    in_ul = False
    in_ol = False
    in_pre = False
    para: list[str] = []

    def flush_para():
        nonlocal para
        if para:
            out.append(f"<p>{replace_inline(' '.join(para))}</p>")
            para = []

    def close_lists():
        nonlocal in_ul, in_ol
        if in_ul:
            out.append("</ul>")
            in_ul = False
        if in_ol:
            out.append("</ol>")
            in_ol = False

    for raw in lines:
        line = raw.rstrip("\n")
        stripped = line.strip()
        if stripped.startswith("```"):
            flush_para()
            close_lists()
            if not in_pre:
                out.append("<pre><code>")
                in_pre = True
            else:
                out.append("</code></pre>")
                in_pre = False
            continue
        if in_pre:
            out.append(html.escape(line))
            continue
        if not stripped:
            flush_para()
            close_lists()
            continue
        if stripped.startswith("---"):
            flush_para()
            close_lists()
            out.append("<hr>")
            continue
        m = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if m:
            flush_para()
            close_lists()
            level = len(m.group(1))
            text = replace_inline(m.group(2))
            anchor = slug(re.sub(r"<[^>]+>", "", text))
            out.append(f'<h{level} id="{anchor}">{text}</h{level}>')
            continue
        m = re.match(r"^\d+\.\s+(.*)$", stripped)
        if m:
            flush_para()
            if in_ul:
                out.append("</ul>")
                in_ul = False
            if not in_ol:
                out.append("<ol>")
                in_ol = True
            out.append(f"<li>{replace_inline(m.group(1))}</li>")
            continue
        if stripped.startswith("- "):
            flush_para()
            if in_ol:
                out.append("</ol>")
                in_ol = False
            if not in_ul:
                out.append("<ul>")
                in_ul = True
            out.append(f"<li>{replace_inline(stripped[2:])}</li>")
            continue
        para.append(stripped)

    flush_para()
    close_lists()
    if in_pre:
        out.append("</code></pre>")
    return "\n".join(out)


def read_pages() -> list[Path]:
    return sorted([p for p in WIKI_SRC.rglob("*.md") if p.name != "manifest.md"])


def wiki_sidebar(current: str) -> str:
    groups = {"Overview": [], "Subsystems": [], "Topics": []}
    for page in read_pages():
        rel = page.relative_to(WIKI_SRC)
        if rel.parent == Path("."):
            groups["Overview"].append(page)
        else:
            groups.setdefault(rel.parent.name, []).append(page)

    chunks = []
    for group, pages in groups.items():
        if not pages:
            continue
        chunks.append(f"<h3>{html.escape(group)}</h3><ul>")
        for p in pages:
            stem = p.stem
            cls = ' style="font-weight:700"' if stem == current else ""
            chunks.append(f'<li><a href="{stem}.html"{cls}>{html.escape(stem)}</a></li>')
        chunks.append("</ul>")
    return "\n".join(chunks)


def render_shell(title: str, body: str) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)}</title>
  <style>{CSS}</style>
</head>
<body>
  {body}
</body>
</html>
"""


def build_wiki() -> None:
    WIKI_OUT.mkdir(parents=True, exist_ok=True)
    pages = read_pages()
    for page in pages:
        content = page.read_text(encoding="utf-8")
        stem = page.stem
        body = f"""
<div class="shell">
  <div class="hero">
    <p class="eyebrow">Agentegra ATF</p>
    <h1>{html.escape(stem)}</h1>
    <p class="lede">Compiled RobotRoss knowledge pages rendered from the current ATF markdown corpus.</p>
  </div>
  <div class="nav">
    <aside class="sidebar">
      <p><a href="../index.html">ATF home</a></p>
      {wiki_sidebar(stem)}
    </aside>
    <article class="article">
      {markdown_to_html(content)}
    </article>
  </div>
</div>
"""
        (WIKI_OUT / f"{stem}.html").write_text(render_shell(stem, body), encoding="utf-8")

    links = "".join(
        f'<div class="card"><h3><a href="{p.stem}.html">{html.escape(p.stem)}</a></h3><p>{html.escape(str(p.relative_to(WIKI_SRC.parent)))} </p></div>'
        for p in pages
    )
    index_body = f"""
<div class="shell">
  <div class="hero">
    <p class="eyebrow">Agentegra ATF</p>
    <h1>RobotRoss Wiki</h1>
    <p class="lede">Browser-readable entry into the current ATF wiki corpus. This build is generated from markdown artifacts already present in the repository.</p>
  </div>
  <div class="grid cards">
    {links}
  </div>
</div>
"""
    (WIKI_OUT / "index.html").write_text(render_shell("RobotRoss Wiki", index_body), encoding="utf-8")


def build_ledger() -> None:
    LEDGER_OUT.mkdir(parents=True, exist_ok=True)
    total = 0
    drawings = 0
    job_end = 0
    categories = Counter()
    actions = Counter()
    days = Counter()
    recent = []
    first_ts = None
    last_ts = None

    if LEDGER_SRC.exists():
        with LEDGER_SRC.open(encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                total += 1
                event = json.loads(line)
                ts = event.get("timestamp", "")
                event_type = event.get("event_type", "")
                event_action = event.get("event_action", "")
                categories[event.get("event_category", "unknown")] += 1
                actions[event_action] += 1
                if event_type == "drawing":
                    drawings += 1
                if event_action in {"job_end", "complete", "completed"}:
                    job_end += 1
                if ts:
                    day = ts[:10]
                    days[day] += 1
                    first_ts = ts if first_ts is None or ts < first_ts else first_ts
                    last_ts = ts if last_ts is None or ts > last_ts else last_ts
                if len(recent) < 25:
                    recent.append(event)

    kpis = [
        ("Events", total),
        ("Drawing events", drawings),
        ("Job-end events", job_end),
        ("Distinct categories", len(categories)),
        ("First event", first_ts or "n/a"),
        ("Last event", last_ts or "n/a"),
    ]
    kpi_html = "".join(
        f'<div class="kpi"><div class="value">{html.escape(str(v))}</div><div class="label">{html.escape(k)}</div></div>'
        for k, v in kpis
    )
    top_categories = "".join(
        f'<span class="pill">{html.escape(name)}: {count}</span>'
        for name, count in categories.most_common(12)
    )
    top_actions = "".join(
        f'<span class="pill">{html.escape(name)}: {count}</span>'
        for name, count in actions.most_common(12)
    )
    recent_rows = "".join(
        "<tr>"
        f"<td>{html.escape(e.get('timestamp',''))}</td>"
        f"<td>{html.escape(e.get('event_type',''))}</td>"
        f"<td>{html.escape(e.get('event_category',''))}</td>"
        f"<td>{html.escape(e.get('event_action',''))}</td>"
        f"<td>{html.escape(str(e.get('line_number','')))}</td>"
        "</tr>"
        for e in recent[:12]
    )
    by_day_rows = "".join(
        f"<tr><td>{html.escape(day)}</td><td>{count}</td></tr>"
        for day, count in sorted(days.items(), reverse=True)[:14]
    )
    body = f"""
<div class="shell">
  <div class="hero">
    <p class="eyebrow">Agentegra ATF</p>
    <h1>RobotRoss Ledger Dashboard</h1>
    <p class="lede">Human-readable overview of the current operational ledger extracted from the RobotRoss event log corpus.</p>
  </div>
  <div class="kpis">{kpi_html}</div>
  <div class="grid cards">
    <div class="card">
      <h2>Top categories</h2>
      <div>{top_categories or '<p>No data.</p>'}</div>
    </div>
    <div class="card">
      <h2>Top actions</h2>
      <div>{top_actions or '<p>No data.</p>'}</div>
    </div>
  </div>
  <div class="grid cards">
    <div class="card">
      <h2>Recent activity by day</h2>
      <table>
        <thead><tr><th>Day</th><th>Events</th></tr></thead>
        <tbody>{by_day_rows}</tbody>
      </table>
    </div>
    <div class="card">
      <h2>Recent ledger rows</h2>
      <table>
        <thead><tr><th>Timestamp</th><th>Type</th><th>Category</th><th>Action</th><th>Line</th></tr></thead>
        <tbody>{recent_rows}</tbody>
      </table>
    </div>
  </div>
</div>
"""
    (LEDGER_OUT / "index.html").write_text(render_shell("RobotRoss Ledger Dashboard", body), encoding="utf-8")


def build_landing() -> None:
    body = """
<div class="shell">
  <div class="hero">
    <p class="eyebrow">Agentegra ATF</p>
    <h1>RobotRoss Knowledge Surface</h1>
    <p class="lede">Single entry point for the current compiled wiki, the operational ledger dashboard, and the local QA tools. This build reflects the current on-disk corpus and can be regenerated after the repo merge and re-ingestion work.</p>
  </div>
  <div class="grid cards">
    <div class="card">
      <h2><a href="wiki-ui/index.html">Browse the wiki</a></h2>
      <p>Read the current compiled RobotRoss knowledge pages in a browser.</p>
    </div>
    <div class="card">
      <h2><a href="ledger-ui/index.html">Open the ledger dashboard</a></h2>
      <p>Inspect the current event corpus with totals, categories, and sample rows.</p>
    </div>
    <div class="card">
      <h2>Ask the local model</h2>
      <p>Run <code>python3 ATF/tools/atf_qa.py --shell</code> from the repo root for text QA over the corpus.</p>
    </div>
    <div class="card">
      <h2>Optional voice layer</h2>
      <p>The voice shell is still pending canonical re-ingestion. Keep it behind the local deployment path only.</p>
    </div>
  </div>
</div>
"""
    LANDING_OUT.write_text(render_shell("RobotRoss Knowledge Surface", body), encoding="utf-8")


def main() -> None:
    build_wiki()
    build_ledger()
    build_landing()
    print(f"Built wiki UI in {WIKI_OUT}")
    print(f"Built ledger UI in {LEDGER_OUT}")
    print(f"Built landing page at {LANDING_OUT}")


if __name__ == "__main__":
    main()
