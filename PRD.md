# DramAdapt QA — Product Requirements Document

**Version 2, 6 November 2026.** Kuku AI Generalist Assignment, Problem 3.
Supersedes v1. Companion: `PRD_ADDENDUM_format_and_sample.md`.

---

## 0. Change log from v1

Five issues raised in review, all fixed here.

| # | Issue in v1 | Fix |
|---|---|---|
| 1 | §10 proposed sharing confidential pack-derived files "through an unlisted link". Unlisted is still sharing. | Removed. The experiment no longer uses Kuku's input pack at all. Test data is an **original screenplay written by us** (`data/screenplay/`). Nothing pack-derived is committed or submitted. See §10. |
| 2 | Phase 0 (90 min) + Phase 1 (180 min) = 4.5 h before documentation, against a 2–3 h assignment. | Re-budgeted to **165–185 min total**, human evaluation protected, UI cut first. See §13. |
| 3 | Summary said "does not translate" while §5 kept a first-pass translation mode. | Stated plainly in §1 and §5: the first-pass function exists only to make the prototype independently runnable. |
| 4 | §11 claimed the checks "do not change" for a new language. Too broad. | Replaced with the architecture-reusable / per-language-rules-required wording in §11. |
| 5 | "3 to 4 calls per line" ≈ 300–400 calls for 100 lines, unmeasured. | Scene batching implemented in code; the run log records **actual** request counts, tokens and cost, and §11 reports those numbers instead of the guess. |
| + | Reviewer addition | **Reviewer acceptance rate** added as a Phase 0 and post-launch metric (§9, §6 Step D). Precision, recall and the baseline comparison are unchanged. |

---

## 1. Summary

DramAdapt QA is a **pre-dubbing quality gate** for localized microdrama dialogue. It takes an English screenplay and a Telugu localized draft and returns a line-by-line report of likely problems: meaning drift, wrong form of address, lines too long for their time slot, phrasing that may not sound natural, and Telugu written in the wrong alphabet. A human editor approves, edits or dismisses every flag.

**DramAdapt's primary function is quality assurance, not translation generation.** The prototype can produce a first-pass Telugu draft when none is supplied, but that function exists solely to make the prototype independently runnable and demonstrable without access to a real localization pipeline. It is labelled as a stand-in everywhere it appears and is not part of the product claim. The tool does not dub, does not lip-sync, and does not auto-approve anything.

One user: a Telugu localization or adaptation editor. One step: reviewing localized dialogue before voice generation or dubbing. One output: a line-by-line QA report with evidence and suggested corrections.

This PRD covers a validation experiment (Phase 0) and, only if it passes, a prototype (Phase 1). If Phase 0 fails, the fallback is the continuity auditor (§12).

## 2. Problem and evidence

AI localization can be grammatically correct and still wrong as drama. A threat becomes a request, a daughter addresses her father like a stranger, a line takes twice as long to speak as the scene allows. These errors are cheap to fix on a script and expensive to fix after voice generation or dubbing.

**Verified facts (only these go in the final doc):**

- A FICCI-EY survey of Indian media and entertainment CXOs (December 2025) found 60% saying multi-language content generation at scale remains a challenge because of quality and consistency issues (reported by MediaNews4U, March 2026). Industry-wide, not microdrama-specific.
- Kuku says AI is used across story and dialogue development, visual production, post-production, dubbing and localisation, and releases 150+ shows a month (Business Standard, October 2026).
- Kuku's COO has said AI is used at every step of microdrama production but creative inputs still need heavy human involvement (MediaNews4U).
- Kuku offers content in Hindi, Tamil, Telugu, Malayalam, Kannada and Bengali (India AI Impact Summit coverage, February 2026).
- KadhaiShorts, a Tamil microdrama app, was reported as still exploring dubbing, translation and language adaptation (NewsBytes summary of a Mint report).

**Public examples**, researched independently of any Kuku material, are logged in `docs/public_evidence.md` with a URL and access date per claim. They exist to show that localization-quality complaints in short-form drama are a public, observable phenomenon and not something we inferred from confidential files.

**Not verified, so do not cite:** the 80% and 53% FICCI-EY figures, the Hollywood Reporter India quote about AI dramatic language, the Mint slang and humour quote, the Animatic Media complaint counts, and anything in `docs/public_evidence.md` still marked UNVERIFIED.

