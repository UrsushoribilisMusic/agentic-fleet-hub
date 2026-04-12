#!/usr/bin/env python3
from __future__ import annotations

import html
import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Iterable

ROOT = Path("/Users/miguelrodriguez/projects/agentic-fleet-hub/ATF")
WIKI_SRC = ROOT / "artifacts" / "wiki"
LEDGER_SRC = ROOT / "artifacts" / "ledger" / "mexico_events.jsonl"
WIKI_OUT = ROOT / "wiki-ui"
LEDGER_OUT = ROOT / "ledger-ui"
LANDING_OUT = ROOT / "index.html"
ARCH_DOC = ROOT.parent / "AGENTS" / "CONTEXT" / "agentegra_atf_architecture.md"
IMAGE_DIR = ROOT / "assets" / "media" / "images"

CSS = """
:root {
  --bg: #f8f9fa;
  --paper: #ffffff;
  --paper-soft: #fdfdfd;
  --ink: #202122;
  --muted: #54595d;
  --line: #a2a9b1;
  --line-soft: #c8ccd1;
  --accent: #3366cc;
  --accent-2: #0645ad;
  --soft: #eaecf0;
  --nav: #f6f6f6;
  --note: #fff8d6;
}
* { box-sizing: border-box; }
html { scroll-behavior: smooth; }
body {
  margin: 0;
  color: var(--ink);
  background: var(--bg);
  font: 16px/1.65 Georgia, "Times New Roman", serif;
}
a { color: var(--accent-2); text-decoration: none; }
a:hover { text-decoration: underline; }
code, pre, .mono {
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
}
.topbar {
  border-bottom: 1px solid var(--line-soft);
  background: linear-gradient(180deg, #ffffff 0%, #f8f9fa 100%);
}
.topbar-inner {
  width: min(1360px, calc(100vw - 32px));
  margin: 0 auto;
  padding: 12px 0;
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: center;
  font: 13px/1.4 system-ui, sans-serif;
  color: var(--muted);
}
.topbar nav {
  display: flex;
  flex-wrap: wrap;
  gap: 14px;
}
.frame {
  width: min(1360px, calc(100vw - 32px));
  margin: 0 auto;
  display: grid;
  grid-template-columns: 220px minmax(0, 1fr);
  gap: 24px;
  padding: 20px 0 40px;
}
.frame.home {
  grid-template-columns: 1fr;
}
.sidebar {
  align-self: start;
  position: sticky;
  top: 16px;
  padding: 12px 14px;
  background: var(--nav);
  border: 1px solid var(--line-soft);
  font: 14px/1.45 system-ui, sans-serif;
}
.sidebar h3,
.sidebar h4 {
  margin: 12px 0 8px;
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: .04em;
  color: var(--muted);
}
.sidebar ul {
  margin: 0;
  padding-left: 18px;
}
.sidebar li { margin: 4px 0; }
.content {
  min-width: 0;
  background: var(--paper);
  border: 1px solid var(--line-soft);
  padding: 24px 32px 40px;
}
.content h1 {
  margin: 0 0 6px;
  font-size: 32px;
  font-weight: 400;
  line-height: 1.15;
}
.content h2 {
  margin: 1.6em 0 0.5em;
  padding-bottom: 4px;
  border-bottom: 1px solid var(--line-soft);
  font-size: 24px;
  font-weight: 400;
}
.content h3 {
  margin: 1.2em 0 0.4em;
  font-size: 19px;
  font-weight: 600;
}
.content h4,
.content h5,
.content h6 {
  margin: 1em 0 0.35em;
  font-size: 16px;
  font-weight: 600;
}
.meta {
  margin: 0 0 18px;
  color: var(--muted);
  font: 13px/1.5 system-ui, sans-serif;
}
.lede {
  font-size: 17px;
  color: #2f3133;
}
.note-box {
  margin: 18px 0;
  padding: 14px 16px;
  border: 1px solid #f1d77a;
  background: var(--note);
  font: 14px/1.6 system-ui, sans-serif;
}
.wiki-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 290px;
  gap: 24px;
}
.infobox {
  align-self: start;
  border: 1px solid var(--line-soft);
  background: #f8fbff;
  font: 14px/1.5 system-ui, sans-serif;
}
.infobox h3 {
  margin: 0;
  padding: 10px 12px;
  text-align: center;
  background: #dfe8f6;
  border-bottom: 1px solid var(--line-soft);
  font-size: 15px;
}
.infobox table {
  width: 100%;
  border-collapse: collapse;
}
.infobox th,
.infobox td {
  padding: 8px 10px;
  border-top: 1px solid var(--line-soft);
  vertical-align: top;
}
.infobox th {
  width: 36%;
  background: #f8f9fa;
  text-align: left;
  font-weight: 600;
}
.toc {
  margin: 18px 0;
  width: fit-content;
  min-width: 280px;
  max-width: 100%;
  padding: 12px 16px;
  border: 1px solid var(--line-soft);
  background: #f8f9fa;
  font: 14px/1.45 system-ui, sans-serif;
}
.toc h3 {
  margin: 0 0 8px;
  font-size: 14px;
}
.toc ol {
  margin: 0;
  padding-left: 20px;
}
.toc li { margin: 4px 0; }
.cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 16px;
  margin: 18px 0;
}
.card {
  padding: 16px;
  border: 1px solid var(--line-soft);
  background: var(--paper-soft);
}
.card h3,
.card h2 {
  margin-top: 0;
  border: 0;
  padding: 0;
}
.kpis {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 12px;
  margin: 18px 0 20px;
}
.kpi {
  padding: 14px 16px;
  border: 1px solid var(--line-soft);
  background: #fbfbfb;
}
.kpi .value {
  font: 700 20px/1.15 system-ui, sans-serif;
}
.kpi .label {
  margin-top: 4px;
  color: var(--muted);
  font: 12px/1.35 system-ui, sans-serif;
  text-transform: uppercase;
  letter-spacing: .04em;
}
.pill {
  display: inline-block;
  margin: 0 8px 8px 0;
  padding: 4px 9px;
  border: 1px solid var(--line-soft);
  background: #f8f9fa;
  font: 13px/1.3 system-ui, sans-serif;
}
.diagram {
  display: grid;
  gap: 12px;
  margin: 16px 0 24px;
}
.diagram-row {
  display: grid;
  grid-template-columns: 130px minmax(0, 260px) minmax(0, 1fr);
  gap: 14px;
  align-items: stretch;
}
.diagram-tag {
  padding: 12px;
  background: #f8f9fa;
  border: 1px solid var(--line-soft);
  font: 700 12px/1.3 system-ui, sans-serif;
  text-transform: uppercase;
  letter-spacing: .04em;
}
.diagram-box {
  padding: 12px 14px;
  border: 1px solid #98a9d0;
  background: #eef3ff;
  font: 700 15px/1.35 system-ui, sans-serif;
}
.diagram-text {
  padding: 12px 14px;
  border: 1px solid var(--line-soft);
  background: #fbfbfb;
}
table {
  width: 100%;
  border-collapse: collapse;
  margin: 14px 0 20px;
  font-size: 14px;
  table-layout: fixed;
}
th,
td {
  padding: 8px 10px;
  border: 1px solid var(--line-soft);
  vertical-align: top;
  overflow-wrap: anywhere;
  word-break: break-word;
}
th {
  background: #eaecf0;
  font: 600 13px/1.35 system-ui, sans-serif;
}
input[type="search"],
textarea {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid var(--line);
  background: #fff;
  font: 14px/1.5 system-ui, sans-serif;
}
textarea { min-height: 136px; resize: vertical; }
.compact-textarea { min-height: 56px; }
.button-row {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin: 12px 0;
}
button {
  padding: 10px 14px;
  border: 1px solid #8aa1d6;
  background: #eaf1ff;
  color: #1f3f8c;
  cursor: pointer;
  font: 600 14px/1 system-ui, sans-serif;
}
button.secondary {
  border-color: var(--line);
  background: #f8f9fa;
  color: var(--ink);
}
button[disabled] {
  cursor: not-allowed;
  opacity: .7;
}
.response-box {
  min-height: 160px;
  padding: 14px 16px;
  border: 1px solid var(--line-soft);
  background: #fbfbfb;
  white-space: pre-wrap;
}
.gallery {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 14px;
  margin: 18px 0;
}
.gallery figure {
  margin: 0;
  padding: 8px;
  border: 1px solid var(--line-soft);
  background: #fff;
}
.gallery img {
  display: block;
  width: 100%;
  height: 180px;
  object-fit: cover;
  background: #f1f3f5;
}
.gallery figcaption {
  padding: 8px 4px 2px;
  font: 12px/1.45 system-ui, sans-serif;
  color: var(--muted);
}
.search-meta {
  margin: 8px 0 0;
  color: var(--muted);
  font: 12px/1.4 system-ui, sans-serif;
}
.hero-image {
  margin: 10px 0 18px;
  border: 1px solid var(--line-soft);
  background: #fff;
}
.hero-image img {
  display: block;
  width: 100%;
  max-height: 420px;
  object-fit: cover;
}
.hero-image figcaption {
  padding: 8px 10px;
  color: var(--muted);
  font: 12px/1.45 system-ui, sans-serif;
}
.video-embed {
  margin: 16px 0 20px;
  border: 1px solid var(--line-soft);
  background: #f8f9fa;
  padding: 12px;
}
.video-embed iframe {
  display: block;
  width: 100%;
  border: 0;
}
.video-embed.vertical iframe {
  max-width: 420px;
  aspect-ratio: 9 / 16;
}
.video-embed.horizontal iframe {
  aspect-ratio: 16 / 9;
}
.footer-note {
  margin-top: 24px;
  padding-top: 10px;
  border-top: 1px solid var(--line-soft);
  color: var(--muted);
  font: 12px/1.5 system-ui, sans-serif;
}
@media (max-width: 1024px) {
  .frame { grid-template-columns: 1fr; }
  .sidebar { position: static; }
  .wiki-grid { grid-template-columns: 1fr; }
  .diagram-row { grid-template-columns: 1fr; }
}
@media (max-width: 720px) {
  .content { padding: 18px 16px 28px; }
  .topbar-inner, .frame { width: min(100vw - 20px, 1360px); }
}
"""


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def canonical_heading(text: str) -> str:
    cleaned = re.sub(r"^\d+[\.\)]\s*", "", text.strip()).lower()
    if cleaned in {"uncertainty & contradictions", "uncertainty and contradictions"}:
        prefix = re.match(r"^(\d+[\.\)]\s*)", text.strip())
        return f"{prefix.group(1) if prefix else ''}Notes and Open Points"
    return text


