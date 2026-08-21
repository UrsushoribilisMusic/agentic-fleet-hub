"""
CANIS-D: Web-search module for the Disposition Lens inference server.

Provides async search (Brave API or SearXNG) + URL fetch + text extraction.
Imported by server.py; can also be used standalone.

Privacy note: queries leave the Mac Mini to Brave / SearXNG.  This is
intentional and disclosed in the Canis UI — it is opt-in, off by default.
"""
from __future__ import annotations

import asyncio
import os
import re
import urllib.parse
from typing import List, Optional

BRAVE_SEARCH_URL = "https://api.search.brave.com/res/v1/web/search"
FETCH_TIMEOUT = 3.0        # per-URL fetch budget (seconds)
SEARCH_TIMEOUT = 8.0       # total Brave API budget
MAX_BODY_CHARS = 900       # body excerpt per result
SEARCH_TRIGGER_ENTROPY = 0.55   # normalised entropy threshold for auto-trigger


class SearchResult:
    """Single search result — title, URL, snippet, optional body excerpt."""

    def __init__(self, title: str, url: str, snippet: str, body_excerpt: str = ""):
        self.title = title
        self.url = url
        self.snippet = snippet
        self.body_excerpt = body_excerpt

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "url": self.url,
            "snippet": self.snippet,
            "body_excerpt": self.body_excerpt,
        }

    def __repr__(self) -> str:
        return f"SearchResult(title={self.title!r}, url={self.url!r})"


async def do_search(
    query: str,
    n: int = 5,
    provider: str = "brave",
) -> List[SearchResult]:
    """
    Fetch top-N search results from Brave Search API or a self-hosted SearXNG.

    Args:
        query:    The search string (typically the user's question or a refined form).
        n:        Number of results to request (actual results may be fewer).
        provider: "brave" (default) or "searxng" (self-hosted).

    Returns:
        List[SearchResult] — empty on any error so the caller can degrade gracefully.
    """
    try:
        import httpx
    except ImportError:
        print("[search] httpx not installed — cannot search.  pip install httpx")
        return []

    if provider == "brave":
        api_key = os.getenv("BRAVE_API_KEY", "").strip()
        if not api_key:
            print("[search] BRAVE_API_KEY not set — skipping search.")
            return []
        params = {"q": query, "count": str(n), "safesearch": "moderate", "text_decorations": "0"}
        headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": api_key,
        }
        url = BRAVE_SEARCH_URL
    else:
        searxng_url = os.getenv("SEARXNG_URL", "http://localhost:8888").rstrip("/")
        params = {"q": query, "format": "json", "count": str(n)}
        headers = {}
        url = f"{searxng_url}/search"

    try:
        async with httpx.AsyncClient(timeout=SEARCH_TIMEOUT) as client:
            resp = await client.get(url, params=params, headers=headers)
            resp.raise_for_status()
            data = resp.json()
    except Exception as exc:
        print(f"[search] API call failed: {exc}")
        return []

    results: List[SearchResult] = []
    if provider == "brave":
        for item in data.get("web", {}).get("results", [])[:n]:
            results.append(SearchResult(
                title=item.get("title", ""),
                url=item.get("url", ""),
                snippet=item.get("description", ""),
            ))
    else:
        for item in data.get("results", [])[:n]:
            results.append(SearchResult(
                title=item.get("title", ""),
                url=item.get("url", ""),
                snippet=item.get("content", ""),
            ))

    return results


async def fetch_and_extract(url: str, max_chars: int = MAX_BODY_CHARS) -> str:
    """
    Fetch a URL and extract its main text body.

    Uses trafilatura when available (best quality); falls back to naive HTML-strip.
    Returns an empty string on any error — never raises.
    """
    try:
        import httpx
    except ImportError:
        return ""

    try:
        async with httpx.AsyncClient(
            timeout=FETCH_TIMEOUT,
            follow_redirects=True,
            headers={"User-Agent": "Canis-Search/1.0 (+https://canis.apertus.ai)"},
        ) as client:
            resp = await client.get(url)
            html = resp.text
    except Exception:
        return ""

    try:
        import trafilatura  # type: ignore
        body = trafilatura.extract(html, include_comments=False, include_tables=False) or ""
    except ImportError:
        # Fallback: strip HTML tags and collapse whitespace
        body = re.sub(r"<[^>]+>", " ", html)
        body = " ".join(body.split())

    return body[:max_chars]


async def enrich_results(results: List[SearchResult], top_n: int = 3) -> List[SearchResult]:
    """
    Fetch and fill body_excerpt for the top-N results concurrently.

    Modifies results in place and returns them.
    """
    async def _fill(r: SearchResult) -> None:
        r.body_excerpt = await fetch_and_extract(r.url)

    await asyncio.gather(*[_fill(r) for r in results[:top_n]], return_exceptions=True)
    return results


def build_context_block(results: List[SearchResult]) -> str:
    """
    Format search results into a compact context block for Pass-2 inference.

    The block is prepended to the user's question so the model answers from
    live sources and can cite [1], [2], etc.
    """
    if not results:
        return ""
    lines = ["[WEB SEARCH RESULTS — use these to answer; cite sources as [1], [2], etc.]"]
    for i, r in enumerate(results, 1):
        body = r.body_excerpt or r.snippet
        lines.append(f"\n[{i}] {r.title}\nURL: {r.url}\n{body[:MAX_BODY_CHARS]}")
    lines.append("\n[END RESULTS]\n")
    return "\n".join(lines)


def should_search(entropy: float, answer_preview: str = "") -> bool:
    """
    Heuristic: decide whether search should be triggered.

    Triggers on high entropy (model is uncertain) OR if the model's first
    tokens suggest uncertainty ("I'm not sure", "I don't know", etc.).
    """
    if entropy >= SEARCH_TRIGGER_ENTROPY:
        return True
    # Lexical markers from the first ~200 chars of Pass-1 output
    preview = answer_preview[:200].lower()
    uncertainty_phrases = (
        "i'm not sure", "i don't know", "i cannot confirm", "i'm unable to",
        "i lack", "i don't have", "unclear", "uncertain", "as of my knowledge",
        "my training data", "i can't verify",
    )
    return any(phrase in preview for phrase in uncertainty_phrases)
