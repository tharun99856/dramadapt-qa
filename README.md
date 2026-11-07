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
(parser rules and window definitions), `docs/solution_two_pages.md` (the submitted two-page doc, exported to
`DramAdapt_QA_solution.pdf` in this folder), `docs/solution_two_pager.md` (its expanded companion),
`docs/failure_log.md` (what went wrong during the build) and `docs/author_record.md` (what the author did,
decided, withdrew and left open).

**What to read, in order.**

1. **`DramAdapt_QA_solution.pdf` - the submitted deliverable, in this folder, not in `docs/`.** Two pages, and
   every number in it names the file it came from. Its source is `docs/solution_two_pages.md`, and
   `python scripts/make_pdf.py` rebuilds it and fails if the result grows past two pages.
2. **`DramAdapt_QA_walkthrough.mp4` - the optional walkthrough, also in this folder.** 2 min 36 s, 15 steps,
   captured from the live hosted app with a caption on every frame explaining what is on screen. Silent, so it
   can be voiced over without re-rendering. `scripts/capture_walkthrough.py` and `scripts/make_walkthrough.py`
   rebuild it; the capture only opens expanders and scrolls, so making it spends no model calls.
3. **https://dramadapt-app.streamlit.app/** - the live prototype, showing the real 174-flag run with the editor's
   approve / edit / dismiss pass on top of it.
4. This README - how to run the gate end to end, and the file-by-file index in "File structure" below.
5. `results/` - the raw outputs folder the brief asks for: every prompt, every raw response, the flags, and the
   measured token totals in `results/run_log.json`.
6. `docs/phase0_results.md` and `docs/failure_log.md` - what the validation said, and what broke on the way.

**Submitted by:** Tharun Rathod, roll number 23115034, branch EE, IIT Roorkee. Kuku AI Generalist
Assignment, Problem 3 (find your own problem). Solo author.

Repository: https://github.com/tharun99856/dramadapt-qa. Prototype: https://dramadapt-app.streamlit.app/.
The API key is not in it and never will be -
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
#    while those cells are empty this bounds the rate from text already in the repo. It is labelled
#    derived because it is not a measurement, and it writes calibration_derived.json, never
#    calibration.json - src/config.py only ever reads the hand-timed one:
python scripts/derive_rate.py

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
#    ... record accept / accept-but-modify / dismiss per flag, in the UI or in batch files:
python scripts/record_acceptance.py data/annotation/acceptance_batches/2026-11-07_relationship_batch1.tsv
#    ... a check the rule drops that the builder keeps goes in data/check_overrides.json; both stay
#        in scores.json, and no threshold moves to fit a decision (entry 28)
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

## Hosting the prototype

The UI is a single `app.py` at the repo root with a pinned `requirements.txt`, which is all Streamlit
Community Cloud needs. Roughly five minutes, and the URL it gives you is the prototype link the brief asks for.

**Done on 7 Nov 2026: https://dramadapt-app.streamlit.app/** (repo `tharun99856/dramadapt-qa`, branch `master`,
main file `app.py`). The steps below are what produced it, kept so the link can be rebuilt if it dies.

1. https://share.streamlit.io (or streamlit.cloud), sign in with the GitHub account that owns
   `tharun99856/dramadapt-qa`.
2. **New app** → Repository `tharun99856/dramadapt-qa`, Main file path `app.py`,
   Python `3.11` or newer. Leave the requirements path at the default `requirements.txt`.
3. Deploy. The first build installs streamlit, pandas, PyYAML and openai; the log shows it working.
4. Optional, only if the hosted app should make model calls: **Settings → Secrets**, add
   `GROQ_API_KEY = "gsk_..."`. `app.py` reads that into the environment on load. Never put a key in a
   repo file, public or private - the `.env` in this folder is git-ignored and stays on this machine.

What the hosted app does without any of that: it reads the committed `results/*_flags.json`, so a viewer
sees the real 174-flag run, the coverage gaps, the timing distribution and every suggestion, and can try
`timing` and `script`, which need no key. The three LLM checks fail loudly and say why.

