# Clau — 2026-06-10

## Task completed: MD-001 — Corpus builder (beat-grammar source list)

**PocketBase task ID**: ljgvcrkn8he70oq  
**Branch**: task/ljgvcrkn8he70oq (microdrama repo)  
**Commit**: 0a7316d  
**Status**: peer_review

### What was done
Produced `data/corpus/source_list.json` — 154 entries across 4 cells:

| Cell | Entries | Min | Pass |
|---|---|---|---|
| EN × CEO-romance | 52 | 50 | ✓ |
| EN × family-secrets | 25 | 20 | ✓ |
| ES × melodrama-hybrid | 52 | 50 | ✓ |
| ES × CEO-romance | 25 | 20 | ✓ |

Total EN = 82, total ES = 77. All URLs are public/free. 102/154 entries have view_count_at_capture (series-level platform totals — per-episode counts not surfaced publicly on any platform).

### Top content found
- **EN CEO-romance**: The Double Life of My Billionaire Husband (520.5M), True Heiress vs. Fake Queen Bee (454.4M), Married at First Sight (232.9M) — all ReelShort
- **ES melodrama-hybrid**: La doble vida de mi esposo multimillonario (170M), Tu lugar es a mi lado (57M) — ReelShort LATAM
- **Bilingual Rosetta stone**: Armas de Mujer (Telemundo × ReelShort, 123 × 2-min eps, Kate del Castillo cast) — tagged bilingual
- **ViX MicrO catalog**: 20+ series from TelevisaUnivision (MX territory, free app)
- **TV Azteca**: El sabor de la venganza — free on tvazteca.com + YouTube playlist

### Research approach
Spawned 4 parallel research agents (EN-CEO, EN-FAM, ES-MEL, ES-CEO), then synthesized results into schema.

### Blockers / notes for next agent
- view_count = null for 52 entries: DramaBox, ViX MicrO, NetShort do not expose public aggregate counts. Suggest MD-002 extraction pipeline capture per-video YouTube counts via yt-dlp where YouTube mirrors exist.
- Armas de Mujer on ReelShort: specific episode URLs not discovered — currently points to reelshort.com root. Needs per-episode URL resolution.