def replace_inline(text: str) -> str:
    text = html.escape(text)
    def _wikilink(m: re.Match) -> str:
        target = m.group(1)
        if "#" in target:
            stem, anchor = target.split("#", 1)
            slug = re.sub(r"[^a-z0-9]+", "-", anchor.strip().lower()).strip("-")
            return f'<a href="{stem.strip()}.html#{slug}">{html.escape(page_title(stem.strip()))}</a>'
        return f'<a href="{target}.html">{html.escape(page_title(target))}</a>'

    text = re.sub(r"\[\[([^\]]+)\]\]", _wikilink, text)
    text = re.sub(r"`([^`]+)`", lambda m: f"<code>{m.group(1)}</code>", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", text)
    return text


def markdown_table(lines: list[str], start: int) -> tuple[str | None, int]:
    if start + 1 >= len(lines):
        return None, start
    header = lines[start].strip()
    sep = lines[start + 1].strip()
    if "|" not in header or "|" not in sep or not re.fullmatch(r"[\|\-\:\s]+", sep):
        return None, start

    def split_row(row: str) -> list[str]:
        row = row.strip().strip("|")
        return [cell.strip() for cell in row.split("|")]

    headers = split_row(header)
    rows = []
    idx = start + 2
    while idx < len(lines):
        line = lines[idx].strip()
        if not line or "|" not in line:
            break
        rows.append(split_row(line))
        idx += 1

    out = ["<table><thead><tr>"]
    for cell in headers:
        out.append(f"<th>{replace_inline(cell)}</th>")
    out.append("</tr></thead><tbody>")
    for row in rows:
        out.append("<tr>")
        padded = row + [""] * max(0, len(headers) - len(row))
        for cell in padded[: len(headers)]:
            out.append(f"<td>{replace_inline(cell)}</td>")
        out.append("</tr>")
    out.append("</tbody></table>")
    return "".join(out), idx - 1


def markdown_to_html(md: str) -> tuple[str, list[tuple[int, str, str]]]:
    lines = md.splitlines()
    out: list[str] = []
    toc: list[tuple[int, str, str]] = []
    in_ul = False
    in_ol = False
    in_pre = False
    para: list[str] = []

    def flush_para() -> None:
        nonlocal para
        if para:
            out.append(f"<p>{replace_inline(' '.join(para))}</p>")
            para = []

    def close_lists() -> None:
        nonlocal in_ul, in_ol
        if in_ul:
            out.append("</ul>")
            in_ul = False
        if in_ol:
            out.append("</ol>")
            in_ol = False

    idx = 0
    while idx < len(lines):
        raw = lines[idx]
        line = raw.rstrip("\n")
        stripped = line.strip()

        table_html, new_idx = markdown_table(lines, idx)
        if table_html:
            flush_para()
            close_lists()
            out.append(table_html)
            idx = new_idx + 1
            continue

        if stripped.startswith("```"):
            flush_para()
            close_lists()
            if not in_pre:
                out.append("<pre><code>")
                in_pre = True
            else:
                out.append("</code></pre>")
                in_pre = False
            idx += 1
            continue
        if in_pre:
            out.append(html.escape(line))
            idx += 1
            continue
        if not stripped:
            flush_para()
            close_lists()
            idx += 1
            continue
        if stripped.startswith("---"):
            flush_para()
            close_lists()
            out.append("<hr>")
            idx += 1
            continue
        m = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if m:
            flush_para()
            close_lists()
            level = len(m.group(1))
            raw_text = canonical_heading(m.group(2))
            text = replace_inline(raw_text)
            anchor = slug(re.sub(r"<[^>]+>", "", text))
            toc.append((level, raw_text, anchor))
            out.append(f'<h{level} id="{anchor}">{text}</h{level}>')
            idx += 1
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
            idx += 1
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
            idx += 1
            continue
        para.append(stripped)
        idx += 1

    flush_para()
    close_lists()
    if in_pre:
        out.append("</code></pre>")
    return "\n".join(out), toc


def read_pages() -> list[Path]:
    return sorted([p for p in WIKI_SRC.rglob("*.md") if p.name != "manifest.md"])


def page_title(stem: str) -> str:
    mapping = {
        "Overview": "Overview",
        "Architecture": "Architecture",
        "VoiceControl": "Voice Control",
        "CommerceLayer": "Commerce Layer",
        "HardwareInterface": "Hardware Interface",
        "JobOrchestration": "Job Orchestration",
        "OrderManagement": "Order Management",
        "BiddingRules": "Bidding Rules",
        "ShopifyIntegration": "Shopify Integration",
        "VirtualsACP": "Virtuals ACP",
        "VideoProof": "Video Proof",
    }
    return mapping.get(stem, re.sub(r"(?<!^)([A-Z])", r" \1", stem))


def synthetic_pages() -> list[dict]:
    architecture_content = f"""# Architecture

## 1. Overview
RobotRoss combines customer-facing input channels, an orchestration layer, local and cloud model components, the Huenit robot arm, and studio recording/output systems. The ATF architecture page should describe that operational chain first, then show how the ATF wraps it into a live technical file.

## 2. System Flow
- **Input channels**: Shopify orders, Telegram or scripted commands, and the live voice showcase.
- **Conversation and control**: `chat_ross.py` handles interactive voice sessions, while `bob_ross.py` acts as the main orchestrator for `write`, `draw`, `svg`, `sketch`, `check`, and `calibrate`.
- **Model path**: Claude Haiku 4.5 is used for control/commerce-side reasoning, while Apertus 8B via Ollama is used for local narration and parsing tasks. Some voice/TTS flows also reference Kokoro, Voxtral, and system fallback engines depending on runtime mode.
- **Execution layer**: Huenit control scripts convert text, sketches, or SVGs into G-code streamed to the robot arm.
- **Studio output**: OBS records the drawing session, order data is written into the ledger, and customer-facing proof/output is produced from that recorded session.

## 3. RobotRoss Architecture Layers
| Layer | Component | Description |
| :--- | :--- | :--- |
| **Input** | **Shopify, Telegram, Voice Showcase** | Human prompts, uploaded designs, or spoken requests enter through commerce, messaging, or live demo channels. |
| **Control** | **`chat_ross.py` + `bob_ross.py`** | Interactive session handling and the main job orchestrator decide what the robot should do next. |
| **Models** | **Claude Haiku 4.5, Apertus 8B, Whisper, Kokoro/Voxtral** | Planning, narration, STT, and spoken output are split across purpose-specific model components. |
| **Execution** | **Huenit scripts + robot arm** | SVG conversion, drawing, calligraphy, calibration, and pyrography are executed against the physical arm. |
| **Output** | **OBS, order ledger, shipped artwork** | Sessions are recorded, logged, linked back to the customer journey, and turned into video proof and physical delivery. |

## 4. Diagram
```text
Shopify / Telegram / Voice
            |
            v
  chat_ross.py / bob_ross.py
            |
            v
 Claude Haiku / Apertus / Whisper / TTS
            |
            v
 huenit_write / huenit_draw / huenit_svg
            |
            v
      Huenit robot arm
            |
            v
   OBS / order ledger / video proof
```

## 5. ATF Overlay
The ATF is layered over the live RobotRoss system rather than replacing it:
- the **compiled wiki** explains the intended architecture and subsystem behavior
- the **operational ledger** captures what actually happened in production logs
- the **local query path** lets an operator inspect the system on the local machine
- the **voice interface** sits on top of the same evidence-backed query layer

## 6. Four-Layer ATF Surface
{architecture_diagram_markdown()}

## 7. Key Runtime Components
- **Voice showcase**: `listen.py` performs Whisper STT with VAD, `chat_ross.py` handles the conversation loop, and spoken confirmations can trigger drawing in the background.
- **Main orchestrator**: `bob_ross.py` performs readiness checks, locking, generation, narration, draw execution, and cleanup.
- **Drawing pipeline**: `huenit_write.py`, `huenit_draw.py`, `huenit_svg.py`, and sketch composition utilities convert requests into robot motion.
- **Audio/TTS**: the architecture sources mention Kokoro as the primary local neural TTS path, Voxtral for higher-end spoken output, and system-level fallback voices.
- **Studio and proof**: OBS captures the run, while the order ledger tracks received time, buyer, content, status, and produced video links.

## 8. Wall of Fame Operating Model
- The commercial target is a **10×10 Wall of Fame** with 100 slots.
- A customer buys a slot, submits a prompt or design, the system dispatches the job, RobotRoss draws it live, proof is recorded, and the physical artwork is shipped.
- This commercial journey matters for the ATF because the technical file must explain not only the robot motion, but also the customer-facing intake and proof chain.

## 9. Notes and Open Points
- The two source architecture documents describe the same system but emphasize different layers: one is voice-showcase and orchestrator centric, the other is end-to-end commerce/studio centric. The ATF page intentionally merges both views.
- TTS references are not fully aligned across the documents: one source emphasizes Kokoro plus system fallbacks, while another also calls out Voxtral. The ATF should present these as runtime variants rather than contradictory claims.
- Some model assignments are mode-specific. Claude Haiku 4.5 appears in control and commerce flows, while Apertus 8B is the local narration/default local reasoning path.
- The compiled wiki still depends on the quality and coverage of the ingested source corpus, so this page should keep being refreshed when the RobotRoss architecture docs change.
"""
    voice_content = """# Voice Control

## 1. Overview
Voice control is a top-level part of the ATF architecture, not a side note. It provides spoken interaction with the same local evidence base used by the text query path.

## 2. Speech-to-Text
- Whisper is the intended speech-to-text engine for converting operator prompts into local text queries.
- Spoken prompts should be interpreted against the compiled wiki and the operational ledger.

## 3. Reasoning Path
- The local model answers from the RobotRoss knowledge corpus and ledger evidence.
- This query path is intended to run on the local system, not through a cloud-hosted inference layer.

## 4. Text-to-Speech
- Voxtral is the intended text-to-speech engine for spoken answers.
- Spoken output should summarize the same evidence-backed answer returned in the text channel.

## 5. Notes and Open Points
- Voice interaction should remain aligned with the same provenance expectations as the text query path.
- The UI should present voice as a first-class control surface once the runtime hookup is in place.
"""
    return [
        {
            "stem": "Architecture",
            "title": "Architecture",
            "group": "Overview",
            "source": "bobrossskill/ARCHITECTURE.md + robot-ross/robot-ross-architecture.txt",
            "content": architecture_content,
        },
        {
            "stem": "VoiceControl",
            "title": "Voice Control",
            "group": "Topics",
            "source": "AGENTS/CONTEXT/agentegra_atf_architecture.md",
            "content": voice_content,
        },
    ]


def format_dt(ts: str | None) -> str:
    if not ts:
        return "n/a"
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M UTC")
    except ValueError:
        return ts


def topbar(prefix: str) -> str:
    return """
<header class="topbar">
  <div class="topbar-inner">
    <nav>
      <a href="{prefix}index.html">ATF home</a>
      <a href="{prefix}wiki-ui/index.html">Wiki</a>
      <a href="{prefix}ledger-ui/index.html">Ledger</a>
    </nav>
    <div>RobotRoss demonstrator · Agentegra ATF</div>
  </div>
</header>
""".replace("{prefix}", prefix)


def wiki_sidebar(current: str) -> str:
    groups = {"Overview": [], "Subsystems": [], "Topics": []}
    for page in read_pages():
        rel = page.relative_to(WIKI_SRC)
        if rel.parent == Path("."):
            groups["Overview"].append({"stem": page.stem, "title": page_title(page.stem)})
        else:
            groups.setdefault(rel.parent.name, []).append({"stem": page.stem, "title": page_title(page.stem)})
    for page in synthetic_pages():
        groups.setdefault(page["group"], []).append({"stem": page["stem"], "title": page["title"]})

    chunks = ['<p><a href="../index.html">ATF landing page</a></p>']
    for group, pages in groups.items():
        if not pages:
            continue
        chunks.append(f"<h3>{html.escape(group)}</h3><ul>")
        if group == "Topics":
            priority = {"Compliance": 0, "Narration": 1, "Voice Control": 2}
            key_fn = lambda item: (priority.get(item["title"], 50), item["title"])
        else:
            order = {"Overview": 0, "Architecture": 1}
            key_fn = lambda item: (order.get(item["title"], 50), item["title"])
        for p in sorted(pages, key=key_fn):
            stem = p["stem"]
            cls = ' style="font-weight:700"' if stem == current else ""
            chunks.append(f'<li><a href="{stem}.html"{cls}>{html.escape(p["title"])}</a></li>')
        chunks.append("</ul>")
    return "\n".join(chunks)


def toc_html(items: list[tuple[int, str, str]]) -> str:
    entries = [item for item in items if item[0] in {2, 3}]
    if not entries:
        return ""
    rows = "".join(
        f'<li style="margin-left:{(level - 2) * 18}px"><a href="#{anchor}">{html.escape(title)}</a></li>'
        for level, title, anchor in entries
    )
    return f'<div class="toc"><h3>Contents</h3><ol>{rows}</ol></div>'


def architecture_layers() -> list[tuple[str, str, str]]:
    return [
        ("Layer 1", "Compiled Wiki", "Structured knowledge pages distilled from docs, code, and architecture notes."),
        ("Layer 2", "Operational Ledger", "Normalized production evidence built from raw RobotRoss log streams."),
        ("Layer 3", "Local Q&A", "A local model interface for answering questions over the wiki and ledger without cloud dependency."),
        ("Layer 4", "Voice Interface", "Optional speech loop using Whisper for STT and Voxtral for spoken responses."),
    ]


def architecture_diagram_html() -> str:
    rows = []
    for tag, title, desc in architecture_layers():
        rows.append(
            f"""
<div class="diagram-row">
  <div class="diagram-tag">{html.escape(tag)}</div>
  <div class="diagram-box">{html.escape(title)}</div>
  <div class="diagram-text">{html.escape(desc)}</div>
</div>
"""
        )
    return "<div class=\"diagram\">" + "".join(rows) + "</div>"


def load_image_cards() -> str:
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    files = sorted(
        [
            p
            for p in IMAGE_DIR.iterdir()
            if p.is_file() and p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp", ".svg", ".gif"}
        ]
    )
    if not files:
        return """
<div class="note-box">
  No ATF image assets are currently present under <code>ATF/assets/media/images/</code>. Any evidence images placed there will be surfaced automatically in this landing page.
</div>
"""
    cards = []
    for image in files:
        rel = image.relative_to(ROOT).as_posix()
        cards.append(
            f"""
<figure>
  <img src="{html.escape(rel)}" alt="{html.escape(image.stem)}">
  <figcaption>{html.escape(image.name)}</figcaption>
</figure>
"""
        )
    return "<div class=\"gallery\">" + "".join(cards) + "</div>"


def render_shell(title: str, body: str, prefix: str) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)}</title>
  <style>{CSS}</style>
