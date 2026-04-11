# Mexico Log Parser

Parser for RobotRoss Mexico wood-marking logs. Converts raw log files into normalized JSONL event streams.

## Input Format

The Mexico logs follow this structure:
```
[timestamp] EVENT_KEY details
```

Example lines:
```
[2026-03-19 12:44:47] PEN DOWN — drawing line 1/2628
[2026-03-19 12:44:56] DRAWING  — 50/2628 moves (2%) — X:+3.9 Y:+16.7mm
[2026-03-19 15:41:39] JOB START — action=svg content='Logo Bird in House for Casa Cucu.svg'
[2026-03-19 15:58:02] JOB END — status=failed duration=0.2s
```

## Normalized Event Schema

Each parsed event contains:

### Core Fields
- `event_id`: Unique MD5-based identifier (source_file:line_number:timestamp)
- `timestamp`: ISO 8601 timestamp with Z suffix
- `timestamp_epoch`: Unix epoch (float)
- `event_type`: High-level classification (drawing, job, motion, system, voice, ai, error, unknown)
- `event_category`: Event source/category (PEN, DRAWING, JOB, GCODE, etc.)
- `event_action`: Specific action (start, end, down, up, progress, execute, etc.)

### Provenance
- `source_file`: Path to the source log file
- `line_number`: Line number in the source file
- `raw_line`: Original log line (preserved exactly)

### Event Details
- `details`: Dict containing event-specific extracted fields
  - Varies by event type
  - Always includes `event_key_raw` and `raw_rest`
- `parsed_at`: When the event was parsed (ISO 8601)
- `parser_version`: Version of the parser that created this event

## Event Type Mappings

| Event Key | Type | Category | Action |
|-----------|------|----------|--------|
| JOB START | job | JOB | start |
| JOB END | job | JOB | end |
| PEN DOWN | drawing | PEN | down |
| PEN UP | drawing | PEN | up |
| DRAWING | drawing | DRAWING | progress |
| DRAW START | drawing | DRAW | start |
| DRAW END | drawing | DRAW | end |
| GCODE | motion | GCODE | execute |
| NARRATION | voice | NARRATION | status |
| VOICE INTRO | voice | VOICE | intro |
| VOICE OUTRO | voice | VOICE | outro |
| WARNING TONE | voice | WARNING | play |
| CHECK | system | CHECK | status |
| PORT | system | PORT | status |
| OBS | system | OBS | status |
| CAFFEINATE | system | CAFFEINATE | status |
| AI TOKENS | ai | AI | usage |
| SKETCH | ai | SKETCH | request |
| SKETCH PREVIEW | ai | SKETCH | preview |
| APPROVE | ai | APPROVE | confirm |
| ERROR | error | ERROR | occurred |
| MARKERS ERROR | error | MARKERS | failed |

## Extracted Details by Event Type

### JOB START
- `action`: The job action type (e.g., "svg")
- `content`: The content/filename being processed
- `size`: Optional size parameter

### JOB END
- `status`: Job completion status (success/failed)
- `duration_seconds`: Duration in seconds (float)

### DRAWING (progress)
- `move_current`: Current move number
- `move_total`: Total moves in sequence
- `percent_complete`: Percentage complete (0-100, float)
- `x_mm`: X coordinate in millimeters (float)
- `y_mm`: Y coordinate in millimeters (float)

### PEN DOWN/UP
- `line_number`: Current line number
- `line_total`: Total lines expected

### AI TOKENS
- `input_tokens`: Input tokens consumed
- `output_tokens`: Output tokens generated
- `total_tokens`: Total tokens for the operation

### SKETCH
- `prompt`: The sketch prompt text

### Voice Events (NARRATION, VOICE INTRO, VOICE OUTRO, WARNING TONE)
- `message`: The voice message text

### System Events (CHECK, PORT, OBS, CAFFEINATE, ERROR)
- `status`: Status message

## Usage

```bash
# Parse a single file
python mexico_log_parser.py vault/raw_sources/robotross/mexico_wood_marking/bob_ross.log \
    --output /path/to/output.jsonl

# Parse a directory of logs
python mexico_log_parser.py --directory vault/raw_sources/robotross/mexico_wood_marking/ \
    --output /path/to/output.jsonl

# With statistics
python mexico_log_parser.py vault/raw_sources/robotross/mexico_wood_marking/bob_ross.log \
    --output /path/to/output.jsonl --stats

# Test mode (show first 5 events)
python mexico_log_parser.py vault/raw_sources/robotross/mexico_wood_marking/bob_ross.log --test
```

## Output Formats

### JSONL (Default)
Newline-delimited JSON, one event per line:
```json
{"event_id": "...", "timestamp": "...", ...}
{"event_id": "...", "timestamp": "...", ...}
```

## Implementation Notes

- The parser handles malformed Unicode characters (U+FFFD replacement character) in the raw logs
- Raw lines are preserved exactly as-is in the `raw_line` field
- Multi-byte character handling: separator characters are replaced with `|` for detail extraction
- All numeric values are converted to appropriate Python types (int/float)
- Timestamps are parsed to ISO 8601 and Unix epoch

## Testing

To test the parser on the sample Mexico log:
```bash
python mexico_log_parser.py vault/raw_sources/robotross/mexico_wood_marking/bob_ross.log \
    --output /tmp/test_events.jsonl --stats
```

Expected output (from bob_ross.log):
- Total events: ~50,878
- GCODE events: ~44,806
- DRAWING events: ~3,959
- PEN events: ~1,272
- Various system, voice, AI, job events

## Dependencies

- Python 3.9+
- No external dependencies (stdlib only)

## Files

- `mexico_log_parser.py`: Main parser implementation
- `README.md`: This documentation
