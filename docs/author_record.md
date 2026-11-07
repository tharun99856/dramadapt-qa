# What I did - a record for the submission

**Tharun Rathod, roll number 23115034, branch EE, IIT Roorkee. Kuku AI Generalist Assignment, Problem 3,
DramAdapt QA.** Written 7 November 2026. Every line below is backed by a file in this repository; where a claim
has no file behind it, it says so instead of estimating.

## The short version

I chose the problem, wrote the PRD and its pre-registered decision rule, wrote the 6-episode test screenplay,
built the harness, ran every model call, did the Telugu evaluation myself, and made the human decisions the
metrics could not make. The gate returned NO-GO against its own rule and I submitted it anyway, with the numbers
that say so on disk. Two of the three things I promised to measure are still unmeasured, and they are marked as
unmeasured in the submitted document rather than filled with an estimate.

## What was mine alone

- **The problem and the PRD.** `PRD.md` v2 plus `PRD_ADDENDUM_format_and_sample.md`. §9 fixes the thresholds and
  the GO/NO-GO rule *before* the run, so the arithmetic could not be moved afterwards. When the reviewer decision
  and the rule disagreed, both were kept visible: `scripts/score.py` still emits `checks_to_drop:
  ["relationship"]` and `data/check_overrides.json` records the keep decision next to it.
- **The test data.** `data/screenplay/` - *The Lamp and the Tide*, 6 episodes, 184 dialogue lines, written by
  me, with the hard cases put in on purpose: 1.2 s slots, sentences split across two speakers, voice-over and
  off-screen lines, one speaker label reused by two different characters. `data/new_show_demo/` is a second,
  separate original episode the pipeline has never seen, kept so the new-input rerun can be demonstrated.
- **The Telugu evaluation.** I am the single evaluator. 100 sampled lines graded in `data/annotation/
  blind_annotation.csv`: 81 `needs_revision`, 19 acceptable, and **83 lines I rewrote in my own Telugu**. That
  file is the ground truth every precision and recall number is measured against.
- **The acceptance pass.** 34 of the 174 flags decided by me - all 21 `relationship` and all 13 `meaning` - as
  accept / accept-but-modify / dismiss, each with a written reason, in `data/annotation/acceptance_batches/` and
  `data/annotation/decisions.csv`. This is what PRD §9 uses to drop a check.
- **The register standard.** `data/relationship_sheet.yaml`: Joss addresses Edda with `నువ్వు` throughout, and the
  కేన్ / హల్లొరాన్ spellings are decided and signed off as of 2026-11-07. The rest is deliberately left as a draft.
- **Two decisions against the arithmetic.** Keeping `relationship` (acceptance 0.476 against precision 0.238,
  because my dismissals named five fixable causes rather than noise), and refusing to reprice `timing` as
  calibrated when the only rate available is derived from my own corrected lines.

## What the assistant and the models did

- The assistant wrote most of the harness with me directing it: parser, checks, metrics, scoring, the Streamlit
  UI, the PDF build. It caught some of its own errors and I caught others; `docs/failure_log.md` has 30 numbered
  entries and says which is which.
- The models produced everything labelled a finding or a suggestion: the first-pass Telugu (Step A), the
  baseline control, the three LLM checks, and every suggested correction. `openai/gpt-oss-120b` on Groq's free
  tier, temperature 0. Timing and script form are plain Python and cost zero model calls.
- **My verdicts were recorded against AI-drafted suggestions that I reviewed and accepted**, so the annotation is
  human-reviewed AI-suggested, not independent. That sentence is in `results/scores.json` and in the submitted
  two-page doc, not just here.

## Numbers I withdrew, and why

| Withdrawn | What replaced it |
|---|---|
| "timing 1 of 2 seeded errors detected" | Nothing. Step E has never been run; `results/scores.json` now says `Not measured` (entry 25) |
| A speaking rate of ~6.5 akshara/s | 5.83, *derived* from my own corrected lines against their slots, labelled derived, with `data/calibration.json` still absent (entry 27) |
| "28% acceptance for timing" | No such number. Timing has 0 of its 69 flags graded (entry 27) |
| Three sheet-wide claims built from a fabricated block | Re-graded against the CSV; the ten contaminated answers were cleared, not patched (entry 22) |
| Two timing statistics measured from Kuku's confidential input pack | Struck and replaced with corpus numbers from our own screenplay, which we can actually show (`docs/failure_log.md`, "Struck from the submitted documents") |

## The one thing that changes how to read the evaluation

While the blind sheet was being presented in blocks, the assistant invented the content of one block - ten English
lines and ten Telugu drafts that exist in no file - and I graded them in good faith; my verdicts landed on ten real
rows I had never seen. It surfaced 30 rows later and a mechanical audit returned 90 of 100. The ten answers were
cleared and the block was re-graded through a script that reads the CSV, so row content cannot come from memory
again. Entry 22, 25, 26.

One cell of the sheet was also edited after the flags had been seen: row `A067`, `మీ నాన్న` to `నీ నాన్న`, on my
instruction. It is a `corrected_line`, not a verdict, so no metric moves - but the sheet was meant to be filled
blind, and one row of it now knows what the QA arm said. Entry 29.

## Tools used, and one place they got it wrong

Python 3.13 stdlib + PyYAML, the OpenAI-compatible client against Groq's free tier, Streamlit + pandas for the UI,
`streamlit.testing.v1.AppTest` to drive it, pandoc + headless Chrome for the PDF, git for 10 commits across
2026-11-06 and 11-07 (the history is squashed, so it does not show the working sequence).

Where they got it wrong, the one I would tell an interviewer unprompted: **the assignment names
`llama-3.1-8b-instant` as an example model, and Groq retired it from the free tier on 2026-08-16** - 404
`model_not_found` on the first live call. I switched the default to a stronger model, which is the conservative
direction: if the checks still find this many problems at that size, the problems are real.

## Still open, stated as open

140 of 174 acceptance decisions (script 22, naturalness 49, timing 69); the ten hand-timed seconds that would turn
the derived rate into a measured one; Step E; the `relationship_sheet.yaml` repairs, deferred on purpose because
editing that file rewrites the prompt prefix two checks quote, which entry 26 priced at 18 re-paid batches. The
hosted prototype link and the walkthrough are mine to publish and are not in this repo yet.

**Time spent is not recorded here on purpose.** The git history is squashed to 10 commits on two dates and no
timer was kept, so any figure I wrote would be invented. Fill it in from your own notes if the submission needs
one.

## How to check any line above

```
python tests/run_tests.py                      # 109 self-tests
python scripts/score.py                        # regenerates results/scores.json and docs/phase0_results.md
python scripts/derive_rate.py                  # which rate numbers are derived and which measured
git log --date=short --pretty="%ad %h %s"      # the 10 commits
```
