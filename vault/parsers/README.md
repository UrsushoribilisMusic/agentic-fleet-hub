# Mexico Log Parser

This directory contains the parser for Mexico wood-marking logs.

## Parser Script

`mexico_log_parser.py` - Main parser script that processes raw log files and extracts structured events.

## Usage

```bash
python3 vault/parsers/mexico_log_parser.py
```

## Input

The parser reads log files from:
- `vault/raw_sources/robotross/mexico_wood_marking/`

## Output

Parsed events are saved as JSON files in:
- `vault/derived/mexico_events/`

## Event Schema

Each event has the following structure:

```json
{
  "timestamp": "ISO 8601 timestamp",
  "event_type": "Type of event",
  "details": ["Additional details specific to event type"],
  "source_file": "Path to source log file",
  "line_number": "Line number in source file"
}
```

## Event Types

The parser currently handles these event types:

- `PEN_DOWN`: Pen down event with line number
- `DRAWING`: Drawing progress with move count, percentage, and coordinates
- `CHECK`: System readiness checks
- `JOB_START`: Job initiation
- `BUSY`: Job in progress
- `OBS`: OBS status
- `CAFFEINATE`: System sleep prevention
- `NARRATION`: Narration status
- `WARNING_TONE`: Warning tone
- `VOICE_INTRO`: Voice introduction
- `DRAW_START`: Drawing start
- `MARKERS`: Marker status
- `ERROR`: Error messages
- `JOB_END`: Job completion

## Notes

- Some log lines may not match current patterns and will be reported as warnings
- The parser preserves provenance by including source file and line number in each event
- Derived artifacts are created outside the raw source folder as required