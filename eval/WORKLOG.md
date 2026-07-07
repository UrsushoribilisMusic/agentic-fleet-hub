# WORKLOG — EVAL-002: Retrieval wiki (hard-facts corpus)

Task ID: rkjlt9ibr4qloop
Branch: task/rkjlt9ibr4qloop
Agent: clau

## Plan

Build the wiki the model consults at query time. Frozen pre-cutoff gold corpus (created < 2026-06-22, no FX- records). Atomic entries: one fact/rule/metric per entry, each {id, title, body, source_ref, type}.

### Sources consumed
1. `/Users/miguelrodriguez/projects/fx/rules.md` — 30 behavioral rules R01–R30
2. `/Users/miguelrodriguez/projects/fx/out/facts/facts.json` — aggregate metrics
3. `/Users/miguelrodriguez/projects/fx/out/facts/facts.db` — task_events (circuit_breaker, status_transitions), tasks (reassignment counts)
4. `agentic-fleet-hub/AGENTS/RULES.md` — team protocol reference
5. `agentic-fleet-hub/standups/` — incident references (I002 Misty spam)
6. Lessons collection (via RULES.md source annotations)

### Output structure
```
eval/wiki/
├── README.md
├── index.json         (66 entries, searchable)
└── entries/           (66 × {id, title, body, source_ref, type})
    R01–R30 (rules), F001–F025 (facts), I001–I005 (incidents), P001–P006 (protocols)
```

## Steps done

1. ✅ Read MISSION_CONTROL.md + heartbeat
2. ✅ Created branch task/rkjlt9ibr4qloop, pushed to origin
3. ✅ Inspected facts.db schema and queried for circuit_breaker events, status transitions, reassignment counts
4. ✅ Built 66 entries via /tmp/build_wiki.py (all types: rule/fact/incident/protocol)
5. ✅ Wrote entries/*.json, index.json, README.md

## Corpus integrity notes

- No FX- task IDs appear in any entry body or source_ref
- All date references are pre-2026-06-22
- Circuit breaker incident (I001) verified from facts.db query: 32 events, most active task = 8sto1zdn9dljy98 (39 reassignments)
- Misty spam incident (I002) verified from standups/2026-03-20.md and fleet/misty/PROGRESS.md
- Self-approval violation (I003) sourced from lessons and CLAUDE.md annotations