**The evidence that is ours:** the natural error rate a native Telugu reviewer finds in a first-pass AI localization during Phase 0, measured on our own original screenplay. That number is the proof the problem is real.

**How the problem was observed, not assumed.** Two public lines of evidence, logged with URLs and access dates in `docs/public_evidence.md`: (a) the gap between a language label and a finished localization - AppGrowing's ad-intelligence read of the two biggest short-drama apps finds DramaBox carrying seven to eight dub language tags across at least 14 titles while ReelShort relies mainly on subtitle overlays with only three to four titles explicitly dubbed, and (b) a practitioner statement that treating localization as an afterthought "regularly produces subtitles that obscure faces, dialogue that feels stiff". No Telugu- or Tamil-specific complaint survives verification anywhere we could find, so we are not citing one, and first-hand viewing of released Telugu episodes is **still to be done by the builder** before the walkthrough claims it.

### 2.1 Why this problem rather than Problems 1 and 2

Chosen, not assigned. The brief asks for the reasoning, so here it is, with the limits.

1. **It is the step the industry itself says is still human.** Kuku's stated position is AI at every step of microdrama production but creative input needing heavy human involvement, and 60% of Indian media and entertainment CXOs name quality and consistency as the blocker for multi-language content at scale. Problem 1 optimises *selection* of moments from content that is already finished. This problem attacks the step where the labour actually is: someone fluent reading every localized line before voice generation exists.
2. **The errors here are the irreversible kind.** A wrong promo pick costs one underperforming ad and can be replaced the same afternoon. A threat that became a request in translation, a daughter using the wrong register to her father, or a line that needs twice its slot is discovered after the voices exist - and, if the timing is wrong, after the picture is locked. Same money spent, opposite recoverability.
3. **One person can evaluate it honestly, which is not true of the alternatives.** Problem 2 needs statute-accurate answers checked by a lawyer; a wrong answer hurts a stranger in real distress, and a solo student without legal access cannot verify correctness without becoming the liability. Problem 1's ground truth is ad performance and retention data we do not have. This problem's ground truth is Telugu, which the builder reads natively: 100 lines annotated blind is a number we can stand behind, and the timing check is arithmetic rather than opinion.
4. **It re-runs on any input, including at the interview.** Problem 3's input pack is optional, so everything here is our own screenplay and our own model calls. `scripts/run_qa.py --input <file or folder>` takes a show nobody has seen before and produces the same artifacts, priced from the run log. The rerun is demonstrated, not described. On a second original screenplay the parser read 34 lines with 0 unparsed blocks; Step A then produced a first pass for all 34 at 3 requests, 4,812 prompt and 3,789 completion tokens, and 9 of them came back in Latin script; the two checks that need no model then ran over that draft at zero requests and raised 33 flags - 24 timing (median slot ratio 2.34, 92% of what it could read past tight + 15%) and 9 script form (`results/new_input_code_*`, `results/new_input_rehearsal_*`). On the full corpus with the real draft attached the same zero-request path raised 91 flags (`results/qa_rehearsal_*`). The three LLM checks have produced no valid finding on genuinely unseen input: the one attempt that got model answers was voided by the attach bug in failure log entry 21. Nothing in the submission depends on material we cannot publish.

**What would change our mind:** if the blind annotation says the first-pass Telugu is basically fine, then a four-check gate is shortlisting noise and the honest answer is "keep the timing check, drop the rest". That is why §6 gates Phase 1 on Phase 0 instead of on enthusiasm.

## 3. Assumptions

1. The test scenario is English → Telugu. Kuku's COO has said Kuku regionalizes content in Indian languages rather than simply adapting English, so this is a reproducible test case, not a claim about Kuku's internal process.
2. Each dialogue line carries its own start and end time, so time windows are exact. Verified on our own screenplay; to be re-verified against a real episode format before any production use.
3. The period setting is preserved in translation: period-appropriate Telugu in the style of dubbing, not a modern or Indian-setting transposition. QA judges against that standard.
4. There is one native-level Telugu evaluator (the builder). No inter-rater agreement is claimed, and this is disclosed.
5. Kuku may already have internal localization QA. This is positioned as a focused, independently reproducible quality gate, not a claim that nobody has looked at the problem.
6. **All Phase 0 input data is original work by the builder.** No third-party or confidential material is used, so the raw outputs are publishable in full.

Open items to resolve first: calibrate the Telugu reading rate with 10 lines read aloud, and test two models on Telugu before choosing a default.

