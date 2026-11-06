# DramAdapt QA — pre-dubbing quality gate for localized microdrama

**Two-page solution summary. 6 November 2026.** Build: `README.md`, code in `src/`, run artifacts in
`results/`, measured statistics in `docs/`. Companion: `PRD.md` (v2) and its addendum.

> **Status of the numbers below.** The prototype and the validation harness are built and tested, and
> the model runs are real: Step A, the unstructured baseline control and the structured checks all
> have token-level logs in `results/`. What is **not** done is the human half - Step B blind
> annotation, the acceptance pass, the speaking-rate calibration and therefore the GO/NO-GO decision.
> Every slot that depends on them is marked `PENDING` rather than filled with an estimate, because the
> estimate would be the one number this project exists to measure. Nothing here is a result until it
> has a file behind it.

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

The stronger evidence is ours to produce: **the natural error rate a native Telugu reviewer finds in a
first-pass AI localization of an original screenplay**, measured in Phase 0 Step B. That number is
`PENDING`, and it is the reason Phase 0 exists rather than a demo.

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
| Timing | **Python only, zero model calls.** akshara count ÷ speaking rate, against the line's own slot and the gap to the next line | Deterministic, free, and reproducible; validated against hand-timed readings |
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
  The rerun has been rehearsed on a second original episode and on the full corpus at zero requests
  (`results/new_input_rehearsal_*`, `results/qa_rehearsal_*`); the three LLM checks on unseen input are
  the part still waiting on a token-budget day.

The alternative I would accept: if blind annotation says the first-pass Telugu is basically fine, this
should shrink to the timing check alone and stop pretending to need four LLM calls. That is why the
project has a GO/NO-GO gate instead of a demo.

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
- **76 self-tests passing** (`tests/run_tests.py`) over windows, chains, akshara counts, scene
  batching, script detection, precision/recall, the severity sweep, acceptance-rate arithmetic, that a
  model's refusal is counted as coverage rather than as a finding, that a refused scene does not
  discard the scenes that answered, and that a report whose lines were never fed to a check cannot
  print a clean-coverage sentence.
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
naturalness **1,036**; relationship **1,727**; first pass (Step A) **1,922**. So the generic one-prompt
control costs about **40%** of what the structured checks cost, and about half of what the cheapest
structured check costs — it is not handed the relationship sheet, the chain instruction, the speaker
history or the register standard. Any argument that structure pays for itself has to beat that gap, and
the acceptance rate plus the per-check precision is what decides it. The whole experiment so far cost
**104 requests, 146,222 prompt and 96,982 completion tokens**, and `null` dollars, because a free tier
that never billed us should not be reported as if it did.

The binding constraint is budget, not speed: this free tier caps the model at **200,000 tokens per day**
and a full structured pass costs about **129,000** of them (meaning 35,571 + relationship 54,292 +
naturalness 38,984 over 18 batches each), so the account affords roughly **1.5 passes a day** - which is
why the runner replays a batch whose exact prompt is already in the call log rather than paying for it
twice, and why one refused scene now costs only that scene. Request totals and token totals per phase are
in `results/run_log.json` and `results/structured_run.json`.
`docs/public_evidence.md` lists current per-1M prices for both models, so a paid run is extrapolatable
from the tokens above.

**Tools used.** Python 3.13 stdlib; PyYAML; the OpenAI-compatible client against Groq's free tier;
Streamlit plus pandas for the review UI; `streamlit.testing.v1.AppTest` for exercising it. The
mistakes those tools made are in section 6 and `docs/failure_log.md`: a model returning the wrong
alphabet and a model ignoring a constraint it was handed; and, found by running the UI rather than
reading it, `AppTest` raising `StreamlitDuplicateElementKey` because two different timing problems on
one line had been given one id - which would have silently overwritten an editor's decision.

**Disclosures.** One evaluator (the builder, native-level Telugu), so no inter-rater agreement is
claimed; 100 lines; one language pair; two model families, because one provider account does not offer
the model the assignment names as its example; test data is an original screenplay rather than any
production localization; and the Phase 0 result set is not yet complete. Two timing statistics in the
addendum were measured once from Kuku's confidential input pack and are **struck from this document**,
replaced by our own corpus numbers above.
