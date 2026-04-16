#!/usr/bin/env python3
"""
ledger_to_md.py — Convert a JSONL RobotRoss run ledger to a queryable Markdown wiki page.

Conversion rules
----------------
- SKIP  event_action == "execute"  (GCODE motor commands — ~88 % of events)
- SUMMARISE drawing progress: emit milestones at 0 %, 25 %, 50 %, 75 %, 100 %
- SURFACE IN FULL: job, voice, AI, narration, OBS, error, warning events

Usage
-----
python ATF/tools/ledger_to_md.py \\
    --input  ATF/artifacts/ledger/mexico_events.jsonl \\
    --output ATF/artifacts/wiki/mexico_run_summary.md
"""

import argparse
import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timezone


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ts(raw: str) -> str:
    """Return a short human-readable UTC timestamp."""
    try:
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M UTC")
    except Exception:
        return raw


def _date(raw: str) -> str:
    return raw[:10] if raw else ""


# ---------------------------------------------------------------------------
# Event loading
# ---------------------------------------------------------------------------

def load_events(path: str) -> list:
    """Load all non-GCODE events from a JSONL ledger."""
    events = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                ev = json.loads(line)
            except json.JSONDecodeError:
                continue
            if ev.get("event_action") == "execute":
                continue  # skip GCODE
            events.append(ev)
    return events


# ---------------------------------------------------------------------------
# Job segmentation
# ---------------------------------------------------------------------------

def segment_by_job(events: list) -> list:
    """
    Split events into job segments.

    Returns a list of dicts:
      { "job_n": int, "start_ts": str, "end_ts": str,
        "status": str, "duration": str, "content": str,
        "events": [ev, ...] }

    Events that fall outside any job boundary are placed in job 0
    ("pre-run session").
    """
    segments = []
    current_job_n = 0
    current_events: list = []
    current_start: str = ""
    in_job = False

    for ev in events:
        action = ev.get("event_action", "")
        category = ev.get("event_category", "")
        ts = ev.get("timestamp", "")

        if ev.get("event_type") == "job" and action == "start":
            # Close any pre-run segment
            if not in_job and current_events:
                segments.append({
                    "job_n": 0,
                    "start_ts": current_events[0].get("timestamp", ""),
                    "end_ts": current_events[-1].get("timestamp", ""),
                    "status": "—",
                    "duration": "—",
                    "content": "—",
                    "events": current_events,
                })
                current_events = []

            in_job = True
            current_job_n += 1
            current_start = ts
            # Extract content from details
            details = ev.get("details", {})
            content = details.get("content", details.get("raw_rest", "—"))
            current_events = [ev]
            current_content = content
            current_status = "unknown"
            current_duration = "—"

        elif ev.get("event_type") == "job" and action == "end":
            current_events.append(ev)
            details = ev.get("details", {})
            current_status = details.get("status", "—")
            current_duration = details.get("raw_rest", "—")
            # Extract duration more cleanly
            dur_raw = details.get("duration_seconds")
            if dur_raw is not None:
                current_duration = f"{dur_raw}s"
            else:
                current_duration = details.get("raw_rest", "—")

            segments.append({
                "job_n": current_job_n,
                "start_ts": current_start,
                "end_ts": ts,
                "status": current_status,
                "duration": current_duration,
                "content": current_content,
                "events": current_events,
            })
            current_events = []
            in_job = False

        else:
            current_events.append(ev)

    # Trailing events after last job
    if current_events:
        if in_job:
            # Unclosed job
            segments.append({
                "job_n": current_job_n,
                "start_ts": current_start,
                "end_ts": current_events[-1].get("timestamp", ""),
                "status": "incomplete",
                "duration": "—",
                "content": current_content,
                "events": current_events,
            })
        else:
            segments.append({
                "job_n": 0,
                "start_ts": current_events[0].get("timestamp", ""),
                "end_ts": current_events[-1].get("timestamp", ""),
                "status": "—",
                "duration": "—",
                "content": "—",
                "events": current_events,
            })

    return segments


# ---------------------------------------------------------------------------
# Drawing-progress milestone tracker
# ---------------------------------------------------------------------------

MILESTONES = [0, 25, 50, 75, 100]


