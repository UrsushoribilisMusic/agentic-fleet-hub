# AFL documentation re-review — d37ad9a

Codi, 2026-11-04. Public main confirmed via GitHub API at d37ad9af2cd274ae9a9ce7c5a2c2e8e8fc0a3bb8; local checkout matches and was clean. Scope: changes since 4f60311, against the Stage One and Stage Two recommendations. Video revisions are a separate ongoing task.

## Outcome

Substantially improved and a stronger Stage One presentation. The judge guide, direct Meta call-site/receipt links, capability table, evidence index, historical banners, repaired negative-result language, deployment caveat and explicit repair stages address the bulk of the review. The revised diagrams were visually inspected. No new implementation failure found. Four documentation/evidence corrections remain before an unqualified consistency sign-off.

## Verification

Created a fresh Python 3.12 venv outside the repo and installed exactly backend/requirements-dev.txt. Ran `python -m pytest tests recal -q` with Modal token variables removed, MODAL_CONFIG_PATH pointing to an empty temporary config, and the optional private S03 artifact variable unset. Result: **213 passed, 8 skipped, 4 warnings, 131 subtests passed in 42.00s**. This independently reproduces the advertised counts with no Modal credentials. Dependency installation used the network; no new live model run or GPU window was initiated. This was not a fresh iOS build or paid-provider integration test.

Checked local Markdown file targets from README, ARCHITECTURE, evidence-index and repair handoff: no missing file targets. No project source or docs edited by this review.

## Remaining corrections, prioritized

### 1. README misattributes the filmed re-ask to Glimmer

README.md:44–45 says the answered re-ask is where SAM and Glimmer actually run. The currently published film's re-ask displays WORLD CHECK FAILED / no paper candidate. In backend/live_backend.py:362–370 that branch returns the retrieved passage **before** the Glimmer call at 372. A passage on screen does not prove Glimmer ran.

Suggested replacement: “The filmed re-ask returns the newly retrieved passage, while its world check remains unresolved. The separate provider receipt above proves a frame went through both SAM and Glimmer.”

Similarly, README.md:72 calls the Oct 28 receipted ROI mask the “filmed mask.” The receipt establishes a manually box-prompted integration run, not which mask appeared in the submission film. Say “the receipted integration mask” unless a film/frame/receipt binding is available.

The new request-path diagram correctly removes the invented identity stage and puts retrieval first, but should add SAM → no candidates → WORLD CHECK FAILED + passage, with only the candidates-present branch continuing to Glimmer. That directly explains the visible payoff.

### 2. Old coverage and geometry statements still contradict the new limits

- README.md:16–20, 85–95 and the coverage bullet still describe reliably recognizing when manuals do not answer. docs/submission.md:11–13 retains the same claim. Use “measures retrieval proximity and flags possible documentation gaps.” Preserve the two known near-misses on the accepted side.
- ARCHITECTURE.md:136–137 still calls the d=0.820 refusal a displaced-paper control. Replace with: “The paper-position question returned d=0.820 against the original corpus and was refused before segmentation; this is a retrieval control, not a visual paper-position result.”
- The exact submitted theme title is still not spelled out, though the field-technician fit is now substantially clearer. This is a minor presentation opportunity, not a newly established eligibility blocker.

### 3. Approval/deployment prose contradicts the corrected diagram

README.md:188–189 still says approving the passage re-versions the corpus. The diagram immediately above now correctly lists export, CPU staging, pin review and guarded activation.

Suggested replacement: “After human approval, we exported the passage, staged the new corpus, reviewed its pin and activated it. The same question then cited the new passage at distance 0.400.”

Keep that same wording in docs/submission.md. Human approval and the separate deployment steps are both part of the demonstrated process.

### 4. The after-distance needs its own public receipt

docs/evidence-index.md:30 links the 39-record pin and film as proof of 0.400. A corpus pin proves which data version is allowed; it does not contain a query, returned distance or cited text. The public before receipt is good. Add a sanitized after or comparison receipt containing the exact unchanged query, selected corpus, top chunk ID, actual distance, source and the relevant passage text/hash. Link that file directly. Use the existing real artifact; do not rerun inference or invent a fixture to present as a recorded result.

The stronger evidence index makes this missing link more apparent. This recommendation is about independently checking the stated number, not disputing the already observed repair.

## Minor cleanup, not a reason to delay video work

- The README model table's Spark Open route can say “Baseten-hosted open-weight model” as the evidence index already does. Keep offline Spark wording and the separate pen-presence provider distinct from the composed live /assist path.
- “SAM on Meta, the rest on Modal” is too broad when discussing the whole system: the phone, local robot, wiki backend and Baseten drafting have other homes. Prefer “demo inference uses Meta API and Modal; drafting uses hosted services; full customer hosting is a target.”
- Some index rows still cite the whole verification directory or a pin as proof of a broader claim. Prefer one specific dated receipt per claim when available.

No score increase for the film is claimed here. The repository is now much easier to assess; remaining repo work is a short consistency pass and one public evidence artifact. Preserve the honest limits and move the main effort to the video.
