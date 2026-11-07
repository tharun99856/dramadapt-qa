# DramAdapt QA — pre-dubbing quality gate for localized microdrama

**Two-page solution summary. 7 November 2026.** Tharun Rathod, roll number 23115034, branch EE, IIT
Roorkee - Kuku AI Generalist Assignment, Problem 3. **This file is the expanded companion**; the document
that is submitted is the two-page `docs/solution_two_pages.md`, exported to `docs/DramAdapt_QA_solution.pdf`
by `python scripts/make_pdf.py`. Build: `README.md`, code in `src/`, run artifacts in
`results/`, measured statistics in `docs/`. Companion: `PRD.md` (v2) and its addendum.

> **Status of the numbers below.** The prototype and the validation harness are built and tested, and
> the model runs are real: Step A, the unstructured baseline control and the structured checks all
> have token-level logs in `results/`. The human half is now done in part: **the 100-row blind annotation
> is complete and scored, and the decision it produces is NO-GO.** Still `PENDING` are the reviewer
> acceptance pass and the speaking-rate calibration; the register standard is **part signed off** (the
> Joss-to-Edda address form and the two name spellings are decided, the rest is not). Slots that depend on
> the open items are marked rather than filled with an estimate, because the estimate would be the one
> number this project exists to measure. Nothing here is a result until it has a file behind it.

## 1. Problem

AI localization can be grammatically correct and still wrong as drama: a threat becomes a request, a
daughter addresses her father like a stranger, a line takes twice as long to speak as the scene
allows. These errors are cheap to fix on a script and expensive to fix after voice generation.

Verified industry evidence, all independent of any confidential material:
- A FICCI-EY survey of Indian media and entertainment CXOs (December 2025) found **60% saying
  multi-language content generation at scale remains a challenge because of quality and consistency**
  (reported by MediaNews4U, March 2026). Industry-wide, not microdrama-specific.
- Kuku states AI is used across story development, visual production, post-production, dubbing and
  localisation, releasing **150+ shows a month** (Business Standard, October 2026), and its COO has
  said AI is used at every step of microdrama production **but creative inputs still need heavy human
  involvement** (MediaNews4U).
- Kuku offers content in Hindi, Tamil, Telugu, Malayalam, Kannada and Bengali. A competitor
  (KadhaiShorts, Tamil) was reported as still exploring dubbing and language adaptation.

The stronger evidence is ours to produce, and it is now measured: a native Telugu reviewer graded **81 of the
100 sampled lines as `needs_revision`** in a first-pass AI localization of an original screenplay, 19 as
acceptable, with their own Telugu for 83 of the 100. What that number is and is not: the 100 come from a
184-line screenplay and were drawn **stratified**, with minimums for short slots, address shifts, threats and
split sentences, so this is the error rate inside a deliberately risk-enriched sample and not a natural rate
for an unselected episode. It is one reviewer, one language, no inter-rater agreement, and the grades were
recorded after review of AI-drafted suggestions rather than written independently (see Disclosures). Full sheet
at `data/annotation/blind_annotation.csv`, arithmetic at `results/scores.json`.

## 2. What it is, and what it is not

One user: a Telugu localization editor. One step: reviewing localized dialogue before voice generation.
One output: a line-by-line report with evidence and a suggested correction per flag.

**DramAdapt's primary function is quality assurance, not translation generation.** The prototype can
produce a first-pass Telugu draft when none is supplied, solely so it is runnable and demonstrable
without a real localization pipeline. That output is labelled `machine first pass - stand-in` in the UI,
the report and the exported JSON. It does not dub, does not lip-sync, and does not auto-approve.

## 3. How it works

Five checks over a parsed screenplay, batched **by scene** so request count scales with scenes, not
lines.

| Check | Method | Why it is separated |
|---|---|---|
| Meaning preservation | LLM per scene; verdict `same / weakened / strengthened / reversed / missing` + one-line reason | A generic prompt averages this away. Split-sentence chains are judged as whole sentences, because Telugu is verb-final |
| Relationship & address | Python rules narrow which lines to ask about; LLM judges the Telugu against a relationship sheet the editor confirms | Honorific systems cannot be find-and-replaced. A register shift the sheet does not predict is a flag |
| Timing | **Python only, zero model calls.** akshara count ÷ speaking rate, against the line's own slot and the gap to the next line | Deterministic, free, and reproducible. The speaking rate is still a provisional 3.5 akshara/s override: `data/calibration_readings.csv` has its ten lines listed and `seconds_read_aloud` empty, so this is calibrated arithmetic waiting for hand-timed readings, not a validated rate |
| Cultural naturalness | LLM, **advisory only** - "possibly unnatural, human review recommended" | Never a score or a percentage. Reported and priced separately because it is the weakest check |
| Script form | **Python only, zero model calls.** Counts Unicode letters per line | Added after the live first pass returned 20 of 100 lines as Telugu words in Latin letters. A model sees a correct Telugu sentence there; a dubbing artist sees nothing readable |