## 4. User and workflow

Primary user: a Telugu localization editor reviewing an AI-generated localized script.

1. **Frame** — the editor supplies the English screenplay, character relationships, scene context and intended emotion.
2. **Draft** — an existing model produces the Telugu draft, or the editor brings one.
3. **Refine** — the editor fixes the important lines.
4. **Check** — DramAdapt QA flags risky lines; the editor approves, edits or dismisses each flag.

## 5. Scope

**In scope:** parsing the screenplay and the localized draft, five checks, a line-by-line report, approve/edit/dismiss controls, JSON and Markdown export, model swap through configuration, and a first-pass localization mode used only when no draft is supplied.

**Out of scope:** a translation product, voice generation or dubbing, lip-sync, any language other than Telugu in this build, accounts, databases, auto-approval of any line, and numeric confidence about Telugu correctness.

The first-pass localization mode is a **demonstration dependency, not a feature promise**. Its output is labelled `machine first pass — stand-in` in the UI, the report, and the exported JSON.

## 6. Phase 0: validation experiment

**Time box: 60–70 minutes, mostly annotation time.** The annotation is the expensive part and is not cut.

**Data:** 100 dialogue lines from `data/screenplay/` (original, by the builder), each with episode, timestamp, speaker, English line, scene context, relationship and emotion. Selection is stratified with a recorded random seed — see the addendum §9.

- **Step A — first pass (10 min).** One LLM produces Telugu for all 100 lines with a single fixed prompt: preserve meaning and emotion, use natural conversational Telugu, preserve relationships and the period register, keep it short enough for the time slot. Save the output untouched, with the raw prompt and response.
- **Step B — blind human annotation (25–30 min).** Before seeing any QA output, with line order randomized, mark each line *acceptable* or *needs revision*. For each problem line record error type (meaning / relationship / timing / naturalness / script), severity, a corrected line and confidence. Use `data/annotation/blind_annotation.csv`. Script form is the one type a reviewer can judge instantly, which makes it the cleanest check of whether the automated flags agree with a human at all.
- **Step C — two systems, identical inputs, same model (10 min).** The baseline is one prompt asking whether the translation is accurate and natural and to list problems. DramAdapt runs the separate checks in §7.3. Both are priced from their own run log, so "cheaper" and "better" are never confused for each other.
- **Step D — scoring (10 min).** Score both against the annotations for precision, recall and false positives. Compare at similar precision — otherwise a system that flags everything wins on recall. Record **reviewer acceptance rate** per check: *accept flag and correction*, *accept flag but modify the correction*, *dismiss the flag*. Acceptance rate measures whether the tool is useful, not merely whether it can find differences.
- **Step E — seeded errors (5 min), kept separate from the main results.** Inject 10 known errors into a copy: 2 meaning reversals, 2 wrong register, 2 literal translations, 2 over-long lines, 2 character voice breaks. Report recall by type only, and say plainly that seeded errors are blunter than real ones.

**Decision thresholds (our own, not industry standards):**

- At least 10 of the 100 lines have genuine issues. Fewer means the problem is not visible enough.
- Structured QA recalls ≥50% of human-confirmed issues **and** beats the baseline at similar precision.
- False positives are counted by hand and reported. Naturalness precision is reported separately.
- Reviewer acceptance rate is reported per check. A check whose flags are almost always dismissed is dropped, even if its precision looks fine — it is not saving anyone time.
- If one check performs badly, drop that check, not the product.

**GO** → build Phase 1. **NO-GO** → switch to the continuity auditor.

## 7. Phase 1: product requirements

### 7.1 Inputs
- English screenplay file in the format in `data/screenplay/`, with a parser tolerant of small format differences. `scripts/run_qa.py --input <file or folder>` takes a show nobody has seen before and runs the whole gate on it, generating the first pass if no draft is supplied; `--skip-step-a` says so and spends nothing instead of silently generating, which is how the parse is rehearsed without touching the token budget.
- Optional Telugu localized draft. If absent, generate a first-pass draft with the configured model and label it as a stand-in.
- A relationship sheet (speaker, listener, expected register, optional notes), editable in the UI, pre-filled by the model and confirmed by the user.
- An alias map keyed by speaker label **and episode range**, because one label can be reused for different characters.