</head>
<body>
  {topbar(prefix)}
  {body}
</body>
</html>
"""


def page_infobox(stem: str, rel: str) -> str:
    rows = [
        ("Artifact", page_title(stem)),
        ("Type", "Compiled wiki page"),
        ("Source", rel),
        ("Surface", "Agentegra ATF"),
        ("Rendering", "Static HTML"),
    ]
    cells = "".join(f"<tr><th>{html.escape(k)}</th><td>{html.escape(v)}</td></tr>" for k, v in rows)
    return f'<aside class="infobox"><h3>Page Facts</h3><table>{cells}</table></aside>'


def architecture_diagram_markdown() -> str:
    return """| Layer | Component | Description |
| :--- | :--- | :--- |
| **Layer 1** | **Compiled Wiki** | Structured knowledge pages distilled from docs, code, and architecture notes. |
| **Layer 2** | **Operational Ledger** | Normalized production evidence built from raw RobotRoss log streams. |
| **Layer 3** | **Local Q&A** | A local model interface for answering questions over the wiki and ledger without cloud dependency. |
| **Layer 4** | **Voice Interface** | Optional speech loop using Whisper for STT and Voxtral for spoken responses. |"""


def overview_enhancements() -> str:
    return """
<section>
  <h2 id="reasoning-session">Local Reasoning Session</h2>
  <p>The ATF query layer works on the local system. Operators can search the compiled wiki and the operational ledger without shipping the evidence corpus to a cloud runtime.</p>
