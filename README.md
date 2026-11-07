# DramAdapt QA

A pre-dubbing quality gate for localized microdrama dialogue. It reads an English screenplay and a
Telugu localized draft and returns a line-by-line list of likely problems: meaning drift, wrong form
of address, lines too long for their time slot, phrasing that may not sound natural, and text that is
Telugu but not in Telugu script. A human editor approves, edits or dismisses every flag.

**DramAdapt's primary function is quality assurance, not translation generation.** The prototype can
produce a first-pass Telugu draft when none is supplied, but that function exists only to make the
prototype runnable without access to a real localization pipeline. It is labelled
`machine first pass - stand-in` everywhere it appears. The tool does not dub, does not lip-sync, and
does not auto-approve anything.

Companion docs: `PRD.md` (requirements and the Phase 0 experiment), `PRD_ADDENDUM_format_and_sample.md`
(parser rules and window definitions), `docs/solution_two_pager.md` (the submission doc),
`docs/failure_log.md` (what went wrong during the build).

**Submitted by:** Tharun Rathod, roll number 23115034, branch EE, IIT Roorkee. Kuku AI Generalist
Assignment, Problem 3 (find your own problem). Solo author.

Repository: https://github.com/tharun99856/dramadapt-qa. The API key is not in it and never will be -
`src/config.py` reads `GROQ_API_KEY` from the environment or from a git-ignored `.env` in this folder,
and `.env.example` documents both. Without a key the tool still runs: `--checks timing,script` and
`--skip-step-a` need no model at all, which is how the new-input path is rehearsed.

---

## Data provenance

Every input in this repository is an original screenplay written by the builder: *The Lamp and the
Tide*, six episodes, 184 dialogue lines, in `data/screenplay/`. `data/new_show_demo/` is a second,
separate original episode that the pipeline has never seen before, kept so the new-input rerun
(`scripts/run_qa.py`) can be demonstrated rather than described. Nothing here comes from a third party
or from any confidential material, so the raw outputs - Telugu draft, prompts, responses, flags,
annotations - are all publishable as ordinary files.

`docs/public_evidence.md` holds the independently researched public sources for the problem statement.
Anything in it marked `UNVERIFIED` must not be quoted in the doc or the walkthrough.

## Install

Python 3.13. Only three third-party imports are used (`yaml`, `openai`, `streamlit`/`pandas` for the UI).

```bash
python -m pip install pyyaml openai streamlit pandas
```

Model access is configured in `config.yaml` (base URL, model, API key environment variable) so any
OpenAI-compatible provider can be swapped in. The key itself is never stored in the repo: put it in
`.env` at the repo root (`GROQ_API_KEY=gsk_...`), which `.gitignore` excludes; a real environment
variable overrides it, and the older `.api_key` file still works. Without a key the LLM
checks fail loudly and the report says so - see *Running without a key* below.

## Run order

