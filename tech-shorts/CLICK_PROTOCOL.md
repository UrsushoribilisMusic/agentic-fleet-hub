# NotebookLM Click Protocol (TS-2)

Template for wiring the real browser steps after Miguel's demo.
Each section maps 1-to-1 to a method in `notebooklm_driver.py`.

Fill in `SELECTOR`, `ACTION`, and `EXPECTED` after the demo walkthrough.

---

## Step 1 — open_or_create_notebook(source_urls)

**Goal:** Land on a notebook page that has zero or more of our source URLs already
added. Return the notebook URL (for recording in `jobs.json`).

**Sub-steps:**

1. Navigate to `https://notebooklm.google.com/`
2. If an existing notebook URL is stored in the job (`job["notebook_url"]`), open it.
   Otherwise create a new notebook.

**Create new notebook click path:**
```
SELECTOR:  (fill in after demo — e.g. button[aria-label="New notebook"])
ACTION:    click
EXPECTED:  modal or new notebook page opens
```

**Name/title the notebook (optional):**
```
SELECTOR:  (fill in)
ACTION:    type(<title>)
EXPECTED:  (fill in)
```

---

## Step 2 — add_sources(source_urls)

**Goal:** Add each source URL to the notebook if not already present.

**Open "Add source" flow:**
```
SELECTOR:  (fill in — e.g. button with text "Add source" or + icon)
ACTION:    click
EXPECTED:  source-add dialog opens
```

**Switch to "Website" / URL tab (if needed):**
```
SELECTOR:  (fill in — e.g. tab button "Website" or "URL")
ACTION:    click
EXPECTED:  URL input field visible
```

**Paste URL and confirm:**
```
SELECTOR:  (fill in — e.g. input[placeholder*="URL"])
ACTION:    fill(<url>)
SELECTOR2: (fill in — confirm/insert button)
ACTION2:   click
EXPECTED:  source appears in source list, spinner then checkmark
```

**Wait for source to finish loading:**
```
EXPECTED:  (fill in — e.g. spinner disappears, source title appears in sidebar)
TIMEOUT:   60s per source
```

---

## Step 3 — trigger_video_overview()

**Goal:** Click the button that starts Video Overview generation for both the
short (9:16 vertical) and the long (16:9 landscape) formats.

**Open "Audio/Video" or "Studio" panel:**
```
SELECTOR:  (fill in after demo)
ACTION:    click
EXPECTED:  panel opens showing Audio Overview + Video Overview options
```

**Trigger Short (9:16 vertical) generation:**
```
SELECTOR:  (fill in — likely a "Generate" or "Create" button near the short video option)
ACTION:    click
EXPECTED:  progress indicator / spinner appears
```

**Trigger Long (16:9 landscape) generation:**
```
SELECTOR:  (fill in)
ACTION:    click
EXPECTED:  second progress indicator appears
```

**Notes from demo:** (fill in)

---

## Step 4 — wait_for_video_ready(timeout_s=900)

**Goal:** Poll until both videos show a "Download" or "Ready" state.

**"Ready" indicator for Short:**
```
SELECTOR:  (fill in — e.g. button[aria-label*="Download"] near short video)
CONDITION: element is visible AND enabled
POLL:      every 15s
TIMEOUT:   900s (15 min)
```

**"Ready" indicator for Long:**
```
SELECTOR:  (fill in)
CONDITION: element is visible AND enabled
POLL:      every 15s
TIMEOUT:   900s
```

**Error / failed state:**
```
SELECTOR:  (fill in — e.g. error toast or retry button)
ACTION:    raise RuntimeError("NotebookLM video generation failed")
```

---

## Step 5 — download_mp4s()

**Goal:** Download both mp4s to `workdir/{job_id}_short.mp4` and
`workdir/{job_id}_long.mp4`.

**Download Short:**
```
SELECTOR:  (fill in — download button for the short/vertical video)
ACTION:    click → intercept browser download event → save to workdir
FILENAME:  {job_id}_short.mp4
```

**Download Long:**
```
SELECTOR:  (fill in — download button for the long/landscape video)
ACTION:    click → intercept browser download event → save to workdir
FILENAME:  {job_id}_long.mp4
```

**Playwright download interception pattern (already wired in driver):**
```python
with page.expect_download() as dl_info:
    page.click(DOWNLOAD_SELECTOR)
download = dl_info.value
download.save_as(workdir / filename)
```

---

## Known unknowns (to resolve during demo)

- [ ] Does NotebookLM require Google OAuth on every launch or does cookie jar work?
- [ ] Are the Short and Long formats triggered from the same panel or different pages?
- [ ] What does the "Video Overview" UI look like — is it a separate "Video" tab,
      or buried in "Audio Overview" > dropdown?
- [ ] Is there a rate limit or cooldown between video generations?
- [ ] What filename does NotebookLM assign to downloaded mp4s (for dedup)?
- [ ] Do Short and Long generate in parallel or sequentially?
- [ ] Approximate generation time for a 1-article notebook?