</section>
"""


def find_image_for_page(stem: str) -> Path | None:
    explicit = {
        "Overview": "Overview.jpeg",
        "Architecture": "IMG_1060.jpeg",
        "VoiceControl": "IMG_1302 2.jpeg",
        "CommerceLayer": "CommerceLayer.png",
        "HardwareInterface": "HardwareInterface.jpeg",
        "OrderManagement": "OrderManagement.jpeg",
    }
    if stem in explicit:
        candidate = IMAGE_DIR / explicit[stem]
        if candidate.exists():
            return candidate
    candidates = [
        IMAGE_DIR / f"{stem}.jpeg",
        IMAGE_DIR / f"{stem}.jpg",
        IMAGE_DIR / f"{stem}.png",
        IMAGE_DIR / f"{stem}.webp",
        IMAGE_DIR / f"{stem} 2.jpeg",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    title = page_title(stem).replace(" ", "")
    for image in IMAGE_DIR.iterdir():
        if image.is_file() and (slug(image.stem) == slug(stem) or slug(image.stem) == slug(title)):
            return image
    return None


def page_image_html(stem: str) -> str:
    image = find_image_for_page(stem)
    if not image:
        return ""
    rel = image.relative_to(ROOT).as_posix()
    return f"""
<figure class="hero-image">
  <img src="../{html.escape(rel)}" alt="{html.escape(page_title(stem))}">
  <figcaption>{html.escape(image.name)}</figcaption>