def drawing_milestones(events: list) -> list:
    """
    Return a list of milestone-hit strings from drawing-progress events.
    Resets on each new DRAW/start event.
    """
    milestones_hit = []
    next_milestone_idx = 0
    last_pos = {"x": None, "y": None}
    draw_name = "unknown"

    for ev in events:
        etype = ev.get("event_type", "")
        eaction = ev.get("event_action", "")
        details = ev.get("details", {})
        ts = ev.get("timestamp", "")

        if etype == "drawing" and eaction == "start":
            # New drawing — reset milestones
            next_milestone_idx = 0
            draw_name = details.get("raw_rest", "unknown").strip("→ '\"")
            milestones_hit.append(f"- `{_ts(ts)}` — **Drawing started**: {draw_name}")

        elif etype == "drawing" and eaction == "progress":
            pct = details.get("percent_complete", 0)
            x = details.get("x_mm")
            y = details.get("y_mm")
            move_cur = details.get("move_current")
            move_tot = details.get("move_total")

            while (next_milestone_idx < len(MILESTONES)
                   and pct >= MILESTONES[next_milestone_idx]):
                m = MILESTONES[next_milestone_idx]
                pos_str = ""
                if x is not None and y is not None:
                    pos_str = f" — position X:{x:+.1f} Y:{y:+.1f} mm"
                progress_str = ""
                if move_cur is not None and move_tot is not None:
                    progress_str = f" ({move_cur}/{move_tot} moves)"
                milestones_hit.append(
                    f"- `{_ts(ts)}` — **{m}% complete**{progress_str}{pos_str}"
                )
                next_milestone_idx += 1

        elif etype == "drawing" and eaction == "down":
            line_n = details.get("line_number")
            line_tot = details.get("line_total")
            if line_n is not None and line_tot is not None:
                milestones_hit.append(
                    f"- `{_ts(ts)}` — **Pen down** (line {line_n}/{line_tot})"
                )

    return milestones_hit


# ---------------------------------------------------------------------------
# Event renderers
# ---------------------------------------------------------------------------

def render_job_events(events: list) -> list:
    """Render all surface-worthy events within a job segment."""
    lines = []

    for ev in events:
        etype = ev.get("event_type", "")
        eaction = ev.get("event_action", "")
        ecategory = ev.get("event_category", "")
        ts = ev.get("timestamp", "")
        details = ev.get("details", {})
        raw_line = ev.get("raw_line", "")

        # ── Job lifecycle ──────────────────────────────────────────────────
        if etype == "job" and eaction == "start":
            content = details.get("content", "—")
            action = details.get("action", "—")
            lines.append(f"- `{_ts(ts)}` **JOB START** action=`{action}` content=`{content}`")

        elif etype == "job" and eaction == "end":
            status = details.get("status", "—")
            dur = details.get("duration_seconds")
            dur_str = f"{dur}s" if dur is not None else details.get("raw_rest", "—")
            lines.append(f"- `{_ts(ts)}` **JOB END** status=`{status}` duration={dur_str}")

        elif etype == "job" and eaction == "active":
            raw = details.get("raw_rest", "")
            lines.append(f"- `{_ts(ts)}` **BUSY** {raw}")

        # ── Drawing milestones handled separately ──────────────────────────
        elif etype == "drawing":
            pass  # handled by drawing_milestones()

        # ── AI events ─────────────────────────────────────────────────────
        elif etype == "ai" and eaction == "request":
            prompt = details.get("prompt", details.get("raw_rest", "—"))
            lines.append(f"- `{_ts(ts)}` **AI SKETCH REQUEST** prompt=`{prompt}`")

        elif etype == "ai" and eaction == "preview":
            raw = details.get("raw_rest", "")
            lines.append(f"- `{_ts(ts)}` **AI SKETCH PREVIEW** {raw}")

        elif etype == "ai" and eaction == "confirm":
            raw = details.get("raw_rest", "")
            lines.append(f"- `{_ts(ts)}` **AI SKETCH APPROVED** {raw}")

        elif etype == "ai" and eaction == "usage":
            inp = details.get("input_tokens", "?")
            out = details.get("output_tokens", "?")
            tot = details.get("total_tokens", "?")
            lines.append(
                f"- `{_ts(ts)}` **AI TOKEN USAGE** input={inp} output={out} total={tot}"
            )

        # ── Voice / Narration ──────────────────────────────────────────────
        elif etype == "voice":
            raw = details.get("raw_rest", "") or details.get("status", "")
            if ecategory == "NARRATION":
                lines.append(f"- `{_ts(ts)}` **NARRATION** {raw}")
            elif ecategory == "VOICE" and eaction == "intro":
                lines.append(f"- `{_ts(ts)}` **VOICE INTRO** {raw}")
            elif ecategory == "VOICE" and eaction == "outro":
                lines.append(f"- `{_ts(ts)}` **VOICE OUTRO** {raw}")
            elif ecategory == "WARNING":
                lines.append(f"- `{_ts(ts)}` **VOICE WARNING** {raw}")
            else:
                lines.append(f"- `{_ts(ts)}` **VOICE** [{ecategory}/{eaction}] {raw}")

        # ── System ────────────────────────────────────────────────────────
        elif etype == "system":
            raw = details.get("raw_rest", "") or details.get("status", "")
            if ecategory == "OBS":
                lines.append(f"- `{_ts(ts)}` **OBS** {raw}")
            elif ecategory == "STOP":
                lines.append(f"- `{_ts(ts)}` **STOP SIGNAL** {raw}")
            elif ecategory == "DRY":
                lines.append(f"- `{_ts(ts)}` **DRY RUN MODE** {raw}")
            else:
                lines.append(f"- `{_ts(ts)}` **SYS [{ecategory}]** {raw}")

        # ── Errors ────────────────────────────────────────────────────────
        elif etype == "error":
            raw = details.get("raw_rest", "") or details.get("status", "")
            lines.append(f"- `{_ts(ts)}` **ERROR [{ecategory}]** {raw}")

        # ── Unknown ───────────────────────────────────────────────────────
        elif etype == "unknown":
            lines.append(f"- `{_ts(ts)}` **UNKNOWN** {raw_line[:120]}")

    return lines