### 7.2 Parser (plain code)
Produces per line: episode, scene, speaker label as written and canonical, delivery tag, English text, Telugu text, tight and loose window in seconds, chain id, nearby action text, and flags for voice-over / off-screen / part of a chain. Malformed input produces a readable error message. The parser never silently drops a line — anything unparsed appears in a validation report with file name and line number. Rules and acceptance tests: addendum §7.

### 7.3 Checks
1. **Meaning preservation** (LLM, medium confidence). Compares English and Telugu and outputs `same / weakened / strengthened / reversed / missing` with a one-line reason. Split-sentence chains run as a whole chain, not fragment by fragment.
2. **Relationship and address** (rules plus LLM, medium confidence). Compares the line's register against the relationship sheet and the speaker's earlier lines; flags inconsistent honorifics or register shifts. No find-and-replace rules for Telugu honorifics. The sheet is keyed on a speaker-listener pair, and a screenplay block never records who is being addressed, so the scene's own rows are handed over and the model picks the pair. When it cannot - no row for the pair, addressee unidentifiable - the verdict is `unknown`, which is reported as a **line not judged**: neither flagged nor cleared. A verdict outside the enum is flagged as `outside_enum:<value>` so a contract break stays visible.
3. **Timing** (Python, high confidence for the estimate only). Estimated spoken duration is the akshara count (a syllable proxy from Unicode grapheme clusters) divided by a speaking rate calibrated by timing the editor reading 10 lines aloud. Flag when the estimate exceeds the tight window by a set margin (medium severity) or the loose window (high severity, "overlaps next line"). Windows and the 15% starting margin: addendum §8. The report states that windows describe the English performance, so a flag means risk, not failure.
4. **Cultural naturalness** (LLM, low confidence, advisory only). Wording is "possibly unnatural, human review recommended". Never a score or a percentage.
5. **Script form** (Python, high confidence). Counted Unicode letters, not asked: a line with no Telugu characters is flagged `not_in_telugu_script` (high — transliterated "Tenglish" is readable to a model and unreadable on a studio floor, and the timing check cannot measure it), and a line whose letter mass is ≥25% Latin is flagged `mixed_script` (medium — the draft is deciding loanword handling line by line instead of once). This check was not in the plan; it was added after the live Step A run returned 20 of 100 lines in Latin script (`docs/model_probe.md`). Zero model calls.

Only checks that survive Phase 0 are shown in the report.

### 7.4 Report
One row per flagged line: original line, localized line, context, check type, severity, evidence, suggested correction, and status (`pending / approved / edited / dismissed`). A summary bar shows lines reviewed, lines flagged, flags by check type, and acceptance rate by check.

### 7.5 Human control
Nothing is auto-approved. Every flag needs an editor action, and edits and dismissals are logged with timestamps.

### 7.6 Exports
JSON of the full run (inputs, prompts, raw model responses, flags, editor actions, request/token/cost totals) and a Markdown report.

## 8. AI and model layer

- One config file holds base URL, model name and an API key read from the environment. OpenAI-compatible client so any provider can be swapped in during the interview.
- Test two models on Telugu before choosing a default, because Telugu quality varies a lot between models.
- Dialogue is **batched by scene**, so the number of requests scales with scenes, not lines. All per-line accounting is still done per line.
- All model outputs are JSON and validated before display. Malformed output is retried once, then shown as an error. No fake success states; the user's work is never erased on failure.
- Every prompt and raw response is saved to the run folder, with measured request counts, prompt tokens, completion tokens and cost. This is the raw outputs deliverable and the source of the §11 cost figures.
- Prompts never ask for, and the UI never shows, numeric confidence about Telugu correctness.

## 9. Evaluation and quality checks

- Metrics per check: precision, recall, false-positive count, the baseline comparison at similar precision, and **reviewer acceptance rate** (accept / accept-but-modify / dismiss).
- The timing check is validated against hand-timed readings of 10 lines.
- A failure log is kept from the first run: missed issues, wrong flags, and one real example where an AI tool used during the build got something wrong (the brief asks for this).
- Disclosures: one evaluator, 100 lines, one language, one model family, and test data that is an original screenplay rather than any production localization.
- How we would know it worked with a real team: the share of flags editors accept, wrongly cleared lines that later surface in dubbing, editor review minutes per episode, and re-recordings avoided — all compared with a pre-tool baseline over a few episodes.

## 10. Data and confidentiality