```bash
# 1. parse the screenplay, validate it, and prove nothing was silently dropped
python scripts/parse_corpus.py

# 2. corpus statistics (slots, gaps, chains, English delivery rate)
python scripts/corpus_stats.py

# 3. stratified 100-line sample with the seed recorded, then the audit of category minimums
python scripts/select_sample.py

# 4. calibrate the Telugu speaking rate - the timing check refuses to guess without it
python scripts/calibrate_rate.py --template    # writes 12 lines to time aloud
#    ... read them at the show's pace, put the seconds in column 3 ...
python scripts/calibrate_rate.py               # writes data/calibration.json

# 5. Step A: first-pass Telugu for all 100 lines, one fixed prompt, output stored untouched
python scripts/run_first_pass.py            # add --compare to run config.yaml's second model too

# 6. Step B: blind annotation sheet, randomized order, no QA output visible yet
python scripts/make_blind_sheet.py
#    ... fill in data/annotation/blind_annotation.csv BEFORE looking at any flag ...

# 7. Step C: the generic single-prompt control, then the structured checks
python scripts/run_baseline.py
python scripts/run_structured.py --label structured
#    after calibrating the rate, re-price timing alone - --merge keeps the flags of the checks you
#    are not re-running, and the label's run log is cumulative, so tokens are never counted twice:
python scripts/run_structured.py --checks timing,script --rate 4.2 --merge structured --label structured

# 8. Step D: scoring, the comparison at similar precision, acceptance rate, GO/NO-GO
python scripts/make_acceptance_sheet.py --flags results/structured_flags.json
#    ... record accept / accept-but-modify / dismiss per flag, or use the UI ...
python scripts/score.py

# 9. Step E: seeded errors, reported separately by type
python scripts/run_seeded.py && python scripts/run_structured.py \
    --telugu-file data/telugu/first_pass_seeded.json --label structured_seeded

# 10. the review UI
streamlit run app.py

# 11. the same gate on a screenplay nobody has seen before (the interview rerun case):
#     a file or a folder, with their Telugu draft or without one
python scripts/run_qa.py --input /path/to/new_show/ep1.txt --telugu their_draft.json
python scripts/run_qa.py --input /path/to/new_show --telugu their_draft.json --label new_input

#     and the forms of that path that have actually been run on this machine. --rate is a
#     placeholder: config.yaml has syllables_per_second: null until the builder times ten lines, and
#     the artifact records the rate as an uncalibrated command-line override. --skip-step-a refuses
#     to generate a first pass, so a rehearsal that must not spend cannot start Step A by accident.
#     The new-input rows above come from the last command here: the draft Step A generated for the
#     unseen episode, run through the two checks that need no model.
python scripts/run_qa.py --input data/new_show_demo --skip-step-a --checks timing,script \
    --label new_input_rehearsal --rate 3.5
python scripts/run_qa.py --input data/screenplay --telugu data/telugu/first_pass.json \
    --checks timing,script --label qa_rehearsal --rate 3.5

python scripts/run_qa.py --input data/new_show_demo --telugu data/telugu/new_input_live.json \
    --checks timing,script --skip-step-a --label new_input_code --rate 3.5

# self-tests: windows, chains, akshara counts, batching, metrics
python tests/run_tests.py

# the UI itself, driven through Streamlit's test harness (needs one results/*_flags.json)
python tests/run_ui_test.py

# the submitted two-page PDF, from docs/solution_two_pages.md (needs pandoc + Chrome; fails if it
# runs past two pages rather than shrinking the font)
python scripts/make_pdf.py
```

## What each part does

| Path | Role |
|---|---|
| `src/parser.py` | pack-block screenplay format in, per-line records out. Tolerant of en dashes and small drift; never drops a block without reporting it |
| `src/corpus.py` | category rules, relationship sheet plus the editor overlay, context per line |
| `src/telugu.py` | akshara count (one per base letter, minus one per virama, so a conjunct counts once), duration estimate and letter-class shares per line |
| `src/batching.py` | scene batches that never split a sentence chain - request count scales with scenes, not lines |
| `src/checks/` | `meaning`, `relationship`, `naturalness` (LLM, per scene); `timing` and `script` (pure Python, zero requests) |
| `src/pipeline.py` | runs a chosen subset of checks and returns flags, per-line verdicts, summaries and honest errors |
| `src/report.py` | stable flag ids, editor decisions, run JSON, Markdown report |
| `src/metrics.py` | precision/recall per check, severity sweep, comparison at similar precision, acceptance rate, seeded recall |
| `src/runlog.py` | every request logged with tokens; cost only when `config.yaml` has prices |
| `app.py` | approve / edit / dismiss per flag, relationship sheet confirmation, exports |
| `docs/solution_two_pages.md` → `scripts/make_pdf.py` | the two-page doc that is actually submitted, and the build that fails if it grows past two pages |

## Honesty rules the code enforces

- **A short model answer is an error.** `require_coverage` raises if the model skips lines; the batch
  is recorded as failed rather than quietly scored as clean.
- **A check that did not run is not a clean pass.** `results/*_report.md` prints
  `Checks completed: 0 of 5 (failed: ...)` and refuses to call zero flags a pass.
- **A transliterated line cannot pass silently.** The script check counts letters rather than asking
  the model, because a Latin-alphabet Telugu line reads as correct to a language model and is
  unusable on a studio floor.
- **No invented cost.** If a Telugu draft was produced outside this pipeline, its provenance records
  `measured: false` and `request_count/tokens/cost: null`.
- **Timing refuses to guess.** No `data/calibration.json` and no `--rate` means the timing check stops.
- **No numeric confidence about Telugu correctness** is requested from the model or shown in the UI.
- **Nothing is auto-approved.** Every flag stays `pending` until an editor action, which is logged
  with a timestamp in `data/annotation/decisions.csv`.
