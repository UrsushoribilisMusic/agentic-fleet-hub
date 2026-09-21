#!/usr/bin/env python3
"""fleet/research_ledger.py — Research Workbench Source and Claim Ledger

Part of Flotilla Council Protocol (FCP-7).
Tracks sources and claims for research-heavy council goals (prospect intelligence,
tech shorts, public articles, sales assets), enforcing source discipline, confidence
tiers, and complete evidence auditability.

Storage:
- Primary: PocketBase collections `research_sources` and `research_claims`.
- Fallback / Pilot: File-backed JSON store at `AGENTS/COUNCIL/research/{goal_id}.json`.

Requirements enforced:
1. Do not store unverified claims as if they are facts (verification_status required).
2. Confidence tiers: High, Moderate, Low, Speculative.
3. Public-facing claims (usable_in_public_copy=True) must have source URLs and cannot be speculative.
4. Prefer primary sources (tracked via source_type with primary preference).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PB_URL = os.environ.get("PB_URL", "http://127.0.0.1:8090")
RESEARCH_FILE_DIR = ROOT / "AGENTS" / "COUNCIL" / "research"

CONFIDENCE_TIERS = ["high", "moderate", "low", "speculative"]
SOURCE_TYPES = ["primary", "secondary", "tertiary", "interview", "internal_telemetry", "other"]
RELIABILITY_TIERS = ["high", "moderate", "low", "unknown"]
VERIFICATION_STATUSES = ["unverified", "verified", "contested", "refuted"]


class ValidationError(ValueError):
    """Raised when source or claim fails research discipline rules."""
    pass


@dataclass
class ResearchSource:
    goal_id: str
    url: str
    title: str
    source_type: str = "primary"
    reliability: str = "high"
    author: str = ""
    agent: str = "gem"
    notes: str = ""
    id: Optional[str] = None
    created: Optional[str] = None
    updated: Optional[str] = None

    def validate(self) -> None:
        if not self.goal_id.strip():
            raise ValidationError("Source must specify a non-empty goal_id")
        if not self.url.strip():
            raise ValidationError("Source must have a valid url")
        parsed = urllib.parse.urlparse(self.url)
        if parsed.scheme not in ("http", "https", "file"):
            raise ValidationError(f"Source url scheme must be http, https, or file: {self.url}")
        if not self.title.strip():
            raise ValidationError("Source must have a title")
        self.source_type = self.source_type.lower().strip()
        if self.source_type not in SOURCE_TYPES:
            raise ValidationError(f"Invalid source_type '{self.source_type}'. Must be one of {SOURCE_TYPES}")
        self.reliability = self.reliability.lower().strip()
        if self.reliability not in RELIABILITY_TIERS:
            raise ValidationError(f"Invalid reliability '{self.reliability}'. Must be one of {RELIABILITY_TIERS}")


@dataclass
class ResearchClaim:
    goal_id: str
    extracted_claim: str
    confidence: str = "moderate"
    verification_status: str = "unverified"
    source_id: str = ""
    source_url: str = ""
    source_title: str = ""
    source_type: str = "primary"
    quote_snippet: str = ""
    usable_in_public_copy: bool = False
    needs_human_review: bool = False
    reviewed_by: str = ""
    agent: str = "gem"
    notes: str = ""
    id: Optional[str] = None
    created: Optional[str] = None
    updated: Optional[str] = None

    def validate(self) -> None:
        if not self.goal_id.strip():
            raise ValidationError("Claim must specify a non-empty goal_id")
        if not self.extracted_claim.strip():
            raise ValidationError("Claim text (extracted_claim) cannot be empty")
        
        self.confidence = self.confidence.lower().strip()
        if self.confidence not in CONFIDENCE_TIERS:
            raise ValidationError(f"Invalid confidence '{self.confidence}'. Must be one of {CONFIDENCE_TIERS}")

        self.verification_status = self.verification_status.lower().strip()
        if self.verification_status not in VERIFICATION_STATUSES:
            raise ValidationError(
                f"Invalid verification_status '{self.verification_status}'. Must be one of {VERIFICATION_STATUSES}"
            )

        if self.source_type:
            self.source_type = self.source_type.lower().strip()
            if self.source_type not in SOURCE_TYPES:
                raise ValidationError(f"Invalid source_type '{self.source_type}'. Must be one of {SOURCE_TYPES}")

        # Public copy guardrails:
        # Public-facing copy requires an audit URL and cannot be speculative or refuted.
        if self.usable_in_public_copy:
            if not self.source_url.strip() and not self.source_id.strip():
                raise ValidationError("Public-facing claims (usable_in_public_copy=True) must have a source_url or linked source_id.")
            if self.confidence == "speculative":
                raise ValidationError("Speculative claims cannot be marked usable_in_public_copy without higher confidence.")
            if self.verification_status == "refuted":
                raise ValidationError("Refuted claims cannot be marked usable_in_public_copy.")

        # Fact discipline guardrail:
        # Do not store unverified claims as if they are facts.
        if self.verification_status == "verified":
            if not self.source_url.strip() and not self.source_id.strip():
                raise ValidationError("Verified claims must cite a source_url or source_id.")
            if not self.quote_snippet.strip() and not self.notes.strip():
                raise ValidationError("Verified claims must include quote_snippet or notes establishing evidence.")


# ---------------------------------------------------------------------------
# API / PocketBase & File Backends
# ---------------------------------------------------------------------------

class ResearchLedgerClient:
    def __init__(self, pb_url: str = DEFAULT_PB_URL, force_file: bool = False):
        self.pb_url = pb_url.rstrip("/")
        self.force_file = force_file
        self._pb_available: Optional[bool] = None

    def is_pocketbase_available(self) -> bool:
        if self.force_file:
            return False
        if self._pb_available is not None:
            return self._pb_available
        try:
            req = urllib.request.Request(f"{self.pb_url}/api/health", headers={"User-Agent": "ResearchLedger/1.0"})
            with urllib.request.urlopen(req, timeout=1.5) as resp:
                self._pb_available = (resp.status == 200)
        except Exception:
            self._pb_available = False
        return self._pb_available

    def _pb_request(self, method: str, endpoint: str, data: Optional[dict] = None) -> dict:
        url = f"{self.pb_url}{endpoint}"
        body = json.dumps(data).encode("utf-8") if data is not None else None
        headers = {"User-Agent": "ResearchLedger/1.0"}
        if data is not None:
            headers["Content-Type"] = "application/json"
        req = urllib.request.Request(url, data=body, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as err:
            err_body = err.read().decode("utf-8")
            raise RuntimeError(f"PocketBase API error {err.code} on {endpoint}: {err_body}")

    # File-backed storage helpers
    def _file_path(self, goal_id: str) -> Path:
        RESEARCH_FILE_DIR.mkdir(parents=True, exist_ok=True)
        safe_id = "".join(c for c in goal_id if c.isalnum() or c in ("-", "_"))
        return RESEARCH_FILE_DIR / f"{safe_id}.json"

    def _read_file_ledger(self, goal_id: str) -> dict:
        path = self._file_path(goal_id)
        if not path.exists():
            return {
                "goal_id": goal_id,
                "sources": [],
                "claims": [],
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception as e:
            raise RuntimeError(f"Error reading file ledger at {path}: {e}")

    def _write_file_ledger(self, goal_id: str, data: dict) -> None:
        path = self._file_path(goal_id)
        data["updated_at"] = datetime.now(timezone.utc).isoformat()
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    # -----------------------------------------------------------------------
    # Sources Operations
    # -----------------------------------------------------------------------

    def record_source(self, source: ResearchSource) -> ResearchSource:
        source.validate()
        if self.is_pocketbase_available():
            payload = {
                "goal_id": source.goal_id,
                "url": source.url,
                "title": source.title,
                "author": source.author,
                "source_type": source.source_type,
                "reliability": source.reliability,
                "agent": source.agent,
                "notes": source.notes,
            }
            res = self._pb_request("POST", "/api/collections/research_sources/records", payload)
            source.id = res.get("id")
            source.created = res.get("created")
            source.updated = res.get("updated")
            return source

        # File-backed path
        data = self._read_file_ledger(source.goal_id)
        source.id = source.id or f"src_{len(data['sources']) + 1:04d}"
        source.created = source.created or datetime.now(timezone.utc).isoformat()
        source.updated = datetime.now(timezone.utc).isoformat()
        
        # update or insert
        sources_list = [s for s in data["sources"] if s.get("id") != source.id]
        sources_list.append(asdict(source))
        data["sources"] = sources_list
        self._write_file_ledger(source.goal_id, data)
        return source

    def list_sources(self, goal_id: str) -> List[ResearchSource]:
        if self.is_pocketbase_available():
            q = urllib.parse.urlencode({
                "filter": f'goal_id="{goal_id}"',
                "sort": "-created",
                "perPage": 200,
            })
            res = self._pb_request("GET", f"/api/collections/research_sources/records?{q}")
            out = []
            for item in res.get("items", []):
                out.append(ResearchSource(
                    id=item.get("id"),
                    goal_id=item.get("goal_id", ""),
                    url=item.get("url", ""),
                    title=item.get("title", ""),
                    source_type=item.get("source_type", "primary"),
                    reliability=item.get("reliability", "high"),
                    author=item.get("author", ""),
                    agent=item.get("agent", ""),
                    notes=item.get("notes", ""),
                    created=item.get("created"),
                    updated=item.get("updated"),
                ))
            return out

        data = self._read_file_ledger(goal_id)
        return [ResearchSource(**s) for s in data.get("sources", [])]

    # -----------------------------------------------------------------------
    # Claims Operations
    # -----------------------------------------------------------------------

    def record_claim(self, claim: ResearchClaim) -> ResearchClaim:
        claim.validate()
        if self.is_pocketbase_available():
            payload = {
                "goal_id": claim.goal_id,
                "extracted_claim": claim.extracted_claim,
                "confidence": claim.confidence,
                "verification_status": claim.verification_status,
                "source_id": claim.source_id,
                "source_url": claim.source_url,
                "source_title": claim.source_title,
                "source_type": claim.source_type,
                "quote_snippet": claim.quote_snippet,
                "usable_in_public_copy": claim.usable_in_public_copy,
                "needs_human_review": claim.needs_human_review,
                "reviewed_by": claim.reviewed_by,
                "agent": claim.agent,
                "notes": claim.notes,
            }
            res = self._pb_request("POST", "/api/collections/research_claims/records", payload)
            claim.id = res.get("id")
            claim.created = res.get("created")
            claim.updated = res.get("updated")
            return claim

        data = self._read_file_ledger(claim.goal_id)
        claim.id = claim.id or f"clm_{len(data['claims']) + 1:04d}"
        claim.created = claim.created or datetime.now(timezone.utc).isoformat()
        claim.updated = datetime.now(timezone.utc).isoformat()

        claims_list = [c for c in data["claims"] if c.get("id") != claim.id]
        claims_list.append(asdict(claim))
        data["claims"] = claims_list
        self._write_file_ledger(claim.goal_id, data)
        return claim

    def update_claim(self, claim_id: str, updates: dict, goal_id: Optional[str] = None) -> dict:
        if self.is_pocketbase_available():
            return self._pb_request("PATCH", f"/api/collections/research_claims/records/{claim_id}", updates)

        if not goal_id:
            raise ValueError("goal_id required for file-backed claim updates")
        data = self._read_file_ledger(goal_id)
        target = None
        for c in data["claims"]:
            if c.get("id") == claim_id:
                target = c
                break
        if not target:
            raise ValueError(f"Claim with id {claim_id} not found in goal {goal_id}")
        target.update(updates)
        target["updated"] = datetime.now(timezone.utc).isoformat()
        self._write_file_ledger(goal_id, data)
        return target

    def list_claims(
        self,
        goal_id: str,
        confidence: Optional[str] = None,
        verification_status: Optional[str] = None,
        public_only: bool = False,
    ) -> List[ResearchClaim]:
        if self.is_pocketbase_available():
            filters = [f'goal_id="{goal_id}"']
            if confidence:
                filters.append(f'confidence="{confidence.lower().strip()}"')
            if verification_status:
                filters.append(f'verification_status="{verification_status.lower().strip()}"')
            if public_only:
                filters.append("usable_in_public_copy=true")
            filter_str = " && ".join(filters)

            q = urllib.parse.urlencode({
                "filter": filter_str,
                "sort": "confidence,created",
                "perPage": 500,
            })
            res = self._pb_request("GET", f"/api/collections/research_claims/records?{q}")
            out = []
            for item in res.get("items", []):
                out.append(ResearchClaim(
                    id=item.get("id"),
                    goal_id=item.get("goal_id", ""),
                    extracted_claim=item.get("extracted_claim", ""),
                    confidence=item.get("confidence", "moderate"),
                    verification_status=item.get("verification_status", "unverified"),
                    source_id=item.get("source_id", ""),
                    source_url=item.get("source_url", ""),
                    source_title=item.get("source_title", ""),
                    source_type=item.get("source_type", "primary"),
                    quote_snippet=item.get("quote_snippet", ""),
                    usable_in_public_copy=bool(item.get("usable_in_public_copy", False)),
                    needs_human_review=bool(item.get("needs_human_review", False)),
                    reviewed_by=item.get("reviewed_by", ""),
                    agent=item.get("agent", ""),
                    notes=item.get("notes", ""),
                    created=item.get("created"),
                    updated=item.get("updated"),
                ))
            return out

        data = self._read_file_ledger(goal_id)
        raw_claims = data.get("claims", [])
        out = []
        for c in raw_claims:
            claim = ResearchClaim(**c)
            if confidence and claim.confidence != confidence.lower().strip():
                continue
            if verification_status and claim.verification_status != verification_status.lower().strip():
                continue
            if public_only and not claim.usable_in_public_copy:
                continue
            out.append(claim)
        return out

    # -----------------------------------------------------------------------
    # Auditing & Reporting
    # -----------------------------------------------------------------------

    def audit_trail(self, goal_id: str) -> dict:
        """Audits the evidence trail for a goal, verifying sources, claims, and compliance."""
        sources = self.list_sources(goal_id)
        claims = self.list_claims(goal_id)

        source_by_id = {s.id: s for s in sources if s.id}
        source_by_url = {s.url: s for s in sources if s.url}

        conf_dist = {tier: 0 for tier in CONFIDENCE_TIERS}
        status_dist = {st: 0 for st in VERIFICATION_STATUSES}
        type_dist = {st: 0 for st in SOURCE_TYPES}

        flagged_needs_review = []
        unlinked_claims = []
        unverified_claims = []
        speculative_claims = []
        public_claims = []
        audit_trail_pairs = []

        for src in sources:
            type_dist[src.source_type] = type_dist.get(src.source_type, 0) + 1

        for c in claims:
            conf_dist[c.confidence] = conf_dist.get(c.confidence, 0) + 1
            status_dist[c.verification_status] = status_dist.get(c.verification_status, 0) + 1

            if c.needs_human_review:
                flagged_needs_review.append(c)

            if c.verification_status == "unverified":
                unverified_claims.append(c)

            if c.confidence == "speculative":
                speculative_claims.append(c)

            if c.usable_in_public_copy:
                public_claims.append(c)

            linked_src = None
            if c.source_id and c.source_id in source_by_id:
                linked_src = source_by_id[c.source_id]
            elif c.source_url and c.source_url in source_by_url:
                linked_src = source_by_url[c.source_url]

            if not linked_src and not c.source_url:
                unlinked_claims.append(c)

            audit_trail_pairs.append({
                "claim_id": c.id,
                "claim": c.extracted_claim,
                "confidence": c.confidence,
                "status": c.verification_status,
                "public_ready": c.usable_in_public_copy,
                "needs_review": c.needs_human_review,
                "source_title": linked_src.title if linked_src else c.source_title,
                "source_url": linked_src.url if linked_src else c.source_url,
                "source_type": linked_src.source_type if linked_src else c.source_type,
                "agent": c.agent,
            })

        has_integrity_gap = len(unlinked_claims) > 0
        total_claims = len(claims)
        verified_pct = (status_dist.get("verified", 0) / total_claims * 100) if total_claims > 0 else 0.0

        return {
            "goal_id": goal_id,
            "total_sources": len(sources),
            "total_claims": total_claims,
            "sources_by_type": type_dist,
            "confidence_distribution": conf_dist,
            "verification_distribution": status_dist,
            "verified_percentage": round(verified_pct, 1),
            "public_claims_count": len(public_claims),
            "flagged_needs_review_count": len(flagged_needs_review),
            "unlinked_claims_count": len(unlinked_claims),
            "audit_trail": audit_trail_pairs,
            "integrity_passed": not has_integrity_gap,
        }

    def export_markdown(self, goal_id: str) -> str:
        """Exports an evidence ledger table in GitHub-Flavored Markdown."""
        audit = self.audit_trail(goal_id)
        claims = self.list_claims(goal_id)
        sources = self.list_sources(goal_id)

        lines = [
            f"# Research Evidence Ledger: Goal `{goal_id}`",
            "",
            f"- **Total Sources**: {audit['total_sources']}",
            f"- **Total Claims**: {audit['total_claims']}",
            f"- **Verified Claims**: {audit['verification_distribution'].get('verified', 0)} ({audit['verified_percentage']}%)",
            f"- **Public-Copy Approved**: {audit['public_claims_count']}",
            f"- **Flagged For Review**: {audit['flagged_needs_review_count']}",
            "",
            "## Sourced Claims Table",
            "",
            "| Claim | Source / URL | Type | Conf | Status | Public? | Review? | Agent |",
            "|---|---|---|---|---|---|---|---|",
        ]

        for c in claims:
            src_text = c.source_title or "Source"
            if c.source_url:
                src_link = f"[{src_text}]({c.source_url})"
            else:
                src_link = src_text
            
            pub_mark = "✓ Yes" if c.usable_in_public_copy else "No"
            rev_mark = "⚠️ Required" if c.needs_human_review else "Clear"
            claim_escaped = c.extracted_claim.replace("|", "\\|")
            
            lines.append(
                f"| {claim_escaped} | {src_link} | {c.source_type} | `{c.confidence}` | `{c.verification_status}` | {pub_mark} | {rev_mark} | {c.agent} |"
            )

        if sources:
            lines.extend([
                "",
                "## Registered Sources Manifest",
                "",
                "| Title | Source Type | Reliability | URL | Ingested By |",
                "|---|---|---|---|---|",
            ])
            for s in sources:
                lines.append(f"| {s.title} | {s.source_type} | {s.reliability} | [{s.url}]({s.url}) | {s.agent} |")

        return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--pb-url", default=DEFAULT_PB_URL, help="PocketBase base URL")
    common.add_argument("--file-mode", action="store_true", help="Force file-backed JSON ledger instead of PocketBase")

    parser = argparse.ArgumentParser(
        description="FCP-7 Research Workbench source and claim ledger.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        parents=[common],
    )

    sub = parser.add_subparsers(dest="subcommand", required=True)

    # record-source
    p_src = sub.add_parser("record-source", parents=[common], help="Record a primary or secondary source")
    p_src.add_argument("--goal", required=True, help="Goal ID")
    p_src.add_argument("--url", required=True, help="Source URL (http/https/file)")
    p_src.add_argument("--title", required=True, help="Source title or publication name")
    p_src.add_argument("--type", default="primary", choices=SOURCE_TYPES, help="Source type (prefer primary)")
    p_src.add_argument("--reliability", default="high", choices=RELIABILITY_TIERS, help="Reliability assessment")
    p_src.add_argument("--author", default="", help="Author or publishing entity")
    p_src.add_argument("--agent", default="gem", help="Ingesting agent")
    p_src.add_argument("--notes", default="", help="Source evaluation notes")

    # record-claim
    p_clm = sub.add_parser("record-claim", parents=[common], help="Record an extracted claim with confidence and source linkage")
    p_clm.add_argument("--goal", required=True, help="Goal ID")
    p_clm.add_argument("--claim", required=True, help="Extracted claim text")
    p_clm.add_argument("--confidence", default="moderate", choices=CONFIDENCE_TIERS, help="Confidence tier")
    p_clm.add_argument("--status", default="unverified", choices=VERIFICATION_STATUSES, help="Verification status")
    p_clm.add_argument("--source-id", default="", help="PocketBase ID of linked research_source record")
    p_clm.add_argument("--url", default="", help="Direct source URL (required if public copy is set)")
    p_clm.add_argument("--title", default="", help="Source publication title")
    p_clm.add_argument("--source-type", default="primary", choices=SOURCE_TYPES, help="Source type")
    p_clm.add_argument("--quote", default="", help="Verbatim quote snippet supporting claim")
    p_clm.add_argument("--public", action="store_true", help="Usable in public copy (articles, sales assets, tech shorts)")
    p_clm.add_argument("--needs-review", action="store_true", help="Flag for explicit human review")
    p_clm.add_argument("--agent", default="gem", help="Extracting agent")
    p_clm.add_argument("--notes", default="", help="Contextual qualifiers or notes")

    # verify-claim
    p_ver = sub.add_parser("verify-claim", parents=[common], help="Update verification status of an existing claim")
    p_ver.add_argument("--claim-id", required=True, help="Claim record ID")
    p_ver.add_argument("--goal", default="", help="Goal ID (required if file-mode)")
    p_ver.add_argument("--status", required=True, choices=VERIFICATION_STATUSES, help="New verification status")
    p_ver.add_argument("--reviewer", default="gem", help="Reviewing agent or human")
    p_ver.add_argument("--notes", default="", help="Verification review notes")

    # list-claims
    p_lst = sub.add_parser("list-claims", parents=[common], help="List claims for a goal")
    p_lst.add_argument("--goal", required=True, help="Goal ID")
    p_lst.add_argument("--confidence", choices=CONFIDENCE_TIERS, help="Filter by confidence tier")
    p_lst.add_argument("--status", choices=VERIFICATION_STATUSES, help="Filter by verification status")
    p_lst.add_argument("--public-only", action="store_true", help="Only show public-copy ready claims")

    # list-sources
    p_lss = sub.add_parser("list-sources", parents=[common], help="List sources for a goal")
    p_lss.add_argument("--goal", required=True, help="Goal ID")

    # audit
    p_aud = sub.add_parser("audit", parents=[common], help="Audit the evidence trail and source discipline of a goal")
    p_aud.add_argument("--goal", required=True, help="Goal ID")
    p_aud.add_argument("--json", action="store_true", help="Output audit report as JSON")

    # export-markdown
    p_exp = sub.add_parser("export-markdown", parents=[common], help="Export an evidence ledger in Markdown format")
    p_exp.add_argument("--goal", required=True, help="Goal ID")
    p_exp.add_argument("--output", help="Optional output file path")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    client = ResearchLedgerClient(pb_url=args.pb_url, force_file=args.file_mode)

    try:
        if args.subcommand == "record-source":
            src = ResearchSource(
                goal_id=args.goal,
                url=args.url,
                title=args.title,
                source_type=args.type,
                reliability=args.reliability,
                author=args.author,
                agent=args.agent,
                notes=args.notes,
            )
            saved = client.record_source(src)
            print(f"[research-ledger] OK: Recorded source {saved.id or ''} - '{saved.title}'")

        elif args.subcommand == "record-claim":
            clm = ResearchClaim(
                goal_id=args.goal,
                extracted_claim=args.claim,
                confidence=args.confidence,
                verification_status=args.status,
                source_id=args.source_id,
                source_url=args.url,
                source_title=args.title,
                source_type=args.source_type,
                quote_snippet=args.quote,
                usable_in_public_copy=args.public,
                needs_human_review=args.needs_review,
                agent=args.agent,
                notes=args.notes,
            )
            saved = client.record_claim(clm)
            print(f"[research-ledger] OK: Recorded claim {saved.id or ''} [{saved.confidence.upper()} / {saved.verification_status}]")

        elif args.subcommand == "verify-claim":
            updates = {
                "verification_status": args.status,
                "reviewed_by": args.reviewer,
            }
            if args.notes:
                updates["notes"] = args.notes
            res = client.update_claim(args.claim_id, updates, goal_id=args.goal)
            print(f"[research-ledger] OK: Updated claim {args.claim_id} status to '{args.status}'")

        elif args.subcommand == "list-sources":
            sources = client.list_sources(args.goal)
            print(f"Sources for goal {args.goal} ({len(sources)} found):")
            for s in sources:
                print(f"- [{s.id or 'local'}] {s.title} ({s.source_type}, {s.reliability}) -> {s.url}")

        elif args.subcommand == "list-claims":
            claims = client.list_claims(
                args.goal,
                confidence=args.confidence,
                verification_status=args.status,
                public_only=args.public_only,
            )
            print(f"Claims for goal {args.goal} ({len(claims)} found):")
            for c in claims:
                flags = []
                if c.usable_in_public_copy:
                    flags.append("PUBLIC")
                if c.needs_human_review:
                    flags.append("REVIEW_NEEDED")
                flag_str = f" [{', '.join(flags)}]" if flags else ""
                print(f"- [{c.confidence[:4].upper()}|{c.verification_status[:5]}] {c.extracted_claim}{flag_str} (Source: {c.source_url or c.source_title or c.source_id})")

        elif args.subcommand == "audit":
            audit = client.audit_trail(args.goal)
            if args.json:
                print(json.dumps(audit, indent=2))
            else:
                print(f"=== RESEARCH EVIDENCE AUDIT FOR GOAL: {args.goal} ===")
                print(f"Total Sources: {audit['total_sources']}")
                print(f"Total Claims:  {audit['total_claims']}")
                print(f"Verification:  {audit['verification_distribution']} ({audit['verified_percentage']}% verified)")
                print(f"Confidence:    {audit['confidence_distribution']}")
                print(f"Public Ready:  {audit['public_claims_count']}")
                print(f"Needs Review:  {audit['flagged_needs_review_count']}")
                print(f"Integrity Gap: {'NONE (Auditable)' if audit['integrity_passed'] else 'FAIL (Unlinked claims found)'}")

        elif args.subcommand == "export-markdown":
            md = client.export_markdown(args.goal)
            if args.output:
                Path(args.output).write_text(md, encoding="utf-8")
                print(f"[research-ledger] Exported markdown evidence ledger to {args.output}")
            else:
                print(md)

    except ValidationError as ve:
        print(f"[research-ledger] VALIDATION ERROR: {ve}", file=sys.stderr)
        sys.exit(2)
    except Exception as exc:
        print(f"[research-ledger] ERROR: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
