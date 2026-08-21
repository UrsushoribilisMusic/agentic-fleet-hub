# CANIS-D: Web-Search Tool Design

*Status: implemented (server.py + iOS). Codi wiring notes in WORKLOG.md.*

---

## 1. What was built

### Mac Mini server (disposition-lens/server.py)

Two-pass inference with optional web search:

```
User question
    │
    ▼
Pass 1: generate (max 64 tokens)
    │
    ├─ entropy < 0.55 AND no uncertainty phrases → skip search
    │
    └─ entropy ≥ 0.55 OR uncertainty phrases → SEARCH
           │
           ▼
     Brave Search API: top-5 results
     Fetch + extract body text from top-3 URLs (3s timeout each, concurrent)
           │
           ▼
     Build context block:
     [WEB SEARCH RESULTS]
     [1] Title — URL
     Body excerpt (max 900 chars each)
     [END RESULTS]
           │
           ▼
    Pass 2: generate (full tokens) with search context prepended
           │
           ▼
    Return: answer + disposition + citations[]
```

**New API fields (InferRequest):**
- `search_enabled: bool = False` (opt-in)
- `search_provider: str = "brave"` (`"brave"` | `"searxng"`)
- `search_top_n: int = 5`

**New API fields (InferResponse):**
- `search_triggered: bool`
- `citations: List[SearchResultItem]` (title, url, snippet, body_excerpt)

### iOS app (Canis)

Search-before-generate strategy (simpler than 2-pass — one MLX session):

1. `WebSearchService.swift` — Brave API client, async URLSession, concurrent body-fetch for top-3 results
2. `SearchContextBuilder` — builds the context block injected into the prompt
3. `CanisMLXEngine.generateWithSearch()` — checks keyword heuristic → searches → single-pass generation with enriched prompt
4. `ChatViewModel` — `isSearching`, `searchQuery`, `webSearchEnabled` state
5. `ChatView` — web search toggle (off by default, shows disclosure: "Query sent to Brave Search") + searching indicator
6. `MessageBubbleView` — citation list at bottom of assistant message

**New `CanisGenerationEvent` cases:**
```swift
case searchStarted(query: String)
case searchComplete(citations: [WebSearchResult])
```

**Search trigger heuristic (iOS):**
- Keyword scan: "latest", "recent", "current", "today", "price of", "who won", etc.
- OR lexical uncertainty: "I'm not sure", "I don't know", "my training data", etc.

---

## 2. Emotion / disposition mapping

**`searching` is a UI ACTIVITY STATE — it is NOT a J-space disposition.**

J-space captures what the model is currently disposed to say. Search happens *between* inference passes — there are no hidden states to read during a URL fetch. Adding `searching` to `DISPOSITIONS` in `disposition.py` would be architecturally wrong.

**What was added:**
- `STATES.searching` in `disposition_lens.jsx` — dog nose-down, ears forward, focused steel-blue tint, head tilted 18°. Distinct from `curious` (green, inquisitive head-tilt) by direction and color.
- Two new `CanisGenerationEvent` cases so `ChatViewModel` can set `isSearching = true` while the fetch is in flight, then clear it on `.searchComplete`.

**Honest emotion mapping:**
| J-space state | Meaning | What happens next |
|---|---|---|
| `uncertain` (H ≥ 0.62) | Model doesn't know | → triggers search |
| `searching` (UI only) | Fetching live results | avatar nose-down, sniff-pulse |
| `confident` (H ≤ 0.22) | Knows the answer (from search) | → avatar confident after Pass 2 |

The arc is legible and honest: *uncertain → searches → returns confident*. The dog's journey matches the model's epistemic state.

**Proposed new indicators (2):**
1. `searching` — activity overlay on the dog avatar: nose pointed down-right at ~18° head-tilt, ears pricked forward, eyes pupils shifted down (looking at ground), periodic 1.5s nose-pulse highlight. Tint: steel-blue `#3A8FD4`.
2. `thinking` (already implied by streaming cursor) — keep as-is, no changes needed.

---

## 3. Sovereignty tension — honest framing

**What leaves the device:**
- DNS + HTTPS to `api.search.brave.com` (or your own SearXNG)
- The user's query text
- HTTP GET to up to 5 external URLs (title/body fetch)

**What stays on-device:**
- All model inference (LLM never goes to cloud)
- All personal data (photos, calendar, health — none of that is in the search query)
- Disposition readout (J-lens, entropy, seed-vectors — local only)

**Three-layer framing:**

1. **Inference is always local.** The model thinks on your iPhone. Nothing about the model's computation touches the cloud.

2. **Search is explicit + opt-in.** The toggle defaults to OFF. When ON, the UI shows: *"Query sent to Brave Search"* inline. No silent egress.

3. **Search provider is swappable.** Users can point to a self-hosted SearXNG for full on-device (or at least on-network) sovereignty. `SEARXNG_URL` env var for the server; future iOS settings for the app.

**Demo/explainer copy:**
> "Canis thinks on-device. When it's uncertain, it can look things up — just like you would. You choose when."

**What NOT to claim:**
- Do NOT say "fully private search" — Brave still sees the query.
- DO say "Brave Search doesn't track queries to build a profile" (that's their stated policy) — but only if Apertus team confirms this is accurate.

---

## 4. Implementation sequence

| Step | Owner | Estimated effort |
|---|---|---|
| `search.py` + `server.py` 2-pass | clau ✅ | ~4h |
| `disposition_lens.jsx` searching state | clau ✅ | 30min |
| `WebSearchResult.swift` + `WebSearchService.swift` | clau ✅ | 2h |
| `CanisGenerationEvent` + `ChatViewModel` + `ChatView` + `MessageBubbleView` | clau ✅ | 2h |
| `CanisMLXEngine.generateWithSearch` stub | clau ✅ | 1h |
| Wire re-prompt into `ChatSession.streamResponse` | **Codi** | 2–3h |
| `DispositionAvatarView` — `isSearching` param + nose-sniff pulse | **Codi** | 1–2h |
| Add `BRAVE_API_KEY` build setting in Xcode + vault | **Codi** | 30min |
| `xcodegen generate` to pull in new Swift files | **Codi** | 5min |

**Blockers:** None for Clau's scope.  
Codi blocked until CANIS-A iOS skeleton merges (needs `CanisMLXEngine` to compile).

---

## 5. Codi wiring guide

### Wire `generateWithSearch` re-prompt (key TODO)

In `CanisMLXEngine.generateWithSearch`, the enriched prompt is already built:
```swift
effectivePrompt = SearchContextBuilder.build(results: results, query: prompt)
```

The `ChatSession.streamResponse(to: effectivePrompt)` call below it will use this. **No additional change needed** — the stub is complete. Codi only needs to:
1. Run `xcodegen generate` to add new files to the Xcode project
2. Add `BRAVE_API_KEY` as a User-Defined build setting in Xcode (value = secret from vault)
3. Wire `isSearching` into `DispositionAvatarView` for the nose-down animation

### `DispositionAvatarView` searching overlay

```swift
// In DispositionAvatarView, add isSearching param:
struct DispositionAvatarView: View {
    let readout: DispositionReadout
    var isSearching: Bool = false   // NEW
    
    // In body: if isSearching, override avatar params to "searching" state
    // (nose-down, head-tilt 18°, pupilY +5, tint #3A8FD4)
    // Animate with a periodic nose-pulse every 1.5s while isSearching == true
}
```

Pass from `ChatView`:
```swift
DispositionAvatarView(readout: viewModel.currentReadout, isSearching: viewModel.isSearching)
```