**The Kuku input pack is not used for Phase 0, is not in this repository, and is not in the submitted raw outputs.**

- All experiment and demo inputs are original screenplays written by the builder. `data/screenplay/` is our own work and is safe to publish.
- The public demo ships with an excerpt of the same original screenplay, labelled as sample data.
- Raw outputs (English lines, first-pass Telugu, annotations, baseline results, structured results, seeded-error results, prompts, responses, run log) are all derived from our own screenplay, so they can be submitted as ordinary open links. **There is no unlisted-link workaround, because there is nothing confidential to work around.**
- Two aggregate timing statistics were measured once from the confidential pack during format discovery. They are **struck from this document** rather than quoted: Kuku has not approved citing even an aggregate, and our own corpus gives the same calibration context without the question (`docs/corpus_statistics.md`: median tight slot 2.6 s, 10% of lines under 1.5 s, median English delivery 3.18 words/s). The numbers themselves are not reproduced here, not even as "previously measured".
- `.gitignore` excludes any pack folder by name pattern so a stray copy cannot be committed by accident.

## 11. Scaling and cost

**Language scaling.** The overall QA architecture is reusable across languages, but each language requires specific relationship rules, linguistic validation, segmentation logic and timing calibration. Concretely, a new language needs: its own relationship and register rules (honorific systems are not transferable), its own segmentation logic (Telugu is verb-final; English clause order is not), its own akshara/syllable proxy and speaking-rate calibration, and a fresh Phase 0 run with a native reviewer for that language. The check *orchestration*, the report, the human-control model and the run log are shared.

**Cost.** Measured, not estimated. The run log records actual requests, prompt tokens, completion tokens and cost for each phase. Because dialogue is batched by scene, request count is set by scenes:

| Work | Requests for 100 lines (scene-batched) |
|---|---|
| First-pass Telugu (Step A) | one per scene, or one per sample block |
| Baseline QA (Step C) | one per scene |
| Structured QA: meaning | one per scene |
| Structured QA: relationship/address | one per scene (shared context) |
| Structured QA: naturalness | one per scene |
| Structured QA: timing | **zero** — pure Python |
| Structured QA: script form | **zero** — pure Python |

The v1 figure of "3–4 calls per line, ~300–400 calls" is gone. What the experiment actually spent, read
out of `results/run_log.json` after the real runs: **134 requests in total, 181,911 prompt tokens and
129,851 completion tokens** - Step A 18 requests per model (34,599/21,137 and 37,416/5,245), the baseline
control 18 (9,633/14,990), the structured pass 73 (88,128/80,891, which is naturalness paid for twice -
19 requests for the pass that stopped at 84 lines and 18 for the pass that finished it), and 7 on the
unseen episode: 3 for its own
Step A (4,812/3,789) plus 4 for an LLM-check pass that had to be thrown away (7,323/3,799) because the
generated draft was never attached to the run, which is failure log entry 21. That is 18 requests per LLM
check for 100
lines of structured QA - not 300-400 - and cost is `null` rather than a price because the
tier never billed us. The aggregate includes wasted calls on purpose: it is what the account spent. The two-page doc quotes the same file.

**Budget and resumption.** A free-tier key caps this model at 200,000 tokens per day and a full structured
pass spends about 130,000 of them, so the design assumes a run can be interrupted: waits obey
the provider's `retry-after` within `provider.max_wait_seconds_per_batch`, a refused scene keeps the
scenes that answered and is reported as *partially judged*, and a batch whose exact prompt is already in
the label's call log is replayed rather than re-requested (`--fresh` to force the request). Cost is
therefore not paid twice for the same **prompt text** - which is a weaker promise than it sounds, see below.

What the cap actually feels like is worth recording, because it is not a wall. Finishing naturalness this
afternoon: 16 of 18 batches were replayed or answered, and two 8-line batches - the median size, not the
largest - returned `still throttled (429 after 530s of waits)` and `(429 after 600s of waits)`, while a
73-token probe in the same window succeeded. A retry of just those two with the wait ceiling lowered to
90 s failed both again and spent nothing, because the other 16 came from the log. So the budget frees
token by token as the window rolls: whether a batch answers depends on when you ask, not how big it is.
The measured consequence was in the artifact - naturalness judged **84 of 100 lines**, the report saying
"2 of 18 batches refused; 84 lines judged, 16 not" and listing those 16 under *sat in a batch the model
never answered*, and 16 of the 18 naturalness batches never needing a second payment.