- **Unconfirmed relationship rows are visibly unconfirmed** - the register standard carries its
  `DRAFT - needs the builder's sign-off` prefix into every prompt that uses it.

## Cost, measured

A free-tier Groq key is configured in `config.yaml` (`openai/gpt-oss-120b`, with
`qwen/qwen3.8-27b` as `telugu.comparison_model`). Pricing stays `null` in the config because a free
tier was never billed: the run log reports real tokens and `cost_usd: null`, not multiplied-out rates.

| Run | Requests | Prompt tokens | Completion tokens | What came back |
|---|---|---|---|---|
| Step A, default model | 18 | 34,599 | 21,137 | 100/100 lines, **20 with no Telugu letters** |
| Step A, comparison model | 18 | 37,416 | 5,245 | 100/100 lines, 0 with no Telugu letters |
| Baseline control (Step C) | 18 | 9,633 | 14,990 | 58 problems, 0 batches silent |
| Structured checks (Step C) | 73 | 88,128 | 80,891 | meaning 13, relationship 21 (+30 not judged), timing 69, naturalness 49 over 100 of 100 lines, script 22 |
| **New input:** Step A on an episode the pipeline had never seen | 3 | 4,812 | 3,789 | 34/34 lines, **9 with no Telugu letters** |
| **New input:** `timing` + `script` over that same draft | 0 | 0 | 0 | 24 timing flags (median slot ratio 2.34, 92% over tight+15%), 9 script-form flags |

Per-1M list prices exist for both models (`docs/public_evidence.md` item 8), so a paid run is
extrapolatable from these tokens - but the figures above are what this environment actually spent,
which is nothing.

**Read `results/run_log.json` by phase, not by aggregate.** That file keeps one block per label ever
written in this workspace, which includes the development labels (`dry_run_no_key`, `merge_test`,
`plumbing_check`, `smoke_timing`, `script_probe`, `drift_demo`) and the two zero-request rehearsals
(`new_input_rehearsal`, `qa_rehearsal`, `new_input_code`), so its `_aggregate` line is what this workshop
spent, not what the experiment costs. The four phases of record are `first_pass`, `first_pass_alt`,
`baseline` and `structured`; the two new-input rows are the interview-rerun case, priced separately
because they answer a different question: what the gate does to a screenplay it has no prior knowledge of.

**Throughput is the real limit, so the run is resumable.** A clean structured pass needs 54 model
requests (three of the five checks ask per scene; timing and script form ask nothing); this label logged
73, because naturalness was paid for twice - 19 requests for the pass that stopped at 84 lines, then 18
more to close the two refused batches. The free tier caps this model at **200,000 tokens
per day** and a full pass costs about **130,000** (meaning 35,571 + relationship 54,292 + naturalness
39,750, each over 18 batches), so on paper the account affords roughly 1.5 passes a
day. In practice the cap behaves like a rolling window rather than a wall: finishing naturalness, 16 of
18 batches answered and two ordinary 8-line batches stayed `429` through 530 s and 600 s of waiting,
while a 73-token probe in the same window went straight through. That is only survivable because of two
properties in the code. A refused batch costs only that batch: each LLM check catches the failure per
scene, keeps the scenes that answered, and reports the check as *partially judged* rather than completed
or clean. And a batch whose exact prompt is already in
`results/<label>_calls.jsonl` is replayed from the log instead of re-requested, so re-running a
half-finished label spends tokens only on what is missing - the retry that fixed 21 more lines reused 16
of 18 batches and paid for two. (`--fresh` forces every batch to be paid for
again; a replayed batch is not recorded again, so the run log counts every request exactly once).
`provider.reuse_logged_calls: false` turns the replay off for the whole configuration. Waits obey the
provider's own `retry-after` header, capped by `provider.max_wait_seconds_per_batch`, because a 398-second
hint answered with a 20-second sleep is a guaranteed second failure.

One caveat on that replay, learned by spending it: the key is the prompt **text**, not the batch. The
naturalness prompt quotes the register standard, and signing that standard off changed one bracketed
prefix, so all 18 naturalness batches looked new to the log. The re-run reported `reused 0` and cost
18,985 prompt and 20,765 completion tokens - the price of the two missing lines being every line. Editing
`data/relationship_sheet.yaml` re-prices naturalness and relationship together, and nothing in the tool
warns you first. Failure log entry 26.

## What Step D said