</figure>
"""


def page_appendix(stem: str) -> str:
    if stem == "VideoProof":
        return """
<section>
  <h2 id="demo-video">Demo Video</h2>
  <div class="video-embed horizontal">
    <iframe src="https://www.youtube.com/embed/cmXL2PpYpU4" title="RobotRoss video proof demo" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen></iframe>
  </div>
</section>
"""
    if stem == "VoiceControl":
        return """
<section>
  <h2 id="voice-demo">Voice Demo</h2>
  <div class="video-embed vertical">
    <iframe src="https://www.youtube.com/embed/rpEXI3Dk49s" title="RobotRoss voice control demo" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen></iframe>
  </div>
</section>
"""
    return ""


def build_wiki() -> None:
    WIKI_OUT.mkdir(parents=True, exist_ok=True)
    pages = read_pages()
    synthetic = synthetic_pages()
    page_cards = []

    for page in pages:
        content = page.read_text(encoding="utf-8")
        stem = page.stem
        rel = str(page.relative_to(WIKI_SRC.parent))
        page_html, toc = markdown_to_html(content)
        if stem == "Overview":
            page_html = re.sub(
                r"(<li><a href=\"Compliance\.html\">Compliance</a>: EU AI Act mapping and architectural traceability\.</li>)",
                r'\1<li><a href="VoiceControl.html">Voice Control</a>: Whisper STT, local reasoning, and Voxtral TTS.</li><li><a href="Architecture.html">Architecture</a>: ATF structure and Flotilla execution context.</li>',
                page_html,
                count=1,
            )
            page_html = overview_enhancements() + page_html
            toc = [(2, "Local Reasoning Session", "reasoning-session")] + toc
        lede = "Compiled RobotRoss knowledge page generated from RobotRoss source code, architecture notes, and operational documentation."
        body = f"""