Two limits worth knowing before you send the link. The cloud filesystem is ephemeral, so decisions made
there do not survive a redeploy - use **Export → decisions CSV** to keep them, and fill the real
`data/annotation/decisions.csv` locally. And the free community tier sleeps when nobody is on it, so the
first load after a gap takes a few seconds.

## The walkthrough video

**`DramAdapt_QA_walkthrough.mp4`, in this folder, next to the PDF.** 2 min 36 s, 15 steps, captured from
the live hosted app rather than a local checkout, so what is on screen is what a reviewer gets from the link.
It is silent and every frame carries a step chip and a caption explaining what is on screen, which means it can
be played muted in a review queue or voiced over later without re-rendering anything.

The steps, in order: the claim on one line, what the page does, why Telugu, why not Hindi, the summary numbers,
how to read them, the anatomy of one flag, the editor action, then one flag each from the register, script and
timing checks, the relationship sheet, the sidebar inputs, the run-checks panel and the export panel. It ends on
what is still open and on the NO-GO verdict.

To rebuild it: `python scripts/capture_walkthrough.py` (needs `selenium` and a local Chrome; writes PNGs and a
manifest into the git-ignored `scratch/walkthrough/`), then `python scripts/make_walkthrough.py` (needs `pillow`
and `imageio-ffmpeg`; writes the MP4 here). The capture only opens expanders and scrolls the page, so making the
video spends no model calls, writes no editor decisions, and never presses the button that would.

## File structure

128 tracked files. **The two submitted deliverables sit in this folder, not in `docs/`: the doc is
`DramAdapt_QA_solution.pdf` and the walkthrough is `DramAdapt_QA_walkthrough.mp4`**; everything else exists so a
reader can check a line of it. Nothing needed to re-run the gate is missing from the repository.

### Root

| File | What it is |
|---|---|
| `DramAdapt_QA_solution.pdf` | **the submitted two-page solution doc.** Built from `docs/solution_two_pages.md`, not hand-written. 2 pages, 152 KB |
| `DramAdapt_QA_walkthrough.mp4` | **the optional walkthrough.** 2 min 36 s, 15 captioned steps, captured from the live hosted app, silent so it can be voiced over. 4.5 MB |
| `README.md` | this file: what the gate does, how to run it end to end, where every number lives |
| `PRD.md` | requirements, the Phase 0 design, and §9 with the thresholds and the drop rule fixed *before* the run |
| `PRD_ADDENDUM_format_and_sample.md` | the screenplay input format, the window definitions and the sample plan |
| `app.py` | the Streamlit UI: the 174 flags, approve / edit / dismiss per flag, the register-sheet confirmation, CSV and report exports |
| `config.yaml` | everything that legitimately changes between runs: provider, model, `api_key_env: GROQ_API_KEY`, windows, and `syllables_per_second: null` until the rate is hand-timed |
| `requirements.txt` | four pinned packages (streamlit, pandas, PyYAML, openai); the rest is standard library |
| `.env.example` | the key template. `.env`, `.api_key` and `.streamlit/secrets.toml` are git-ignored and carry no key in this repo |
| `.gitignore` | the three key files, the Kuku input pack by name pattern, and the local scratch and build directories |
| `.streamlit/config.toml` | only what a hosted demo needs; everything a viewer sees is in `app.py` |

### `docs/` - what a reviewer reads

| File | What it is |
|---|---|
| `solution_two_pages.md` | the source of `DramAdapt_QA_solution.pdf` in the repository root, so the PDF is reproducible |
| `solution_two_pager.md` | the expanded companion: the same claims with the full reasoning |
| `author_record.md` | what was the author's alone, what the assistant and models did, what was withdrawn |
| `failure_log.md` | 30 numbered entries of what actually broke, with dates and how each was found |
| `phase0_results.md` | the scored Phase 0 result, rendered from `results/scores.json` |
| `phase0_results_timing_derived583.md` | the same scoring with timing re-priced at the derived rate |
| `category_audit.md` | whether the 100-line sample met its category minimums |
| `corpus_statistics.md` | slot, gap and delivery numbers measured from our own screenplay |
| `public_evidence.md` | the public sources for the problem statement; anything marked `UNVERIFIED` is not quotable |
| `model_probe.md` | the three models tried on Telugu and why `openai/gpt-oss-120b` was chosen |

