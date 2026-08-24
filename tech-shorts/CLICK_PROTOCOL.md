# NotebookLM click-path protocol (captured 2026-08-24, live walkthrough with Miguel)

The browser-driven step (TS-2). NotebookLM = notebook.google.com ("Gemini Notebook", Video Overviews powered by Gemini). No clean API → drive the browser. Locate elements by **visible text / role** (window size varies; pixel coords below are only backup hints from a 1469×836 capture).

## Full creation → download flow

### 1 · Main list → create notebook
- URL: `https://notebook.google.com/` (main list, "My notebooks"). If it opens the last notebook instead, click the **top-left logo/icon** to return to the list.
- Click **"+ Create new"** (top-right). → opens an untitled notebook (`/notebook/<uuid>`).

### 2 · Add sources
- In the left **"Sources"** panel, click **"+ Add sources"** (top-left of panel). → opens the Add-sources dialog (`?addSource=true`), titled *"Create Audio and Video Overviews from …"*.
- **Source types** (buttons in the dialog):
  - **URL**: type the URL into the box → click the blue **submit arrow (→)**. Repeat per URL. (Also a **"Websites"** button.)
  - **Upload files**: `Upload files` button — pdf, images, docs, audio (→ this is the TS-11 file-source path).
  - **Copied text**: `Copied text` button — paste md/txt content (→ TS-11 path for .md/.txt).
  - **Drive**: `Drive` button.
- Counter shows `n / 300` sources. Add each source from the job.
- After sources are added, NotebookLM **auto-generates a summary** in the Chat pane and **auto-titles** the notebook from the sources. Wait for the summary to render before proceeding.

### 3 · Video Overview (the deliverable) — run TWICE
- Right **"Studio"** panel → click the **"Video Overview"** tile (top-right of the tile grid).
- Dialog **"Customize Video Overview"**:
  - **Format** cards: **Cinematic** (default ✓) · **Explainer** · **Short (New!)**.
  - Optional **"What should the video focus on?"** chips + **Custom topic** box → *leave blank for Gemini's creative license* (our default).
  - Click **"Generate"**.
- **Two generations per job**: run once with **Cinematic**, then re-open Video Overview and run again with **Short**. They generate **in parallel** (Studio shows both "Generating … Video Overview… This may take a while").
- ⏱ Videos take **~10–15 min** (server-load dependent; faster in CET morning before US peak).

### 4 · Publishing extras (optional, not required for the video)
- **Infographic** tile → *"Customize Infographic"*: language · **orientation** (Landscape/Portrait/Square) · **visual style** (Auto-select / Kawaii / Clay / Sketch Note / **Anime** ← our default / more via ">") · detail (Concise/**Standard**/Detailed) · optional description → **Generate**. Finishes fast; great still image for **X / Reddit** posts (post with the notebook/video URL).
- **Slide Deck** tile → *"Customize Slide Deck"*: **Detailed Deck** (our default — more per page) / Presenter Slides · length (Short/**Default**) · description → type **"Use the Lego artwork style"** → **Generate**. (For Reddit posts. Many slides go unused; some are gems.)

### 5 · Preview & download (same for videos, infographic, slide deck)
- In the **Studio** panel, click the finished artifact (e.g. its title link) → opens a **preview modal**.
- Top-right modal controls: Share · minimize · **✕ close** · **⋮ (three-dot menu)**.
- Click **⋮ → "Download"**. (Menu also has "Delete".) → downloads the file (mp4 for videos, image for infographic, deck for slides) to `~/Downloads`.

## Notes for the driver (`notebooklm_driver.py`)
- Prefer role/text locators: `getByRole('button', {name:'Create new'})`, `'Add sources'`, `'Generate'`, tile by text `'Video Overview'`, format card `'Cinematic'`/`'Short'`, menu item `'Download'`.
- Auth: uses the logged-in Chrome session (Miguel's Google account). Keep session warm; no headless login.
- The long generation wait needs polling: watch the Studio item flip from "Generating … This may take a while" to a clickable finished artifact, then open → ⋮ → Download.
- Two video files per job (Cinematic + Short) → both land in ~/Downloads; hand off to `build_edge.sh`/`pipeline.py` for hook/outro assembly.
- Downloaded filename is NotebookLM's title (e.g. the auto-title) — capture the newest mp4 in ~/Downloads after the download click.

## Reference capture: this session
- Notebook: "A Global Workspace in Language Models" (auto-titled), 2 sources (anthropic.com/research/global-workspace + transformer-circuits.pub/2026/workspace).
- Generated: Cinematic + Short video overviews (Video Overview ×2), Infographic "Inside the AI J-Space Mindscape" (Anime), Slide Deck (Detailed, Lego style).