<main class="frame">
  <aside class="sidebar">
    {wiki_sidebar(stem)}
  </aside>
  <article class="content">
    <h1>{html.escape(page_title(stem))}</h1>
    <p class="lede">{html.escape(lede)}</p>
    {toc_html(toc)}
    <div class="wiki-grid">
      <div>{page_image_html(stem)}{page_html}{page_appendix(stem)}</div>
      {page_infobox(stem, rel)}
    </div>
    <p class="footer-note">Source markdown: {html.escape(rel)} · Generated from the current on-disk ATF corpus.</p>
  </article>
</main>
"""
        (WIKI_OUT / f"{stem}.html").write_text(render_shell(stem, body, "../"), encoding="utf-8")
        page_cards.append(
            f"""
<div class="card">
  <h3><a href="{stem}.html">{html.escape(page_title(stem))}</a></h3>
  <p>{html.escape(rel)}</p>
</div>
"""
        )

    for page in synthetic:
        stem = page["stem"]
        page_html, toc = markdown_to_html(page["content"])
        body = f"""
<main class="frame">
  <aside class="sidebar">
    {wiki_sidebar(stem)}
  </aside>
  <article class="content">
    <h1>{html.escape(page['title'])}</h1>
    <p class="lede">Compiled RobotRoss knowledge page generated from RobotRoss source code, architecture notes, and operational documentation.</p>
    {toc_html(toc)}
    <div class="wiki-grid">
      <div>{page_image_html(stem)}{page_html}{page_appendix(stem)}</div>
      {page_infobox(stem, page["source"])}
    </div>
    <p class="footer-note">Source material: {html.escape(page['source'])} · Rendered into the ATF wiki surface.</p>
  </article>
</main>
"""
        (WIKI_OUT / f"{stem}.html").write_text(render_shell(page["title"], body, "../"), encoding="utf-8")

    index_body = """
<main class="frame home">
  <section class="content">
    <h1>RobotRoss Wiki</h1>
    <p class="lede">This wiki is generated from RobotRoss source code, architecture material, and operational documentation. Redirecting to the system overview.</p>
    <p><a href="Overview.html">Open Overview</a></p>
  </section>
