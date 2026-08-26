# Codi Worklog - WP1 C-109

Task: WP1 C-109 On-device retrieval against downloaded pack.

Plan:
- Inspect C-108 pack download/backend format and the current Canis iOS chat path.
- Add an iOS knowledge pack store that can install/download a versioned SQLite pack and report local state.
- Add an offline retriever over the downloaded pack with citations to wiki sections/source pages.
- Route normal chat through local pack retrieval before MLX generation so airplane-mode answers remain grounded.
- Add focused tests for retrieval/citation behavior and run the Canis build verifier.