The human is the final gate: approve, edit or dismiss, each logged with a timestamp. Outputs are a
Markdown report and a JSON run artifact containing the inputs, every prompt, every raw response, the
flags, the editor actions and the measured request/token/cost totals.

## 4. Why this problem, and not Problems 1 or 2

Chosen, not assigned - and the brief asks for the reasoning, so it is written down rather than implied.

- **It is where Kuku says the human work still is.** Their account is AI at every step of microdrama
  production but creative input still needing heavy human involvement, and 60% of Indian media CXOs
  name quality and consistency as what blocks multi-language content at scale (FICCI-EY, Dec 2025).
  Finding promos optimises the *selection* of moments from finished content; this works on the step
  that is still manual reading.
- **The errors are the irreversible kind.** A wrong promo is replaced the same afternoon. A threat
  that became a request, or a line that needs 2.9x its slot, is found after the voices exist and, for
  timing, after the picture is cut.
- **I can evaluate it honestly alone.** An AI lawyer needs statute-accurate answers checked by a
  lawyer, and a wrong answer hurts a stranger in real distress - a risk I cannot verify, only borrow.
  Promo quality needs ad-performance data I do not have. Telugu correctness I can judge myself: 100
  lines annotated blind is a real number, and the timing check is arithmetic.
- **It re-runs on anything.** `scripts/run_qa.py --input <file or folder>` takes a show nobody has
  seen and produces the same artifacts, priced from the run log - which is what the interview asks for.
  On a second original screenplay the parser read 34 lines with 0 unparsed blocks, Step A translated all
  34 for 3 requests, and the two checks that need no model raised 33 flags at zero requests
  (`results/new_input_code_*`). The three LLM checks there are still waiting on a token-budget day, and
  their one attempt was voided by the bug in failure log entry 21.

The alternative I said I would accept: if blind annotation says the first-pass Telugu is basically fine, this
should shrink to the timing check alone and stop pretending to need four LLM calls. That is why the project
has a GO/NO-GO gate instead of a demo. **It ran, and the answer was two-edged.** The premise for shrinking
failed - 81 of 100 lines are not basically fine - but the gate still returned **NO-GO**, because the
structured arm has to beat the unstructured control at similar precision on *typed* flags and it does not:
structured **0.506** flag precision over 174 flags against the control's **0.897** over 58, with no severity
cut of the structured arm reaching 0.897 (the best cut, high-severity only, reaches 0.536).

Where the failure actually sits became clear only after the arithmetic was fixed (failure log entry 25). On
issues, the control credits 109 of the reviewer's 158 and the structured arm 86. On lines, it is the other way
round: the structured arm put a flag on **80 of the 81** lines the reviewer marked, at 0.879 precision on the
lines it touched, while the control touched 52 of 81 at 0.897. One line, `E05-L003`, no check touched at all.
Per type, `script` found 22 of the reviewer's 24
with zero false positives and no model call, `timing` found 18 of 19, `naturalness` 31 of 58, `relationship`
5 of 11 and `meaning` 10 of 46. So the honest sentence is not "decomposition does not work": it is that this
gate is good at saying *which lines to re-read* and weak at saying *what is wrong with them*, and the criterion
pre-registered in §9 measures the second thing. The recorded decision stays NO-GO; it is not being relabelled
after the fact. `results/scores.json`, `docs/phase0_results.md`.

## 5. What is built and verified now

- **An original 6-episode screenplay, 184 dialogue lines** (`data/screenplay/`), written by the builder.
  It deliberately contains the hard cases: 1.2 s slots, sentences split across two speakers for timing,
  voice-over and off-screen lines, one label reused by two different characters in different episodes,
  and address terms that shift mid-episode.
- **Parser passing six acceptance tests plus a format-drift fixture** (`scripts/parse_corpus.py`,
  `data/format_drift_fixture.txt`): no block is dropped without file and line number, en-dash ranges
  and `Scene Start/End` headers parse, V.O./O.S. labels normalize.
- **Corpus statistics, ours rather than borrowed** (`docs/corpus_statistics.md`): median tight slot
  **2.6 s**, **10%** of lines under 1.5 s, median English delivery **3.18 words/s**, 3 chains,
  8 voice-over and 8 off-screen lines, 13 speaker labels resolving to 11 characters.