</main>
<script>
window.location.replace("Overview.html");
</script>
"""
    (WIKI_OUT / "index.html").write_text(render_shell("RobotRoss Wiki", index_body, "../"), encoding="utf-8")


def summarize_jobs(events: Iterable[dict]) -> list[dict]:
    jobs: list[dict] = []
    current: dict | None = None
    for event in events:
        action = event.get("event_action")
        event_type = event.get("event_type")
        ts = event.get("timestamp", "")
        if event_type == "job" and action == "start":
            if current:
                jobs.append(current)
            details = event.get("details") or {}
            current = {
                "start": ts,
                "content": details.get("content") or details.get("action") or "unknown",
                "size": details.get("size"),
                "events": 1,
                "last": ts,
                "status": "in_progress",
                "highlights": [],
            }
            continue
        if current is None:
            continue
        current["events"] += 1
        current["last"] = ts or current["last"]
        if action in {"failed", "signal"} and len(current["highlights"]) < 3:
            current["highlights"].append(event.get("raw_line", ""))
            current["status"] = "attention"
        if action in {"complete", "completed", "job_end"}:
            current["status"] = "completed"
            current["end"] = ts
            jobs.append(current)
            current = None
    if current:
        jobs.append(current)
    return jobs[-8:][::-1]


def build_ledger() -> None:
    LEDGER_OUT.mkdir(parents=True, exist_ok=True)
    total = 0
    drawings = 0
    categories = Counter()
    actions = Counter()
    days = Counter()
    events: list[dict] = []
    first_ts = None
    last_ts = None

    if LEDGER_SRC.exists():
        with LEDGER_SRC.open(encoding="utf-8") as fh:
            for raw in fh:
                raw = raw.strip()
                if not raw:
                    continue
                event = json.loads(raw)
                events.append(event)
                total += 1
                ts = event.get("timestamp")
                event_type = event.get("event_type", "")
                event_action = event.get("event_action", "")
                categories[event.get("event_category", "unknown")] += 1
                actions[event_action] += 1
                if event_type == "drawing":
                    drawings += 1
                if ts:
                    day = ts[:10]
                    days[day] += 1
                    first_ts = ts if first_ts is None or ts < first_ts else first_ts
                    last_ts = ts if last_ts is None or ts > last_ts else last_ts

    jobs = summarize_jobs(events)
    kpis = [
        ("Events", total),
        ("Drawing events", drawings),
        ("Distinct categories", len(categories)),
        ("First event", format_dt(first_ts)),
        ("Last event", format_dt(last_ts)),
        ("Recent jobs", len(jobs)),
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
    by_day_rows = "".join(
        f"<tr><td>{html.escape(day)}</td><td>{count}</td></tr>"
        for day, count in sorted(days.items(), reverse=True)[:14]
    )
    job_rows = []
    for job in jobs:
        notes = " | ".join(job["highlights"]) if job["highlights"] else "No flagged exceptions in sampled events."
        content = str(job["content"]).replace("\\", "/").split("/")[-1]
        size = f'{job["size"]} mm' if job.get("size") is not None else "n/a"
        job_rows.append(
            "<tr>"
            f"<td>{html.escape(format_dt(job.get('start')))}</td>"
            f"<td>{html.escape(content)}</td>"
            f"<td>{html.escape(size)}</td>"
            f"<td>{html.escape(str(job.get('events', 0)))}</td>"
            f"<td>{html.escape(job.get('status', 'unknown'))}</td>"
            f"<td>{html.escape(notes[:180])}</td>"
            "</tr>"
        )
    search_rows = []
    for event in events[-200:][::-1]:
        raw_line = event.get("raw_line", "")
        search_rows.append(
            "<tr class=\"ledger-row\" "
            f"data-search=\"{html.escape((raw_line + ' ' + event.get('event_action', '') + ' ' + event.get('event_category', '')).lower())}\">"
            f"<td>{html.escape(format_dt(event.get('timestamp')))}</td>"
            f"<td>{html.escape(event.get('event_type', ''))}</td>"
            f"<td>{html.escape(event.get('event_category', ''))}</td>"
            f"<td>{html.escape(event.get('event_action', ''))}</td>"
            f"<td>{html.escape(raw_line[:180])}</td>"
            "</tr>"
        )

    script = """
<script>
const searchInput = document.getElementById('ledger-search');
const rows = Array.from(document.querySelectorAll('.ledger-row'));
const counter = document.getElementById('ledger-search-count');
function applySearch() {
  const term = searchInput.value.trim().toLowerCase();
  let shown = 0;
  for (const row of rows) {
    const hit = !term || row.dataset.search.includes(term);
    row.style.display = hit ? '' : 'none';
    if (hit) shown += 1;
  }
  counter.textContent = term ? `${shown} matching rows in the recent 200-event sample` : `Showing ${shown} recent ledger rows`;
}
searchInput.addEventListener('input', applySearch);
applySearch();
</script>
"""

    body = f"""