The 100 blind rows are graded, so `scripts/score.py` ran against a complete sheet for the first time. From
`results/scores.json`, against the 81 lines the reviewer called `needs_revision`, which carry 158 typed issues:

| arm | flags | flag precision | reviewer issues credited | of the lines it touched, how many were real | of the 81 issue lines, how many got a flag |
|---|---|---|---|---|---|
| structured, five checks | 174 | 0.506 | 86/158 = 0.544 | 80/91 = 0.879 | 80/81 = 0.988 |
| unstructured baseline control | 58 | 0.897 | 109/158 = 0.690 | 52/58 = 0.897 | 52/81 = 0.642 |

**Decision: NO-GO**, unchanged, failing the same pre-registered rule: the structured arm must beat the baseline
at similar precision on typed flags, and no severity cut of it reaches 0.897 (high-only gets to 0.536).

What the corrected reading adds is where the failure actually is. The gate is good at choosing which lines to
look at and weak at naming what is wrong with them. It put a flag on 80 of the 81 lines the reviewer marked -
`E05-L003` is the only line no check touched - and 88% of the lines it touched were real problems,
against a baseline that touches fewer lines at 90%. But its typed flags name the right type far less often:
`timing` found 18 of the reviewer's 19 timing issues and 50 of its 69 flags sat on lines the reviewer did not
call a timing problem; `script` found 22 of 24 with zero false positives and no model call at all; `naturalness`
found 31 of 58 at 0.633 precision; `meaning` found 10 of 46. The one timing miss is `E03-L011`, a line the model
left in Latin script, so there are no akshara to count. The two script misses are the ones only a reader can see.

Two numbers in this section were wrong before they were fixed, and both are failure log entry 25. Recall was
flags over a mixed denominator, which understated the baseline badly (0.248 reported, 0.690 actual) and made the
arms uncomparable; and `seeded_errors` was scored against the *unseeded* run, because a missing artifact fell
back silently, so "timing 1 of 2 detected" described a draft that never contained the seeded errors. Both are
fixed in `src/metrics.py`, pinned by new tests (109 self-tests), and `results/scores.json` keeps the old reading
beside the new one as `recall_legacy_flagcount` instead of replacing it quietly.

Two things it still cannot say. The acceptance pass has not been run, so `checks_to_drop: ["relationship"]` is
arithmetic rather than the decision PRD §9 asks for; checked directly, 0 of that check's 16 false positives are
refusals, so the number rests on precision alone and not on the model hedging. And Step E has never been run
against the seeded draft. The naturalness coverage gap that sat here - 16 lines two batches refused - is closed:
all 100 lines are now judged, `naturalness` went 40 → 49 flags and the gate's untouched lines 3 → 1, which is
the only reason the numbers in this section differ from the ones in entry 25. What it cost is in entry 26.
Full text in `docs/phase0_results.md`; the failures behind this run are entries 22 to 26.

## Still gated on the builder

- **Rate calibration (step 4).** `data/calibration_readings.csv` lists the ten lines and its
  `seconds_read_aloud` column is still empty, so `config.yaml` stays at `syllables_per_second: null` and the
  timing check refuses to run without an override. The `--rate 3.5` used in
  `results/demo_timing_uncalibrated_report.md` is a provisional number, labelled as one, and the report prints
  the overrun share next to the flag count so that "this check is shortlisting almost everything" is visible
  instead of impressive. Until those ten readings exist, timing's 50 false positives cannot be interpreted:
  18 of its 19 reviewer-confirmed overruns are found, which is the part that is already real.
- **Step D acceptance pass** in `app.py` - the builder's own approve / edit / dismiss decisions, which is
  what PRD §9 uses to drop a check. Until they exist, `checks_to_drop: ["relationship"]` is arithmetic.
- **Step E seeded errors.** Never run against the seeded draft; the numbers that used to be in
  `results/scores.json` came from the clean run and are withdrawn (entry 25). The report prints the command.
- **Still open:** first-hand viewing of released Telugu episodes, the rest of the register-standard
  sign-off (the two name spellings and the Joss-to-Edda address are decided as of 2026-11-07 and recorded in
  `data/relationship_sheet.yaml`), the **hosted prototype link** and the walkthrough. The two-page doc is done:
  `docs/solution_two_pages.md`, exported by `python scripts/make_pdf.py` to
  `docs/DramAdapt_QA_solution.pdf` (2 pages, and the script refuses to emit more).