- **A stratified 100-line sample**, seed `20261106`, all category minimums met, recorded in
  `results/selection_manifest.json` and `docs/category_audit.md`.
- **109 self-tests passing** (`tests/run_tests.py`) over windows, chains, akshara counts, scene
  batching, script detection, precision/recall, the severity sweep, acceptance-rate arithmetic, that a
  model's refusal is counted as coverage rather than as a finding, that a refused scene does not
  discard the scenes that answered, that a report whose lines were never fed to a check cannot
  print a clean-coverage sentence, that a generated draft reaches the records the checks read, and that a
  `--merge` re-render cannot delete the record that a
  check was only partially judged, that a recall numerator and its denominator count the same kind of thing
  for both arms, and that a missing seeded artifact is refused instead of quietly scored against the clean run.
- **A working review UI** (`app.py`), exercised end-to-end under Streamlit's own test harness.
- **Step A run for real, twice.** 100 lines, 18 scene-batched requests per model, one fixed prompt,
  temperature 0, on a free-tier Groq key: `openai/gpt-oss-120b` (34,599 prompt / 21,137 completion
  tokens) and `qwen/qwen3.8-27b` (37,416 / 5,245). Only 9 of 100 lines agree between them, so the
  second model is a second opinion rather than a reroll. Tokens are actual; cost is `null`, because a
  free tier was never billed and we do not multiply a rate nobody charged.
- **Three measured findings.** (1) The default model returned **20 of 100 lines as Telugu words written
  in Latin letters** - e.g. `Meeru seal ki kooda layakaledu.` - which no translation prompt flags,
  because to a language model that *is* Telugu. This created check 5. (2) At a provisional
  3.5 akshara/s the timing check shortlists most of the draft - 69 flags over 66 of the 80 lines it
  could read, 82% of them past slot + 15% - so the first useful number is not the
  flag count but the overrun distribution: the report prints the median estimate/slot ratio and the
  share of lines over slot + 15% beside the count, because a check that flags everything selects
  nothing. Both readings are still open - the rate is uncalibrated, or a machine first pass really
  does overrun Telugu slots structurally - and the second would be the most useful thing here.
  `PENDING` the builder's ten hand-timed readings. (3) **The relationship check's 51 flags were 21
  problems and 30 refusals.** The prompt offers `unknown` as a verdict, the code mapped anything it did
  not recognise to a low-severity flag, and 59% of that check's output was the model saying it had no
  basis - usually *"the sheet has no row for this pair"*, because a screenplay block never records who
  is being addressed. A refusal is now recorded as `lines_not_judged` and printed as a coverage gap,
  never as a flag and never as a clean line; the same 100 lines and the same recorded responses now give
  **21 flags and 30 lines not judged**.

## 6. Failures

`docs/failure_log.md` is the full list, including the ones found only after a real key was wired in.
The one worth reading here: every model was given each line's slot length and told to fit it.
For `I set it down an hour ago.` - a 1.4 s slot - the default model returned
`నేను దాన్ని ఒక గంటకు ముందు పెట్టాను.`: **14 akshara, about 4.0 s**, and the comparison model returned
9 akshara, still over. Confident JSON, no note that the constraint was broken. Nothing about the
output *looks* wrong. Only measuring it shows it, which is the whole argument for a timing check that
runs in plain Python and costs nothing.

The worst failure was in the evaluation layer, and it is why the numbers above carry a re-annotation. While
presenting the blind sheet in blocks, the assistant fabricated the entire content of block 7: ten English
lines and ten Telugu drafts that exist in no file in this repository, shown as sheet rows A061-A070. The
reviewer graded them in good faith, and their verdicts landed on ten real rows they had never seen. It
surfaced 30 rows later, when a `corrected_line` could not describe its own English column; the check that
proved it is mechanical - re-read the transcript and test, per row, whether that row's real fields ever
appeared in anything shown. **90 of 100 passed; those ten failed.** The answers were cleared rather than
patched, because a severity earned on an invented sentence transfers to nothing, and kept at
`scratch/ghost_block7_answers.json`; the block was re-graded from the file through a presenter script that
reads the CSV, so row content cannot come from memory again. Three sheet-wide claims built from those ghost
rows are withdrawn, including the two examples that were going to argue nothing checks whether a Telugu word
exists - that limitation is now an argument with no evidenced row, and is not presented as a finding.
`docs/failure_log.md` entry 22, with entry 23 for the scorer that then crashed on the first run its own guard
had ever allowed, and entry 25 for the two things that only came out when the arithmetic was re-derived by hand
after the reviewer asked whether the sheet could be trusted: a recall formula whose denominator counted 210
things for a 158-issue sheet, which understated our own control arm, and a seeded-error block that had been
reading the *unseeded* run's flags all along because one artifact was missing and `or s_flags` answered for it.
Both made the submission look better than the evidence did, and neither was caught by the 91 tests that existed,
because each one fed the functions shapes the bug could not appear in.