### `src/` - the gate

| File | What it is |
|---|---|
| `src/parser.py` | pack-block screenplay format in, per-line records out. Tolerant of en dashes and small drift; never drops a block without reporting it |
| `src/corpus.py` | category rules, relationship sheet plus the editor overlay, context per line |
| `src/telugu.py` | akshara count (one per base letter, minus one per virama, so a conjunct counts once), duration estimate and letter-class shares per line |
| `src/batching.py` | scene batches that never split a sentence chain - request count scales with scenes, not lines |
| `src/checks/` | `meaning`, `relationship`, `naturalness` (LLM, per scene); `timing` and `script` (pure Python, zero requests) |
| `src/pipeline.py` | runs a chosen subset of checks and returns flags, per-line verdicts, summaries and honest errors |
| `src/report.py` | stable flag ids, editor decisions, run JSON, Markdown report |
| `src/metrics.py` | precision/recall per check, severity sweep, comparison at similar precision, acceptance rate, seeded recall |
| `src/runlog.py` | every request logged with tokens; cost only when `config.yaml` has prices. Anything not measured is written `measured: false` |
| `src/llm.py` | the OpenAI-compatible client, JSON validation and one retry. Malformed output is an error, never a silent pass |
| `src/prompting.py` | the prompts the three LLM checks share, including the register-sheet prefix and the `DRAFT - needs the builder's sign-off` warning |
| `src/flags.py` | the flag record every check returns; it holds no numeric model confidence, by PRD §8 |
| `src/sample.py` | loads the Phase 0 sample as parsed lines with the first-pass Telugu attached |
| `src/config.py` | reads `config.yaml`, resolves the key from environment / `.env` / `.api_key`, and refuses to guess a calibration |
| `src/console.py` | `force_utf8()`, the first statement in every `main()` on Windows |

### `scripts/` - in run order

| Script | What it is |
|---|---|
| `parse_corpus.py` | screenplay to `data/parsed/`, plus the validation report that proves nothing was dropped |
| `corpus_stats.py` | the numbers in `docs/corpus_statistics.md` |
| `select_sample.py` | the stratified 100-line sample, seed recorded in `results/selection_manifest.json` |
| `make_blind_sheet.py` | `data/annotation/blind_annotation.csv` in randomized order, with no QA output visible |
| `run_first_pass.py` | Step A: the machine Telugu draft, stored untouched |
| `run_baseline.py` | Step C: the generic single-prompt control |
| `run_structured.py` | Step C: the five checks. `--merge LABEL` re-prices one check without re-paying the others |
| `run_seeded.py` | Step E: injects the known errors from `data/seed_ops.yaml`. The checks have never been run on the result |
| `score.py` | Step D: precision/recall, the comparison at similar precision, acceptance rate, `checks_to_drop`, GO/NO-GO |
| `make_acceptance_sheet.py` | the 174-row acceptance sheet, every status `pending` |
| `record_acceptance.py` | writes a reviewer batch file into `decisions.csv`, and refuses to overwrite a flag that already carries a decision |
| `derive_rate.py` | bounds the speaking rate from text already in the repo, labels it derived, and writes `calibration_derived.json`, never `calibration.json` |
| `calibrate_rate.py` | turns the hand-timed `data/calibration_readings.csv` into `data/calibration.json` once those seconds exist |
| `run_qa.py` | the whole gate on a screenplay nobody has seen: `--input <file or folder>`, with or without `--telugu` |
| `make_pdf.py` | the submitted PDF, with the two-page guard and the type-size search |
| `capture_walkthrough.py` | optional, for the video only: drives the hosted app in headless Chrome and saves one PNG per step. Opens expanders and scrolls, never clicks, so it spends no model calls and writes no decisions. Needs `selenium` plus a local Chrome, neither of which the gate itself uses |
| `make_walkthrough.py` | optional, for the video only: burns the step chip and caption onto those PNGs and writes `DramAdapt_QA_walkthrough.mp4` here in the root. Needs `pillow` and `imageio-ffmpeg` (the latter carries the ffmpeg binary, so no separate install) |