# ---------------------------------------------------------------------------
# Statistics helpers
# ---------------------------------------------------------------------------

def run_stats(events: list) -> dict:
    """Compute high-level stats over all (non-GCODE) events."""
    stats: dict = defaultdict(int)
    ai_tokens_total = 0
    ai_requests = 0
    error_categories: list = []

    for ev in events:
        etype = ev.get("event_type", "")
        eaction = ev.get("event_action", "")
        details = ev.get("details", {})

        stats[etype] += 1

        if etype == "ai" and eaction == "usage":
            ai_tokens_total += details.get("total_tokens", 0)
            ai_requests += 1
        elif etype == "ai" and eaction == "request":
            ai_requests += 1
        elif etype == "error":
            error_categories.append(ev.get("event_category", "ERROR"))

    return {
        "total_events": len(events),
        "by_type": dict(stats),
        "ai_requests": ai_requests,
        "ai_tokens_total": ai_tokens_total,
        "errors": error_categories,
    }


# ---------------------------------------------------------------------------
# Markdown assembly
# ---------------------------------------------------------------------------

def build_markdown(events: list, run_name: str) -> str:
    """Assemble the full Markdown document from the event list."""
    sections: list[str] = []

    if not events:
        return f"# {run_name}\n\n*No events found.*\n"

    all_dates = sorted(set(ev.get("timestamp", "")[:10] for ev in events if ev.get("timestamp")))
    date_range = f"{all_dates[0]} to {all_dates[-1]}" if all_dates else "unknown"

    # ── Title & overview ────────────────────────────────────────────────────
    sections.append(f"# {run_name} — {date_range}")
    sections.append("")

    stats = run_stats(events)
    sections.append("## Run Overview")
    sections.append("")
    sections.append(f"| Field | Value |")
    sections.append(f"|---|---|")
    sections.append(f"| Date range | {date_range} |")
    sections.append(f"| Days active | {', '.join(all_dates)} |")
    sections.append(f"| Total events (non-GCODE) | {stats['total_events']} |")
    for etype, count in sorted(stats["by_type"].items()):
        sections.append(f"| Events: {etype} | {count} |")
    sections.append(f"| AI sketch requests | {stats['ai_requests']} |")
    sections.append(f"| AI tokens (total) | {stats['ai_tokens_total']} |")
    sections.append(f"| Errors | {len(stats['errors'])} |")
    sections.append("")

    # ── Jobs ────────────────────────────────────────────────────────────────
    segments = segment_by_job(events)
    job_segments = [s for s in segments if s["job_n"] > 0]
    pre_segments = [s for s in segments if s["job_n"] == 0]

    sections.append("## Jobs")
    sections.append("")
    sections.append(
        f"Total jobs: **{len(job_segments)}** across "
        f"{len(all_dates)} days ({date_range})."
    )
    sections.append("")

    for seg in segments:
        job_n = seg["job_n"]
        if job_n == 0:
            label = "Pre-run / Session Init"
        else:
            label = f"Job {job_n}"
        start_str = _ts(seg["start_ts"])
        end_str = _ts(seg["end_ts"])

        sections.append(f"### {label} — {start_str}")
        sections.append("")
        if job_n > 0:
            sections.append(f"| Field | Value |")
            sections.append(f"|---|---|")
            sections.append(f"| Content | `{seg['content']}` |")
            sections.append(f"| Status | `{seg['status']}` |")
            sections.append(f"| Duration | {seg['duration']} |")
            sections.append(f"| End | {end_str} |")
            sections.append("")

        # Drawing milestones
        draw_lines = drawing_milestones(seg["events"])
        if draw_lines:
            sections.append("#### Drawing Progress")
            sections.append("")
            sections.extend(draw_lines)
            sections.append("")

        # Other events
        ev_lines = render_job_events(seg["events"])
        if ev_lines:
            sections.append("#### Events")
            sections.append("")
            sections.extend(ev_lines)
            sections.append("")

    # ── AI Interactions (global summary) ────────────────────────────────────
    sections.append("## AI Interactions")
    sections.append("")
    ai_events = [ev for ev in events if ev.get("event_type") == "ai"]
    if ai_events:
        for ev in ai_events:
            eaction = ev.get("event_action", "")
            ecategory = ev.get("event_category", "")
            ts = ev.get("timestamp", "")
            details = ev.get("details", {})

            if eaction == "request":
                prompt = details.get("prompt", details.get("raw_rest", "—"))
                sections.append(f"- `{_ts(ts)}` **SKETCH REQUEST** prompt=`{prompt}`")
            elif eaction == "preview":
                raw = details.get("raw_rest", "")
                sections.append(f"- `{_ts(ts)}` **SKETCH PREVIEW** {raw}")
            elif eaction == "confirm":
                raw = details.get("raw_rest", "")
                sections.append(f"- `{_ts(ts)}` **SKETCH APPROVED** {raw}")
            elif eaction == "usage":
                inp = details.get("input_tokens", "?")
                out = details.get("output_tokens", "?")
                tot = details.get("total_tokens", "?")
                sections.append(
                    f"- `{_ts(ts)}` **TOKEN USAGE** in={inp} out={out} total={tot}"
                )
    else:
        sections.append("*No AI events recorded.*")
    sections.append("")

    # ── Voice Events (global summary) ────────────────────────────────────────
    sections.append("## Voice Events")
    sections.append("")
    voice_events = [ev for ev in events if ev.get("event_type") == "voice"]
    if voice_events:
        for ev in voice_events:
            ecategory = ev.get("event_category", "")
            eaction = ev.get("event_action", "")
            ts = ev.get("timestamp", "")
            details = ev.get("details", {})
            raw = details.get("raw_rest", "") or details.get("status", "")
            sections.append(f"- `{_ts(ts)}` **{ecategory}/{eaction}** {raw}")
    else:
        sections.append("*No voice events recorded.*")
    sections.append("")

    # ── Errors & Warnings ───────────────────────────────────────────────────
    sections.append("## Errors & Warnings")
    sections.append("")
    error_events = [
        ev for ev in events
        if ev.get("event_type") == "error"
        or (ev.get("event_type") == "voice" and ev.get("event_category") == "WARNING")
    ]
    if error_events:
        for ev in error_events:
            etype = ev.get("event_type", "")
            ecategory = ev.get("event_category", "")
            ts = ev.get("timestamp", "")
            details = ev.get("details", {})
            raw = details.get("raw_rest", "") or details.get("status", "")
            sections.append(
                f"- `{_ts(ts)}` **[{etype.upper()}/{ecategory}]** {raw[:200]}"
            )
    else:
        sections.append("*No errors or warnings recorded.*")
    sections.append("")

    sections.append(
        f"*Generated by `ledger_to_md.py` — {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}*"
    )

    return "\n".join(sections) + "\n"


