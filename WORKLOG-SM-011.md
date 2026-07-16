# SM-011 Worklog

Task: Web Console - Example RAG Indices & Personas (`ro2mwixuoyr1gz6`)

Plan:
1. Reuse the SM-004 RAG package bundle format for trial examples so iOS can consume examples and customer packages through the same path.
2. Add two prebuilt example indices: Robot Ross ATF wiki and a generic industrial troubleshooting guide.
3. Add default personas with preloaded system prompts: Field Engineer, Product Manager, Technical Writer.
4. Expose examples/personas in the Sovereign Mind console API and render free unauthenticated downloads in the web console.
5. Add focused tests for package creation, download resolution, persona metadata, and retrieval.

Notes:
- Branch: `task/ro2mwixuoyr1gz6`
- Depends on SM-004 package generator already present in `package/server/sovereign-rag.mjs`.
