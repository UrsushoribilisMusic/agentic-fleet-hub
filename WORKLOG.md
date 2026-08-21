# WORKLOG — CANIS-D: Real Web-Search Tool

**Task ID:** 319n7hqonu30l2n  
**Agent:** clau  
**Branch:** task/319n7hqonu30l2n

## Deliverables

1. `disposition-lens/search.py` — standalone async search module (Brave API + SearXNG fallback + trafilatura extraction)
2. `disposition-lens/server.py` — 2-pass `/infer` with `search_enabled` flag + `citations` in response
3. `disposition-lens/prototype/disposition_lens.jsx` — `searching` activity state added to STATES
4. `canis-ios/Canis/Models/WebSearchResult.swift` — Codable data model
5. `canis-ios/Canis/Services/WebSearchService.swift` — Brave API URLSession client
6. `canis-ios/Canis/Services/CanisMLXEngine.swift` — search-before-generate extension
7. `canis-ios/Canis/Services/ChatViewModel.swift` — search state handling
8. `canis-ios/Canis/Views/ChatView.swift` — web search toggle + searching indicator
9. `canis-ios/Canis/Models/ChatMessage.swift` — citations field
10. `canis-ios/Canis/Models/Disposition.swift` — `CanisGenerationEvent` search cases

## Design decisions

- **Mac Mini (server.py):** 2-pass approach. Pass 1 = short generation (64 tokens), entropy-threshold trigger.
  Pass 2 = full generation with search context injected.
- **iOS:** search-before-generate (not 2-pass) — simpler, fewer MLX sessions, lower memory pressure.
  Trigger = keyword-based heuristic (current events, "latest", "recent", "today", etc.) + opt-in toggle.
- **`searching` is an ACTIVITY STATE, not a J-space disposition.** New `CanisGenerationEvent` cases:
  `.searchStarted(query:)` and `.searchComplete(citations:)`. `DispositionReadout` unchanged.
- **Sovereignty framing:** search is opt-in (off by default), disclosed in UI ("Query sent to Brave Search"),
  swappable to self-hosted SearXNG. Inference stays on-device. Documented in CANIS-D-design.md.

## Key files touched

| File | Change |
|---|---|
| `disposition-lens/search.py` | NEW — search module |
| `disposition-lens/server.py` | ADD SearchResult model, `_do_search`, `_fetch_and_extract`, 2-pass infer |
| `disposition-lens/prototype/disposition_lens.jsx` | ADD `searching` to STATES + REEL |
| `canis-ios/Canis/Models/WebSearchResult.swift` | NEW |
| `canis-ios/Canis/Services/WebSearchService.swift` | NEW |
| `canis-ios/Canis/Services/CanisMLXEngine.swift` | ADD `generateWithSearch` |
| `canis-ios/Canis/Services/ChatViewModel.swift` | ADD search state handling |
| `canis-ios/Canis/Views/ChatView.swift` | ADD search toggle + searching label |
| `canis-ios/Canis/Models/ChatMessage.swift` | ADD `citations: [WebSearchResult]` |
| `canis-ios/Canis/Models/Disposition.swift` | ADD `.searchStarted` / `.searchComplete` cases |

## Codi wiring notes

- `WebSearchService.swift` is complete — Codi does NOT need to touch it
- `CanisMLXEngine.generateWithSearch` stubs the 2-pass re-prompt flow with `TODO(codi)` markers
- The key Codi task: hook `generateWithSearch` into the existing `generate` function by passing
  the search results back through `ChatSession.streamResponse(to: enrichedPrompt)` where
  `enrichedPrompt = SearchContextBuilder.build(results:query:)` prepended to the original question.
- `DispositionAvatarView` will need a `isSearching: Bool` param passed from ChatViewModel — Codi wires that.