# ---------------------------------------------------------------------------
# CLI entrypoint
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Convert a JSONL RobotRoss run ledger to a queryable wiki Markdown file."
    )
    parser.add_argument(
        "--input", "-i",
        required=True,
        help="Path to the JSONL ledger file (e.g. ATF/artifacts/ledger/mexico_events.jsonl)",
    )
    parser.add_argument(
        "--output", "-o",
        required=True,
        help="Path for the output Markdown file (e.g. ATF/artifacts/wiki/mexico_run_summary.md)",
    )
    parser.add_argument(
        "--run-name",
        default=None,
        help="Display name for this run (default: derived from input filename)",
    )
    args = parser.parse_args()

    input_path = args.input
    output_path = args.output

    if not os.path.isfile(input_path):
        print(f"ERROR: input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    run_name = args.run_name
    if not run_name:
        base = os.path.splitext(os.path.basename(input_path))[0]
        run_name = base.replace("_", " ").replace("-", " ").title() + " — Robot Ross Run"

    print(f"Loading events from {input_path} …", file=sys.stderr)
    events = load_events(input_path)
    print(f"Loaded {len(events)} events (GCODE skipped)", file=sys.stderr)

    print(f"Building Markdown …", file=sys.stderr)
    md = build_markdown(events, run_name)

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as fh:
        fh.write(md)

    print(f"Written → {output_path}  ({len(md.splitlines())} lines)", file=sys.stderr)


if __name__ == "__main__":
    main()