<main class="frame home">
  <section class="content">
    <div class="meta">Static evidence surface</div>
    <h1>RobotRoss Ledger Dashboard</h1>
    <p class="lede">Wikipedia-toned operational view over the normalized RobotRoss event ledger, with job summaries first and raw-row search as a secondary drill-down.</p>
    <div class="kpis">{kpi_html}</div>
    <div class="cards">
      <div class="card">
        <h3>Top categories</h3>
        <div>{top_categories or '<p>No data.</p>'}</div>
      </div>
      <div class="card">
        <h3>Top actions</h3>
        <div>{top_actions or '<p>No data.</p>'}</div>
      </div>
    </div>
    <h2>Recent jobs</h2>
    <table>
      <thead><tr><th>Started</th><th>Content</th><th>Size</th><th>Events</th><th>Status</th><th>Notes</th></tr></thead>
      <tbody>{''.join(job_rows) or '<tr><td colspan="6">No job summaries available.</td></tr>'}</tbody>
    </table>
    <div class="cards">
      <div class="card">
        <h3>Recent activity by day</h3>
        <table>
          <thead><tr><th>Day</th><th>Events</th></tr></thead>
          <tbody>{by_day_rows}</tbody>
        </table>
      </div>
      <div class="card">
        <h3>Ledger text search</h3>
        <input id="ledger-search" type="search" placeholder="Search raw log text, category, or action">
        <p id="ledger-search-count" class="search-meta"></p>
        <table>
          <thead><tr><th>Timestamp</th><th>Type</th><th>Category</th><th>Action</th><th>Raw line</th></tr></thead>
          <tbody>{''.join(search_rows)}</tbody>
        </table>
      </div>
    </div>
    <p class="footer-note">The large first/last-event hero tiles were intentionally removed to keep the emphasis on job summaries and searchable evidence rather than oversized timestamps.</p>
  </section>
</main>
{script}
"""
    (LEDGER_OUT / "index.html").write_text(render_shell("RobotRoss Ledger Dashboard", body, "../"), encoding="utf-8")


def build_landing() -> None:
    mock_examples = [
        {
            "question": "Which STT engine is RobotRoss using?",
            "answer": "RobotRoss voice input is designed around Whisper for local speech-to-text before the query is passed into the ATF reasoning layer.",
        },
        {
            "question": "Which model is doing the narration?",
            "answer": "Narration is generated by a local language model. The current corpus references Apertus 8B via Ollama for Bob Ross-style commentary.",
        },
        {
            "question": "Where do the ledger events come from?",
            "answer": "The operational ledger is derived from immutable RobotRoss production logs, starting with the Mexico wood-marking runs.",
        },
        {
            "question": "What satisfies Articles 12, 13, and 14 here?",
            "answer": "The ATF architecture itself: automatic logging, generated explainability pages, and evidence-backed human oversight through the queryable wiki and ledger.",
        },
    ]
    examples_json = json.dumps(mock_examples).replace("</", "<\\/")
    body = f"""
<main class="frame home">
  <section class="content">
    <h1>RobotRoss Automated Technical File</h1>
    <p class="lede">Every action — input received, decision made, motion executed — is logged automatically and synthesised into a live, queryable Technical File. Articles 12, 13, and 14 are satisfied by the architecture itself. No manual documentation, no after-the-fact reconstruction, easier compliance.</p>
    <div class="cards">
      <div class="card">
        <h3><a href="wiki-ui/index.html">Wiki</a></h3>
        <p>Browse generated RobotRoss pages compiled from source code, architecture notes, and operational documentation.</p>
      </div>
      <div class="card">
        <h3><a href="ledger-ui/index.html">Operational ledger</a></h3>
        <p>Inspect job summaries and search the recent raw event sample by text.</p>
      </div>
      <div class="card">
        <h3>Local reasoning path</h3>
        <p>The intended query path is local-first: wiki + ledger corpus, local model, and optional voice I/O.</p>
      </div>
    </div>
    <h2>Local Reasoning Session</h2>
    <p>This model query works on the local system. The examples below are mock text-search and answer fields that rotate across common RobotRoss questions.</p>
    <label for="local-query" class="mono">Search</label>
    <textarea id="local-query" class="compact-textarea" readonly></textarea>
    <div class="button-row">
      <button type="button" id="query-model">Query model</button>
      <button type="button" class="secondary">Talk to the model</button>
    </div>
    <label for="local-answer" class="mono">Mock answer</label>
    <div id="local-answer" class="response-box"></div>
    <h2>Architecture</h2>
    <p>The ATF architecture document is materially richer than the compact compiled overview. This page exposes that structure directly so the demo reflects the implementation contract instead of a thin landing page summary.</p>
    {architecture_diagram_html()}
    <h2>Gallery</h2>
    {load_image_cards()}
  </section>
</main>
<script>
const mockExamples = {examples_json};
let mockIndex = 0;
const queryField = document.getElementById('local-query');
const answerField = document.getElementById('local-answer');
function renderMock() {{
  const item = mockExamples[mockIndex % mockExamples.length];
  queryField.value = item.question;
  answerField.textContent = item.answer;
}}
document.getElementById('query-model').addEventListener('click', () => {{
  mockIndex = (mockIndex + 1) % mockExamples.length;
  renderMock();
}});
renderMock();
setInterval(() => {{
  mockIndex = (mockIndex + 1) % mockExamples.length;
  renderMock();
}}, 5000);
</script>
"""
    LANDING_OUT.write_text(render_shell("RobotRoss Automated Technical File", body, ""), encoding="utf-8")


def main() -> None:
    build_wiki()
    build_ledger()
    build_landing()
    print(f"Built wiki UI in {WIKI_OUT}")
    print(f"Built ledger UI in {LEDGER_OUT}")
    print(f"Built landing page at {LANDING_OUT}")


if __name__ == "__main__":
    main()