That gap is now closed: naturalness was re-run on 2026-11-07 and judges **100 of 100 lines**, 49 flags
where the partial pass reported 40. What it cost is the caveat on the paragraph above. The replay key is
the prompt *text*, and the naturalness prompt quotes the register standard - signing two decisions off
changed one bracketed prefix, so all 18 batches looked new and the run reported `reused 0` for
18,985 prompt and 20,765 completion tokens. Editing `data/relationship_sheet.yaml` silently re-prices
naturalness and relationship; entry 26.

**Human gate.** The human stays the final gate. The tool shortlists risky lines so editors read fewer lines, not zero.

## 12. Fallback and risks

**Fallback:** the continuity auditor — a fact ledger with speaker attribution and seeded contradictions, English only.

| Risk | Mitigation |
|---|---|
| LLM weakness in Telugu undermines the naturalness check | Keep it advisory; report its precision and acceptance rate separately. |
| A small model produces an unrealistically bad Telugu first pass, inflating the error rate | Run the first pass with two models and report both; disclose which model produced the annotated set. |
| Seeded errors flatter the results | Natural errors are the primary result; seeded results are reported separately by type. |
| One reviewer can be biased | Review blind and randomized; disclose. |
| Format may surprise us on a new show | Confirm the format first; keep the parser tolerant and unlogged drops impossible. |
| Kuku may already have this internally | Position honestly. |
| Time | Cut the UI before cutting the checks. |

## 13. Time budget

Total **165–185 minutes**, against an assignment of approximately 2–3 hours.

| Activity | Budget |
|---|---|
| Phase 0 validation experiment (§6) | 60–70 min |
| Phase 1 working prototype (§7) | 85–90 min |
| Testing and documentation | 20–25 min |
| **Total** | **165–185 min** |

Phase 1 build order inside its 85–90 min: parser → meaning + relationship checks → timing check → minimal report → evidence, suggestions and approve/edit/dismiss → run the 100 lines and compute metrics → save outputs and record the walkthrough.

**Cut order when time runs short: report styling, then UI polish, then the naturalness check. Never the blind annotation, never the baseline comparison.** A prettier UI that has not been checked against a human-annotated ground truth proves nothing.

## 14. Deliverables checklist

- Solution doc (2-page PDF): problem and evidence, assumptions, how it works, what Phase 0 found, failures, scale and cost.
- Prototype link: Streamlit or similar with our own sample screenplay, plus a GitHub repo with run steps.
- Raw outputs: original lines, first-pass Telugu, annotations, baseline results, DramAdapt results, seeded-error results, prompts and responses, run log with measured request/token/cost totals.
- Walkthrough video of up to 3 minutes in the builder's own voice.

## 15. Execution status at build time

Checked against §14 as of 6 November 2026. The detail lives in `README.md` and `docs/failure_log.md`.