### `data/` - inputs, rules and the human record

| Path | What it is |
|---|---|
| `screenplay/episode-001..006.txt` | the original 6-episode test screenplay, 184 dialogue lines, written by the author |
| `new_show_demo/episode-001.txt` | a second original episode the pipeline had never seen, for the rerun demo |
| `parsed/` | `corpus.csv`, `corpus.json`, `stats.json` and `validation_report.md`: the parse output and its audit |
| `alias_map.yaml` | speaker label as written to canonical character |
| `category_rules.yaml` | the transparent rules behind the sample categories |
| `selection_plan.yaml` | target 100 lines and the category minimums |
| `relationship_sheet.yaml` | the register and address sheet, part signed off. Saved flags quote the machine draft byte-for-byte, so repairs are deferred to one edit |
| `seed_ops.yaml` | the Step E error fragments |
| `format_drift_fixture.txt` | a screenplay in a drifted format, used by the parser tests |
| `telugu/` | `first_pass.json` (Step A from the API, `openai/gpt-oss-120b`, the draft that was annotated), `first_pass_alt.json` (the same draft from the comparison model `qwen/qwen3.8-27b`), `first_pass_seeded.json` (Step E input), `new_input_live.json` (the unseen episode's draft), `step_a_raw_response.json` (an earlier in-session draft imported with `--from-file` so it claims no tokens, kept as returned and unedited) |
| `annotation/` | `blind_annotation.csv` the ground truth (81 `needs_revision`, 19 acceptable, 83 rewrites), `blind_order.json` the randomization, `sample_lines.csv` / `.json` the lines behind it, `decisions.csv` all 174 flags with their status (34 decided), `acceptance_batches/` the three reviewer batch files with the reasons, `blind_annotation_README.md` how the sheet was filled |
| `calibration_readings.csv` | the ten lines to time by hand; `seconds_read_aloud` is still empty, which is why the rate is derived and not measured |
| `calibration_derived.json` | the derived bound (5.83 akshara/s), labelled derived |
| `check_overrides.json` | the human decision that keeps `relationship`, recorded beside the rule that drops it |

### `results/` - the raw outputs folder

| Artifact | What it is |
|---|---|
| `structured_flags.json`, `structured_run.json`, `structured_calls.jsonl`, `structured_report.md` | the scored run: 174 flags, every prompt and raw response, tokens request by request |
| `baseline_flags.json`, `baseline_run.json`, `baseline_calls.jsonl` | the generic control: 58 flags at 0.897 precision |
| `scores.json` | every headline number, with the withdrawn reading kept beside it as `recall_legacy_flagcount` |
| `run_log.json` | measured request and token totals for the whole experiment: 134 requests, 181,911 prompt, 129,851 completion, `null` dollars |
| `timing_derived583_*` and `scores_timing_derived583.json` | timing re-priced at the derived rate: 142 flags, 37 of them timing, decision unchanged |
| `demo_timing_uncalibrated_*` | timing alone over the 100-line sample at the provisional 3.5 (69 flags), which is what the UI demo shows |
| `qa_rehearsal_*` | the two no-model checks over all six episodes: 91 flags |
| `new_input_rehearsal_*` | the unseen episode with no draft at all: 0 flags, and it says so rather than calling the lines clean |
| `new_input_code_*` | the unseen episode with the draft Step A generated for it, through the no-model checks: 33 flags |
| `seeded_manifest.json` | the nine edits Step E would use. `structured_seeded_flags.json` does not exist, so nothing is scored against them |
| `selection_manifest.json` | the sample seed and the category minimums |

### `tests/`

| File | What it is |
|---|---|
| `run_tests.py` | 109 self-tests: windows, chains, akshara counts, batching, metrics, report ids |
| `run_ui_test.py` | 11 checks that drive the actual UI through `streamlit.testing.v1.AppTest` |
| `fixtures/telugu_stub.json` | a Telugu draft for the tests, so they need no key and no network |

Not in the repository on purpose: `.env`, `.api_key`, `.streamlit/secrets.toml` (the key never goes in a repo
file), `scratch/`, `build/`, `__pycache__/`, and Kuku's confidential input pack, which `.gitignore` excludes by
name pattern so a stray copy cannot be added by accident.

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

Two things it still cannot say. The acceptance pass is **34 of 174 flags graded** - the whole of `relationship`
(21, two batches) and the whole of `meaning` (13, one batch) - and 140 rows in `data/annotation/decisions.csv` are
still `pending`, so script, naturalness and timing have no acceptance number at all. And Step E has never been run
against the seeded draft. The naturalness
coverage gap that sat here - 16 lines two batches refused - is closed: all 100 lines are now judged, `naturalness`
went 40 → 49 flags and the gate's untouched lines 3 → 1, which is the only reason the numbers in this section
differ from the ones in entry 25. What it cost is in entry 26.

Both graded checks disagree with the arithmetic, in opposite directions. `relationship`: acceptance **10 of 21** (3 accept,
7 accept-but-modify, 11 dismiss) - 0.476 - where precision alone says 0.238, so `scripts/score.py` still names the
check for dropping and `data/check_overrides.json` records the decision to keep repairing it, over the full 21,
beside the rule's own output; the threshold was not moved to fit either. The 11 dismissals sort into five causes
and four of the five are repairable rules, not model noise: **four demanded an address term the English line never
had** ("Say it once more", "He bought them." - inserting one puts words in the actor's mouth), **two misread the
listener** (`E01-L017` and `E03-L010` are spoken *to* Caine and *to* Silas), **two blamed the line for what is
wrong in the sheet** (`నాన్నా` is correct for a daughter to her father; a constable's name + `గారు` is the natural
register), **two contradicted a register rule nobody had written down** (Edda uses `మీరు` and the honorific verb
with Joss, where the check demanded `నీవు`), and **one would have broken the meaning outright**: on `E03-L002` the
model offered "Meeku oka gaṇṭa undi" for "I have an hour", which says *you have an hour*. That last one is the
worst thing a QA gate can do, and it is confident about it. All seven accept-but-modify rows give one reason the
check cannot see at all: the register lives in the pronoun and the verb ending, not in the address term - Caine
uses `మీరు` with Edda where an aunt uses `నువ్వు`, and every fix it offered was rejected for prepending a title
instead.

`meaning`: acceptance **11 of 13** (1 accept, 10 accept-but-modify, 2 dismiss) - 0.846 - and the scorer's precision
for the same check is also 0.846 (11 of 13 flags), which is a coincidence and not a cross-check. The two rows each
side calls wrong are not the same two rows: the scorer says `E01-L015` and `E05-L026`, the reviewer dismissed
`E03-L030` and `E05-L026`. The split is my own chain rule - `src/metrics.py` credits a flag on a split-sentence
fragment when its partner line carries the instance, and `E03-L030` is the fragment the reviewer graded
`acceptable` on its own. What the batch really shows is that meaning's defect sits in the suggestion layer: ten of
13 flags named the right problem and a wrong fix, in four kinds - a fix still in Latin letters (`E02-L029`), a typo
(`నిలిచలేదు` for `నిలవలేదు`, `E04-L011`), a word that means something else (`ధైర్యంగా` is "boldly", not "a dare"),
and a fix in the wrong register for the speaker (`E02-L006`, `E05-L029`). The one flag accepted outright,
`E01-L015`, is a scorer false positive the reviewer found useful. Full text in `docs/phase0_results.md`; the
failures behind this run are entries 22 to 30.

## Still gated on the builder

- **Rate calibration (step 4).** `data/calibration_readings.csv` lists the ten lines and its
  `seconds_read_aloud` column is still empty, so `config.yaml` stays at `syllables_per_second: null` and the
  timing check refuses to run without an override. The `--rate 3.5` used in
  `results/demo_timing_uncalibrated_report.md` is a provisional number, labelled as one, and the report prints
  the overrun share next to the flag count so that "this check is shortlisting almost everything" is visible
  instead of impressive. Until those ten readings exist, timing's 50 false positives cannot be interpreted:
  18 of its 19 reviewer-confirmed overruns are found, which is the part that is already real.
- **What a rate in between does.** `python scripts/derive_rate.py` bounds the rate from text already in the
  repo - the reviewer's own `corrected_line` akshara divided by that line's slot - and the median is
  **5.83 akshara/s** over 83 lines, against the 3.5 the submitted run used and the 6.11 the draft itself
  demands. Re-pricing timing at 5.83 is free (no model calls) and lands at
  `results/timing_derived583_flags.json`: **37 flags instead of 69, precision 0.275 → 0.459, false positives
  50 → 20, and 16 of the reviewer's 19 timing instances instead of 18.** Whole-run precision 0.506 → 0.606
  with recall 0.544 → 0.532, and the decision is still NO-GO. That is a sensitivity check, not a calibration:
  a rate derived from corrected lines makes those lines fit by construction, and the reviewer graded the
  3.5 flag list, not this one, so `results/scores.json` keeps describing the run that was actually annotated.
- **Step D acceptance pass** in `app.py` - the builder's own approve / edit / dismiss decisions, which is
  what PRD §9 uses to drop a check. 34 of 174 are in: the whole of `relationship` and the whole of `meaning`,
  recorded from `data/annotation/acceptance_batches/2026-11-07_relationship_batch{1,2}.tsv` and
  `2026-11-07_meaning_batch1.tsv` by `scripts/record_acceptance.py`,
  which refuses to overwrite a flag that already carries a decision. 140 rows are still `pending`:
  script 22, naturalness 49, timing 69.
- **The sheet edit that is owed, and not yet paid.** The acceptance pass says `data/relationship_sheet.yaml` needs
  the Edda-to-Joss side of the register fork, `నాన్నా` as an expected address for a daughter to her father, and a
  rule that stops demanding an address term the English line never had. Editing that file rewrites the prompt
  prefix both `relationship` and `naturalness` quote, which entry 26 priced at 18 batches, so it goes in once,
  after the remaining batches - see entry 29.
- **One cell of the blind sheet was edited after the flags were seen.** Row `A067` (`E02-L026`) read `మీ నాన్న`
  where the signed-off Joss-to-Edda rule says `నీ నాన్న`; the reviewer directed the change and it is applied. It
  touches a `corrected_line`, not a `verdict` or an `error_types`, so no precision or recall figure moves - but
  the sheet was supposed to be filled before looking at any flag, and saying so is the honest part (entry 29).
- **Step E seeded errors.** Never run against the seeded draft; the numbers that used to be in
  `results/scores.json` came from the clean run and are withdrawn (entry 25). The report prints the command.
- **Still open:** first-hand viewing of released Telugu episodes and the rest of the register-standard
  sign-off (the two name spellings and the Joss-to-Edda address are decided as of 2026-11-07 and recorded in
  `data/relationship_sheet.yaml`). The two-page doc is done: `docs/solution_two_pages.md`, exported by
  `python scripts/make_pdf.py` to `DramAdapt_QA_solution.pdf` at the repository root (2 pages, and the script
  refuses to emit more). The **hosted prototype** is live at https://dramadapt-app.streamlit.app/ and the
  **walkthrough** is `DramAdapt_QA_walkthrough.mp4`, also at the repository root.