A second one, because it is the kind of failure a submission normally hides: the builder asked for
`llama-3.1-8b-instant`, and that model was retired from Groq's free tier on 2026-08-16. It returned
404 `model_not_found`, and it is not in the account's model list. We could not benchmark the model
named in the assignment's own example, so the default is `openai/gpt-oss-120b` - a stronger model than
an 8B, which is the conservative direction for a first pass: if the checks still find this many
problems at that size, the problems are real.

## 7. Scale, cost, disclosure

**Language scaling.** The QA architecture is reusable across languages, but each language needs its own
relationship and register rules, its own segmentation logic (Telugu is verb-final; English clause order
is not), its own syllable proxy and speaking-rate calibration, and a fresh Phase 0 with a native
reviewer. The orchestration, report, human-control model and run log are shared.

**Cost is measured, not estimated.** For 100 lines in 18 scene batches: first pass one request per
scene; baseline one per scene; meaning, relationship and naturalness one per scene each; timing and
script form **zero**, because both count things instead of asking about them. Prompt tokens per request,
measured from the per-request logs in `results/`: unstructured baseline **535**; meaning **1,055**;
naturalness **1,055**; relationship **1,727**; first pass (Step A) **1,922**. So the generic one-prompt
control costs about **42%** of what the structured checks cost, and about half of what the cheapest
structured check costs — it is not handed the relationship sheet, the chain instruction, the speaker
history or the register standard. Any argument that structure pays for itself has to beat that gap, and
the acceptance rate plus the per-check precision is what decides it. The whole experiment so far cost
**134 requests, 181,911 prompt and 129,851 completion tokens**, and `null` dollars, because a free tier
that never billed us should not be reported as if it did. Seven of those requests bought findings we then
threw away (failure log entry 21) and eighteen bought a coverage gap closed at full price (entry 26); the
total is left to include both.

The binding constraint is budget, not speed: this free tier caps the model at **200,000 tokens per day**
and a full structured pass costs about **130,000** of them (meaning 35,571 + relationship 54,292 +
naturalness 39,750 over 18 batches each), so the account affords roughly **1.5 passes a day** - which is
why the runner replays a batch whose exact prompt is already in the call log rather than paying for it
twice, and why one refused scene now costs only that scene. The cap is a rolling window, not a wall:
naturalness first ended at **84 of 100 lines** because two ordinary 8-line batches refused 530 s and 600 s
of waiting while 16 others answered and a 73-token probe went through in the same minute. Re-running it the
next day closed that gap - **100 of 100 lines judged, 49 flags where the partial pass had 40** - and it is
worth recording what that cost, because the replay did not save us: signing the register standard had
changed one bracketed prefix inside the naturalness prompt, so none of the 18 batches matched the log and
all 18 were paid for again. Request totals and token totals per phase are
in `results/run_log.json` and `results/structured_run.json`.
`docs/public_evidence.md` lists current per-1M prices for both models, so a paid run is extrapolatable
from the tokens above.

**Tools used.** Python 3.13 stdlib; PyYAML; the OpenAI-compatible client against Groq's free tier;
Streamlit plus pandas for the review UI; `streamlit.testing.v1.AppTest` for exercising it. The
mistakes those tools made are in section 6 and `docs/failure_log.md`: a model returning the wrong
alphabet and a model ignoring a constraint it was handed; and, found by running the UI rather than
reading it, `AppTest` raising `StreamlitDuplicateElementKey` because two different timing problems on
one line had been given one id - which would have silently overwritten an editor's decision.

**Disclosures.** One Telugu evaluator (the builder, native-level), so no inter-rater agreement is claimed; and
their verdicts, which are the whole human half of this result, were recorded in batches inside a chat session
with an AI assistant, where a share of the grades and rewrites were drafted by the assistant and then reviewed,
changed or accepted by the reviewer. Every row carries the reviewer's approval, so the judgement on the sheet is
the reviewer's, but it is human-reviewed AI-suggested annotation rather than independent human annotation and
must not be read as the latter; 100 lines; one language pair; two model families, because one provider account
does not offer the model the assignment names as its example; test data is an original screenplay rather than any
production localization; and the Phase 0 result set is not yet complete. Two timing statistics in the
addendum were measured once from Kuku's confidential input pack and are **struck from this document**,
replaced by our own corpus numbers above.