| Deliverable | State |
|---|---|
| Original test data, 184 lines, hard cases included | done, `data/screenplay/` |
| Second original screenplay, one episode, unseen by the pipeline | done, `data/new_show_demo/` - parsed, given its own Step A first pass at 3 requests, and checked by `timing` and `script` at zero requests: 33 flags (`results/new_input_code_*`). No LLM check has produced a valid finding on it yet |
| Parser + six acceptance tests + format-drift fixture | done, all pass |
| Corpus statistics replacing the pack-derived ones | done, `docs/corpus_statistics.md` |
| Stratified 100-line sample, seed recorded, minimums met | done, seed `20261106` |
| Five checks + baseline control, scene-batched, run log | done and **run against a live model**; tokens measured, cost `null` because the tier is free |
| Step A first-pass Telugu, two models | done, 18 requests each, 100/100 coverage, 20 lines returned without Telugu script on the default model |
| Baseline control (Step C) | done: 18 requests, 9,633 prompt / 14,990 completion tokens, 58 problems reported |
| Structured run (Step C) | done: all five checks complete over all 100 lines - naturalness initially judged **84 of 100** and reported as partially judged (two 8-line batches stayed `429` through 530 s and 600 s of waiting and the 16 that answered were kept), then re-run on 2026-11-07 to **100 of 100**, 49 flags where the partial pass had 40. Timing ran on the same 100 lines but only at a **provisional 3.5 akshara/s passed on the command line** (69 flags, 82% of measured lines over their slot by more than 15%); with `config.yaml` still at `syllables_per_second: null` the check refuses to guess, so that list is a rehearsal of the arithmetic, not a calibrated finding |
| New-input rerun path | `scripts/run_qa.py --input <file or folder>`; `--merge` re-prices one check without paying for the others; a batch already in the call log is replayed instead of re-requested, and `--fresh` forces a real request. Rehearsed at zero requests and then run for real on unseen input, artifacts on disk; the LLM half still has no valid result there, and a run of it spends about a third of a day's token budget |
| Self-tests | 109 passing, plus `tests/run_ui_test.py` driving the UI under `AppTest`. Two of the new ones exist because of entry 25: they feed the metric functions shapes the bug could not hide in |
| Review UI with approve / edit / dismiss | done, exercised under `AppTest`. The earlier warning that the edit path could re-fire in a loop was wrong and is retracted: `apply_decisions` in `src/report.py:59-61` sets `edited = True` whenever an edited suggestion is non-empty, and `app.py:185` tests it |
| Two-page doc | **done, and two pages.** `docs/solution_two_pages.md` is the submitted text, `docs/DramAdapt_QA_solution.pdf` the export, `scripts/make_pdf.py` the build (it fails rather than emitting a third page). `docs/solution_two_pager.md` is kept as the expanded companion every figure in it points back to |
| Failure log | 26 numbered entries, seven of them found only after a real key was wired in; entry 22 is the assistant fabricating ten rows of the human evaluation, entry 24 is what Step D said when it finally ran, entry 25 is the two ways the scorer flattered the wrong arm and reported a seeded run that never happened, entry 26 is what closing the naturalness coverage gap actually cost |
| Rate calibration (open item) | **not done** - needs the builder to time ten lines aloud into `data/calibration_readings.csv`, whose `seconds_read_aloud` column is still empty |
| Register standard | **part signed off, 2026-11-07.** The reviewer set the Joss-to-Edda address to నువ్వు in every episode and fixed the name spellings at కేన్ and హల్లొరాన్; both are recorded in `data/relationship_sheet.yaml` as `reviewer_decisions` and printed into `docs/phase0_results.md` from that file, not pasted. The rest of `draft_paragraph` is still unconfirmed against the episodes, and the Step A draft column was deliberately not rewritten - see entry 22's rule about not editing evidence |
| Step E seeded errors | **not measured.** `results/structured_seeded_flags.json` has never existed; the numbers previously printed in `results/scores.json` came from the clean run and are withdrawn. The manifest has 9 edits and the command to run them is in the report |
| Step B blind annotation | **done** - 100/100 rows graded, 81 `needs_revision`, 19 `acceptable`, 83 own-Telugu rewrites. Rows 61-70 were re-annotated on 2026-11-07 after entry 22, and every one of the 100 rows is now audited as shown-verbatim-from-the-file (`scratch/audit_rows_shown.py`, 100/100). Provenance, stated because it changes the weight: the batches were recorded in a chat session and a share of the grades were reviewed from an AI draft rather than written first by the reviewer, so this is human-reviewed AI-suggested annotation, not independent human annotation, and no inter-rater claim is made |
| Step D scoring and the GO/NO-GO | **done, and it is NO-GO** - `results/scores.json`, `docs/phase0_results.md`, re-scored 2026-11-07 after the naturalness re-run. Structured 0.506 flag precision over 174 flags, 86/158 reviewer issues credited, 80/81 issue lines touched at 0.879 line precision; baseline control 0.897 over 58 flags, 109/158 issues, 52/81 lines. The comparison criterion fails because no severity cut of the structured arm reaches the baseline's typed-flag precision (high-only: 0.536). Recall is now instance-based; the withdrawn flag-over-mixed-count values are kept in the artifact as `recall_legacy_flagcount` (entry 25) |
| Step D acceptance pass | **not done** - the builder's own approve/dismiss decisions in `app.py`; until they exist, PRD §9's rule for dropping a check cannot be applied and `checks_to_drop: ["relationship"]` is arithmetic, not a decision |
| Walkthrough video | not done |

`scripts/score.py` refuses to run on an unfilled annotation sheet, so nothing in §6 can be marked
complete by an accident of tooling. That guard worked, and it also cost us: everything below it was
unreachable for the whole build, including one line with a name that had never existed (entry 23). The
scorer only compiled into real behaviour once the hundredth verdict was in.
