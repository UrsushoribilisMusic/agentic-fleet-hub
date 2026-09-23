# WORKLOG — CANIS-BONE-05
## Multi-bone store + management (extend KnowledgePackStore)

## Task
Extend `KnowledgePackStore.swift` from a single `current.sqlite` to MULTIPLE named
bones stored at `Documents/knowledge-packs/bones/<uuid>.sqlite`, with a JSON index
tracking name, docCount, size, createdAt, active flag, and isBuiltIn.

## Layout after this ticket

```
Documents/knowledge-packs/
  bones/
    00000000-0000-0000-0000-000000000001.sqlite  ← built-in Robot Ross ATF
    <uuid2>.sqlite                                ← user-installed bone
  bones-index.json   ← [{id, name, docCount, wikiSectionCount, size, createdAt,
                          isActive, isBuiltIn}]
  current.sqlite     ← kept for backward-compat (token-download flow)
  installed-pack.json ← kept for backward-compat (legacy metadata)
```

## Key design decisions

1. **`BoneEntry`** — new Codable/Identifiable/Equatable struct published as
   `KnowledgePackStore.bones: [BoneEntry]`.

2. **`activePackURL`** — nonisolated static that reads `bones-index.json` and returns
   the active bone's path. Falls back to `currentPackURL` if no index exists (backward
   compat with pre-BONE-05 installs).

3. **`KnowledgePackRetriever`** — change default `packURL` from `currentPackURL` to
   `activePackURL`. Since default args are evaluated per call, each new retriever
   instance picks up the current active bone automatically.

4. **Built-in bone** — stable UUID `00000000-0000-0000-0000-000000000001` so seeding is
   idempotent. `isBuiltIn = true` prevents deletion. Re-seeded as active whenever the
   last user bone is deleted.

5. **`deletePack()`** — kept for backward compat with `ModelHubView`. Deletes the active
   non-built-in bone; falls back to clearing `current.sqlite` if no bones index.

6. **CRUD API**:
   - `installBone(from:name:docCount:wikiSectionCount:) throws -> BoneEntry`
   - `setActiveBone(id:) throws`
   - `renameBone(id:name:) throws`
   - `deleteBone(id:) throws`

## Files changed
- `Canis/Services/KnowledgePackStore.swift` — full rewrite with multi-bone support
- `Canis/Services/KnowledgePackRetriever.swift` — update default packURL
- `CanisTests/BoneStoreTests.swift` — new: BoneEntry codable + store integration tests
