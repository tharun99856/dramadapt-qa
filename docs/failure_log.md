# Failure log

Started on the first run, not after the demo. Every entry is something that actually happened during
the build, with how it was found. PRD section 9 asks for this; an interviewer asking "what broke?"
should get an answer with dates in it.

## Missed issues (the tool did not see what was there)

**1. The interlocked split sentence.** The chain detector originally only linked a fragment to the
next line from the *same* speaker. Episode 3 splits one sentence across two speakers - Haloran
"Say it as a promise, not a ..." then Edda "... a dare. I hear you, Father." The first corpus parse
found 2 chains where there were 3. Found by counting the ellipsis lines in the screenplay against the
parser's output, not by the parser telling me. Now `chain_kind="interlocked"`, and an orphan fragment
that has no partner produces a `fragment` warning instead of being dropped quietly.
*Why it matters:* a fragment-by-fragment translation of a verb-final language is guaranteed to be
wrong, so a check that cannot see the join cannot judge meaning either.

**2. Silent drops are still drops when they are warnings nobody reads.** The first version treated an
unquoted speaker block as dialogue, which inflated the line count. The rule in the addendum is that
dialogue is quoted; a block that breaks the rule is not dialogue and not a warning to ignore. Fixed by
excluding it and reporting `kind="unquoted"` with file and line number.

## Wrong flags

**3. The timing check flagged almost every line.** `results/demo_timing_uncalibrated_report.md`. On the
live Step A draft at a provisional 3.5 akshara/s, it returns 69 flags over 66 of the 80 lines it could
measure - median estimate/slot ratio 1.746, p90 2.857, max 4.048, and 82.5% of measured lines over the
slot by more than the 15% margin. (The other 20 lines are the transliterated ones: no Telugu letters,
so no akshara to count; the summary lists them by id rather than scoring them as clean.) Two causes,
and both are real:
- the rate is not calibrated yet - nobody has read ten Telugu lines aloud for this show;
- the first pass itself is verbose, because the model treated "keep it short enough for the time slot"
  as decoration rather than a constraint.

The check is not the thing that failed here; the draft was. But the *report design* failed, because a
list of 69 flags is not a shortlist. Response: timing flags now come back worst-first by ratio, the
evidence string carries the multiple (`1.75x the slot`), the summary prints the overrun share next to
the flag count and states where the rate came from (`override passed on the command line - not
calibrated`), so "this check is selecting nothing" is visible in the first line rather than something
you notice after reading forty rows.

## An AI tool used during the build, getting something wrong

**4. The stand-in Telugu first pass ignored its own slot field.** This is the required example, and it
is not a hypothetical. The instruction in `config.yaml` says *keep each line short enough to be spoken
inside its time slot*, and every item in the prompt carries `slot_seconds`. The model that produced
`data/telugu/step_a_raw_response.json` - the agent assembling this repository - returned lines such as

| English | slot | Telugu it returned | akshara | akshara allowed at 4.5/s |
|---|---|---|---|---|
| `I set it down an hour ago.` | 1.4 s | `గంట క్రితమే నేను పెట్టేశాను.` | 11 | 6 |
| `Promise me you will not sign her paper.` | 3.4 s | `ఆమె పాత్రకు నువ్వు సంతకం చేయవని మాట ఇవ్వు.` | 18 | 15 |
| `Three on my shoal. Say it to me.` | 2.0 s | `నా మట్టపై ముగ్గురు. నా ముందు చెప్పు.` | 12 | 9 |

All three exceed the budget they were handed, the first by almost double, and the model did not report
that it was doing so - it returned confident JSON with no note. Nothing about the output *looks* wrong;
the only way to see it was to measure it, which is precisely the argument for a timing check that runs
in plain Python and costs nothing. It is also the reason the first pass is labelled a stand-in and the
annotation is done by a person.

The 4.5/s column is the most generous rate anyone has claimed for Telugu speech; at the provisional
3.5/s the same slots allow 4.9, 11.9 and 7.0 akshara, so the three lines are over by 2-3x, not by a
rounding error.

**4b. The live model did the same thing, on the same line, worse.** After a real API key was wired in,
`I set it down an hour ago.` (1.4 s slot) came back from `openai/gpt-oss-120b` as
`నేను దాన్ని ఒక గంటకు ముందు పెట్టాను.` - **14 akshara**, about 4.0 s at the provisional rate - and from
`qwen/qwen3.8-27b` as `నేను గంట క్రితం దించాను.` - 9 akshara, still over. So this is not an artifact of
the agent-written stand-in: two different models served by the same API, same fixed prompt, handed back
a line 2.9x and 1.8x too long for a slot they were told about in the prompt, with no note. The
comparison model being closer is also the reason `telugu.comparison_model` stays in the config.

**5. Word choices in that same draft that need a native reader and are not verified.** `ఊచ` for
*tide*, `మట్ట` for *shoal*, `అడ్డుగట్టు`/`గట్టు` for *sandbar*, `బందరం` for *harbour*, `దయాధనం` for
*charity*, and whether `అత్తయ్య` is the right rendering of Caine's "Aunt" in a non-Indian period
setting. These are plausible, not confirmed. Anyone reading the Telugu file as though it were a human
localization is reading a machine draft with unverified vocabulary in it.

**6. I fixed the test instead of the code - twice - and once that was the right call.** Two early
assertions failed because my expectation was wrong (a scene split came out `[3, 2]` not `[2, 3]`;
high-severity-only precision is 1.0, not 0.8). Correcting the test was right. But "the test disagrees
with my model of the world" is also exactly what a real bug looks like, and the only reason these two
ended as test fixes rather than code fixes is that I went back to the source file and re-derived the
number. Recording that distinction here because it is the failure mode most likely to repeat.

## Found by the UI test rather than by reading the code

**7. Two timing flags on one line shared one id.** A line can be over its own slot *and* part of a
chain that is over the combined slot. `flag_id` was `line_check`, so both collapsed to
`E01-L024_timing`: the second decision overwrote the first, and the acceptance rate counted one action
where two had been made. Caught by running `app.py` under `streamlit.testing.v1.AppTest`, which raised
`StreamlitDuplicateElementKey`. Timing ids now carry the verdict. The lesson is that the report was
read as text and never acted on per line until the UI forced the question "what happens if an editor
reviews both of these?"

## Found by the live runs, not by the plan

**12. A model answered in the wrong alphabet and nothing noticed.** The live Step A run on
`openai/gpt-oss-120b` returned 20 of 100 lines as Telugu words written in Latin letters - e.g.
`Meeru seal ki kooda layakaledu. Aameyi teesukondi.` for *You are not worth a seal. Take her away.*
The `qwen/qwen3.8-27b` pass returned none. The draft file recorded the lines as complete, the pipeline
would have sent them to the meaning check as Telugu, and a generic "review this translation" prompt
reads them as correct because they *are* Telugu, just unprintable for a voice artist. Two things
failed: the model, and our own design, which had no check that counts letters. Fixed by adding check 5
(`src/checks/script.py`, zero model calls) and by reporting `not_telugu_script` in Step A coverage.
This is the clearest case in the log of a defect that only measurement could surface.

**13. The requested model does not exist on the account we were given.** The builder asked for
`llama-3.1-8b-instant`. Groq retired it for free and developer tiers on 2026-08-16
(`docs/public_evidence.md` item 7), and the key confirms it: 404 `model_not_found` for
`llama-3.1-8b-instant`, `meta-llama/llama-3.1-8b-instant` and `llama-3.3-70b-versatile`, and none of
them appear in `GET /models`. Default moved to `openai/gpt-oss-120b`. Reported rather than quietly
substituted, because an experiment whose model is named in the config but not in the run log is not
reproducible. Re-checked at 13:45 UTC on 6 November: `GET /models` returns 11 ids on this key
(`allam-2-7b`, two Orpheus TTS models, two Whisper models, `openai/gpt-oss-120b`, `gpt-oss-20b`,
`gpt-oss-safeguard-20b`, `qwen/qwen3.8-27b` and `meta-llama/llama-prompt-guard-2-22m/86m`). The only
"llama" left is a pair of prompt-injection classifiers, so there is no Llama chat model to fall back to
on this account.

**14. The free tier refused the forty-seventh request and the check threw away the first forty-six.**
The structured run completed meaning (18 batches) and relationship (18), then naturalness got 10
batches in before the key started answering 429/503 through five waits and gave up. Because each check
looped over its batches with no error handling, the exception propagated to the pipeline, which
recorded `naturalness: failed` - and the ten batches that *had* answered were discarded along with
their verdicts. So the artifact reported "0 lines judged" for work that had actually been paid for in
tokens, which is the opposite of the rule this repo is built on.

Fix in three parts, all now in the code: each LLM check catches `LLMError` per batch and returns the
batches it lost, so partial results survive (`_absorb` in `src/pipeline.py`); a partially judged check
is listed as partially judged, with the lines it read and the lines it did not, never as completed and
never as a clean pass; and `run_structured.py --merge` re-runs one check against an existing artifact
without paying for the others again. The run log for a label is cumulative across invocations, which is
why merging does not double count tokens.

**15. The annotation sheet went stale under our feet.** `data/annotation/blind_annotation.csv` was
generated from the imported stand-in draft. When Step A was re-run against the live models, 99 of its
100 rows no longer matched the Telugu a reviewer would actually be judging - and the reviewer would
have been scoring lines that were no longer in the file it exports. `scripts/make_blind_sheet.py`
rebuilds in place, keeps any verdicts already typed, and now records which Telugu file and which
provenance built the sheet. Nothing had been annotated yet, so nothing was lost; had the order been
different, the whole of Step B would have been invalid.

**16. A third of the relationship flags were the model saying it could not tell.** The first
structured artifact reported 51 relationship flags over 100 lines, which looked like the most
productive check in the tool. Counting the verdict strings behind them: 12 `address_mismatch`,
5 `too_formal`, 2 `honorific_dropped`, 2 `too_informal` - and **30 `unknown`**. `unknown` is in the
prompt's own enum, and the code mapped every verdict it did not recognise to a low-severity flag,
so 59% of that check's output was a refusal dressed as a finding. The evidence fields say why: *"No
relationship rule covers Edda Halloran speaking to any listener in this line"*, *"the sheet has no row
for the Company clerk speaking to Mistress Caine"*. The relationship sheet is keyed on a
speaker-listener pair and a screenplay block never records who is being addressed, so for many lines
there is genuinely nothing to check against.

Fixed by making the distinction explicit: a declined verdict is recorded in the verdict table and
counted as `lines_not_judged`, never as a flag and never as a clean line; a verdict outside the enum
is flagged as `outside_enum:<value>` so a contract break stays visible instead of being laundered into
"low severity"; the report prints a coverage line and a warning under "Reading this report"; the review
UI says the same in a banner. Same rule applied to a blank verdict in the meaning and naturalness
checks. The structured artifact now reads **21 relationship flags and 30 lines not judged** out of the
same 100 lines and the same recorded responses - nothing new was paid for to find this.

**17. Partial retention was silently missing from the one check that needed it most.** While
re-scoring naturalness, `naturalness.run` raised `ValueError: not enough values to unpack (expected 3,
got 2)`: the per-batch `except LLMError` and the `failed` list had been added, but the function still
returned `(flags, verdicts)`. So naturalness - the check the free tier actually throttles - discarded
every answered batch exactly as before, and the pipeline's new `_absorb` never saw the refused ones.
The crash was only found because a merge run happened to call that branch. `tests/run_tests.py` now
calls all three LLM checks with a stub that refuses the second batch and asserts each returns
`(flags, verdicts, failed)` with the answered batch kept, so this cannot regress quietly.

**18. The free tier does not cap requests, it caps tokens per day - and we had spent the day.** The
throttle message, once it was actually read instead of slept through: `429 ... on tokens per day (TPD):
Limit 200000, Used 198682, Requested 2237. Please try again in 6m37.008s`, with
`retry-after: 398`. Three consequences, all now in the code. `_create` obeys the provider's own
`retry-after` instead of a hardcoded ramp (waiting 20 s against a 398 s hint is a guaranteed second
failure), it stops waiting when no attempt is left rather than sleeping before giving up, and a per-batch
`max_wait_seconds_per_batch` ceiling stops one stubborn scene from eating the run. And because a whole
structured pass costs about 127k of those 200k tokens - measured per check over 18 scene batches:
meaning 35,571, relationship 54,292, naturalness 37,332 scaled from its 19 logged requests -
naturalness later measured whole at 39,750, which prices a clean pass at about 130k -
one day of free tier is about 1.5 full passes. That is why `run_structured.py` and `run_qa.py` replay
any batch whose exact prompt is already in the label's call log (`--fresh` forces a real re-request),
so a run interrupted by the budget can be finished later without paying twice. The replay is keyed on
model + system + user text, so changing a prompt cannot inherit an answer from the old prompt: it just
misses. This is what turned today's dead end into a free re-score: 47 of 54 batches came back from the
log, one request was actually spent, and the 30-refusal finding above cost nothing to discover.

What the later retries taught is not in that arithmetic. The cap is not a wall you hit and stop at: at
14:20 UTC, after a 429 that morning, a 73-token probe succeeded, and a naturalness merge answered 7 of
its 7 unpriced batches - then two of them, `episode-005.txt#S02` and `episode-006.txt#S02`, refused
through 530 s and 600 s of waiting. Both are ordinary 8-line batches, the median size, so whether a
scene gets an answer depends on *when* you ask, not how big the request is: the window frees tokens as
they age out, one at a time. A second attempt with the wait ceiling cut to 90 s refused both again and
spent nothing, because the other 16 batches came from the log - 16 reused, 2 attempted, 55 requests
total either way. Naturalness therefore ends at **84 of 100 lines judged**, and the report says so in
those words rather than rounding it up to a pass. *(Closed on 2026-11-07 by the re-run in entry 26, which
is also the time the sentence above about prompt-text replay stopped being theoretical.)*

**19. A document claimed a run that no artifact supports.** `PRD.md` §15 said the second screenplay in
`data/new_show_demo/` was "used to prove the new-input rerun", which reads as a full gate run on unseen
input. `ls results/` has no `new_input_*` files: the claim was written from the intent of the script,
not from a run. Two things came out of checking. First, `scripts/run_qa.py --checks timing,script`
without `--telugu` silently triggers the Step A generation, so the rehearsal that should have cost
nothing was about to spend requests; `--skip-step-a` now refuses to do that and says so. The rehearsal
was then actually run twice, both at zero requests, and the artifacts are on disk:
`results/new_input_rehearsal_*` (unseen episode: 34 lines parsed, 0 unparsed blocks, nothing judged
because nothing had Telugu) and `results/qa_rehearsal_*` (full corpus with the real draft: 184 lines,
100 with Telugu, 91 flags - 69 timing and 22 script form). The timing half of that is not a calibrated
number: `config.yaml` still has `syllables_per_second: null`, so the run passed 3.5 on the command line
and the artifact records the rate as "override passed on the command line - not calibrated". The LLM
half on unseen input is still not run, and the docs now say that instead of implying it was. Second, the
report printed the opposite of its own warning: for the unseen episode it said "Every line was read by
every check that could run on it" two lines below a warning that no line had Telugu, and then listed all
34 as "Not flagged". `write_markdown` now counts lines with no Telugu alongside refused batches and
declined verdicts and keeps them out of the cleared list. The first version of that heading then needed
correcting too: it claimed *nothing* had read those lines, when the pure-code checks had read all of them -
what is true is that they were not read by every check. Four assertions in `tests/run_tests.py` hold the
line. (The suite was at 80 self-tests that day; entry 21 explains why the unseen episode had no Telugu
attached in the first place, which is the cause this entry only described as a symptom.)

**20. A merge silently deleted the record that a check was only partially judged.** Re-rendering the
structured report after the naturalness retry - `--checks timing,script --merge structured`, zero
requests, all three LLM checks carried over - turned `errors` from
`[{"check": "naturalness", "partial": true, "error": "2 of 18 batches refused; 84 lines judged, 16 not"}]`
into `[]`. The flags survived, the summaries survived, and the "Checks that did not finish" section simply
vanished, because the merge dropped prior errors for any check whose *flags* were carried over - which is
exactly the partially judged one. This was found by diffing against the snapshot taken before the render,
not by reading the code, where the expression looked like sensible de-duplication. It is the same failure
as entry 17 one layer up: work that was honestly recorded as incomplete, quietly becoming a clean pass.
Now `carry_over_errors()` in `scripts/run_structured.py`, tested four ways: a timing re-render keeps the
naturalness refusal, re-running a check replaces its own error, and an untouched check's error survives.
The base artifact was restored from the snapshot and re-merged, so the shipped
`results/structured_run.json` carries the refusal again.

**21. Step A's own answer never reached the checks that were supposed to read it.** The live run on the
unseen episode (`scripts/run_qa.py --input data/new_show_demo --label new_input_live`) came back with 20
flags: 14 from `meaning` at **high** severity, each with the evidence line `Telugu:` followed by nothing and
the reason "Telugu line is empty, so the content is missing", plus 6 naturalness, and 0 timing and 0 script
flags. The model was not misbehaving. `run_qa.py` generated the Telugu, wrote it to
`data/telugu/new_input_live.json`, printed its coverage, and never put it back on the records the checks
read - so 34 empty fields went to every check. The two pure-code checks reported nothing to read; the three
LLM checks were asked to judge a draft that was not there and returned confident findings anyway. This is
entry 19's gap and entry 20's gap in their worst form: not a missing warning, but 14 invented high-severity
flags for a file that had been produced one function earlier and discarded.

Found by reading a flag's evidence and noticing `Telugu: /` with nothing between them, then checking the
generated file on disk, which had Telugu in it for all 34 lines.

Fixed in two places because the mistake has two shapes. `attach_from_payload()` in `scripts/run_qa.py` is
now used by the `--telugu` branch and the Step A branch alike, and writes only non-empty values, so a blank
answer cannot erase a draft another source supplied. `judgeable_lines()` in `src/pipeline.py` keeps a line
with no Telugu out of every model batch, in the structured arm and the baseline control alike, so a missing
draft is a coverage gap the report can name rather than a finding. It changes nothing already measured: all
100 sample lines have Telugu, so the filter is a no-op on both shipped arms.

What the same unseen input says now. Step A cost 3 requests, 4,812 prompt and 3,789 completion tokens for
34 lines, and 9 of the 34 came back in Latin script - the same default-model habit the `script` check exists
for. The two pure-code checks then ran over that draft at zero requests and found 33 real things: 24 timing
flags (median slot ratio 2.34, 92% of the lines it could read over tight slot + 15%, at the same uncalibrated
3.5/s override) and 9 script-form flags. `results/new_input_code_*`. Getting there spent one genuine Step A
call the log had not covered, 1,938 prompt and 1,556 completion, taking the workshop total to 116 requests /
162,926 prompt / 109,086 completion. The three LLM checks have still never produced a valid finding on
unseen input, and the void attempt is kept at `scratch/broken_attach_evidence/` so this entry can be checked
instead of taken on faith. Six assertions in `tests/run_tests.py` hold the two fixes: 86 self-tests at the time of that fix, 91 now.

**22. The assistant fabricated ten lines of the evaluation and the reviewer graded them.** Block 7 of the
blind annotation was presented as rows A061-A070 with English and Telugu for each. All twenty of those strings
were invented. `I know what a signed paper does to a room. I have watched it in nine harbours.`,
`I am not a clause.`, `I am not a man who is good at these rooms, Miss Halloran.` and eight more exist nowhere
in `data/annotation/blind_annotation.csv`, nowhere in `data/parsed/corpus.json` and nowhere in the six
screenplay files. The real row 62 is `Lock the gate, Edda. It is you he means.` with the Latin-script draft
`Darwaza nilipi, Edda. Aadani artham meeru.`; the real row 70 is `Then the lamp wants buying, and I have the
money in my coat.` The reviewer answered the invented lines, in good faith, and their verdicts, error types,
severities, confidences and Telugu rewrites were then written onto ten real rows whose content they had never
seen. Nothing was misaligned: the judgements describe sentences that are not in the study.

How it was found, one hundred rows later. While recording block 10, the reviewer flagged the spelling of
Halloran across the sheet; checking the sheet to count the variants turned up row 62's `corrected_line` talking
about a signed paper and nine harbours, which cannot be a correction of a gate-locking line. From there the
audit was mechanical: `scratch/audit_rows_shown.py` re-reads the transcript, and for each of the 100 rows
tests whether that row's real `english` **and** real `telugu` ever appeared in anything the assistant sent.
**90/100 pass. A061-A070 fail.** Blocks 1-6, 8, 9 and 10 were presented faithfully, so the other ninety rows
stand and only this block was poisoned.

What was done. The ten rows' verdict columns were cleared, not edited, and the reviewer's block-7 answers were
kept intact at `scratch/ghost_block7_answers.json` with the invented line each one was about, so the record is
not destroyed and the fabrication is checkable rather than asserted. The block was re-presented from the file
through `scratch/present_block.py`, which reads the CSV and prints rows - the only defence that matters here
is that no row content can now come from the assistant's memory.

Consequences that have to travel with the submission. `scratch/annotation_consistency_notes.md` had promoted
three of these ghost rows into sheet-wide claims, and all three are withdrawn in that file: the two
non-words said to have slipped past the `script` check at rows 62 and 65 (`బందర్\u200cగాళ్లలో`, `బందరు` - drafts
that were never generated), the `క్లాజ్` consistency said to repeat at row 70, and the two register rows said to
be Mistress Caine speaking to Edda and to the boy at 63 and 69, whose real speakers are Edda Halloran and the
Voice of the lamp. The sharpest loss is the first of those: **the "no check asks whether a Telugu word exists"
gap is now an argument with no evidence behind it.** It is still true that nothing in this build validates
wordhood and no dictionary or morphological validator is built, and rows 29, 31 and 39 do show real
non-word/in-script defects - but `script` catches those three by letter count, so the interesting claim
(a well-formed Telugu non-word passing every check) is currently un demonstrated. It must not reappear as a
finding until a real row shows it.

This is the worst error in the build because it is not a check being weak; it is the human-evidence layer,
the part the whole submission rests on, being unverified for ten rows. The scoring script would have consumed
it silently: `scripts/score.py` reads verdict columns and nothing in it can tell that a verdict was earned on
a different sentence. The general lesson, written where it will be read - **present source data to a reviewer
by running the file, and audit that what was shown is what is stored.**

**23. The scorer crashed the first time it had a complete sheet to read.** `scripts/score.py` opens with a
guard that refuses to run on an unfilled annotation file, and the guard had fired on every invocation this
project ever made, so line 115 - `if s["flags"] == 0 and genuine:` - had literally never executed. The instant
the hundredth verdict was recorded, the scorer reached that line and raised `NameError: name 's' is not
defined`. `s` was never a variable in the file; the intent is `s_score["flags"]`, and the sibling lines around
it already used `s_score`. One character of a name, and it sat behind a guard that made the code below it
unreachable for the entire build.

This is the mirror image of entry 21. There, a run looked clean because the data never arrived; here, a tool
looked finished because it had always exited early with a *correct-looking* message. "It refuses until you do
the human part" is a good safety property, and it is also a way to hide an unexecuted tail. The fix is in
`scripts/score.py:115`; the run that proved it is `results/scores.json` and `docs/phase0_results.md`, written
2026-11-07 11:40 from the completed sheet. `score.py` also gained `--report`, because it wrote that document to
a hardcoded repo path, which meant no test could call `main()` without overwriting a submitted document with
fixture data. Five assertions in `test_the_scorer_finishes_once_the_sheet_is_filled` run the completed path
against a synthetic filled sheet and read the caveat line that used to crash: 91 self-tests.

**24. What Step D said when it finally ran, and what it still cannot say.** From 100 blind rows, 81 graded
`needs_revision`: structured QA **precision 0.509, recall 0.525** over 165 flags (81 false positives), the
unstructured baseline control **precision 0.897, recall 0.248** over 58 flags. Per check: `script` 1.0
precision / 0.139 recall, `meaning` 0.846 / 0.069, `naturalness` 0.675 / 0.171, `timing` 0.275 / 0.119,
`relationship` 0.238 / 0.032. The gate's own rule is that structured must beat the baseline at similar
precision, and no severity cut of the structured arm reaches the baseline's 0.897 - highest is 0.536 at
high-only - so **the decision is NO-GO**, with `relationship` marked for the drop list.

Three things that must travel with those numbers, not behind them. One: `acceptance_rate` is empty because the
approve/dismiss pass has not been run, and PRD §9 makes that pass, not precision, the criterion for dropping a
check - so `checks_to_drop: ["relationship"]` is an arithmetic output, not the decision the plan asked for.
Two: the `naturalness` batch errors are still there, 2 of 18 batches refused and 16 lines never judged, so
that arm's recall is measured over 84 of 100 lines and the report says so in `caveats`. Three: single evaluator,
single language, no inter-rater agreement, and the sheet it scores is the one that contains the block-7
re-annotation above. The honest reading of 0.248 vs 0.525 recall at 0.897 vs 0.509 precision is that the
decomposed arm finds roughly twice as much of what the human saw while being wrong about roughly half of what
it flags, and that the unstructured control is being underestimated by our own comparison rule - not that
either design has been refuted.

**This entry's last paragraph is superseded by entry 25.** The "twice as much" reading came from a recall
formula that did not divide what it claimed to, and the numbers in this entry are the pre-fix output of
`scripts/score.py`. They are left as written because they are what the build believed on 2026-11-07 at 11:40;
the corrected run is entry 25, and `results/scores.json` now carries both.

**25. The comparison rule was wrong in the gate's favour's opposite direction, and a seeded result described
a run that had never happened.** Two defects in `src/metrics.py` and `scripts/score.py`, found while re-deriving
Step D in plain loops (`scratch/recheck_step_d.py`) after the reviewer asked whether the sheet could be trusted.

One: recall was `true_positive_flags / (true_positive_flags + missed_instances)` - a flag count over a mixed
count. For the structured arm the denominator came to 160 against 158 reviewer issues; for the baseline it came
to **210** against the same 158, because a baseline flag names no error type while the miss counter demanded a
flag whose check equalled each type. So the unstructured control was reported at recall 0.248 when its flags sit
on lines covering 109 of the 158 issues, 0.690. The submitted sentence, "the decomposed arm finds about twice as
much of what the human saw", was not merely imprecise: on a like-for-like denominator the decomposed arm finds
*less* by that measure (82 of 158). Numerator and denominator are now the same kind of thing, the instance
credit list is in `results/scores.json` as `credited_instances` so anyone can recompute it, the old value is
retained beside it as `recall_legacy_flagcount`, and `line_level` is reported too - which is where the useful
finding is: the gate touches **78 of the 81** issue lines at 0.867 line precision, against the baseline's 52 of
81 at 0.897. It behaves as a decent line-level shortlist and as a weak type-namer - a reading of the numbers,
not a mode the tool ships - and the pre-registered rule only measures
the type-naming, so **the recorded decision stays NO-GO and is not being relabelled after the fact.**

Two: `scripts/score.py` scored the seeded errors with `seeded_flags.get("flags", []) or s_flags`.
`results/structured_seeded_flags.json` has never existed, so every seeded number to date was the *clean* run's
flags looked up against lines broken only in the seeded draft, and the guard that was supposed to warn about a
missing seeded run checked `seeded_manifest.json` instead of the flags file - so it stayed silent. Worse,
`seeded_recall` counted any flag on a line as detection, which is how "meaning: 4 seeded, 4 detected, recall
1.0" was produced while the meaning check itself fired on none of the four and `by_check` showed the timing
check catching them. A seeded error caught by the wrong check is not that check working; it is that line being
noisy. The fallback is gone, a missing artifact now returns `status: not measured` plus the command to run it
and a caveat that says any seeded number in a document is unsupported, and detection is reported twice:
`detected_by_expected_check` and `detected_by_any_check`.

Why this one is worth two paragraphs: both defects made the submission look *better* than the evidence, and
neither was caught by the 91 self-tests that existed, because every one of them fed the functions inputs shaped
like the bug. The new tests are written from the failure, not from the design: `tp + fn` is pinned equal to the
instance count for both arms, an untyped flag is pinned to credit every type on its line, a wrong-check flag on
a seeded line is pinned to score 0.0 for the check that was supposed to catch it, and the scorer is pinned to
refuse the clean run's flags when the seeded artifact is absent. 109 self-tests.

**Superseded on one point by entry 26:** the 78/81 line figure and the 0.867 line precision were measured while
16 naturalness lines sat unanswered. After the re-run the same arithmetic gives **80 of 81 lines touched at
0.879 line precision**, 0.506 flag precision and 86/158 instances over 174 flags. The decision does not move:
still NO-GO, still `relationship` on the arithmetic drop list, still no severity cut reaching 0.897.

**26. Closing the naturalness coverage gap cost 18 full batches, because the replay guard compares prompt text
and the prompt quotes the register standard.** `results/structured_flags.json` carried
`{"check": "naturalness", "partial": true, "error": "2 of 18 batches refused; 84 lines judged, 16 not"}`, which
means the structured arm's own recall was measured over 84 of 100 lines while the control was measured over 100 -
a caveat the reviewer rightly said weakened the report. The fix looked free: `python scripts/run_structured.py
--checks naturalness --merge structured`, whose whole point is that 16 of those 18 prompts are already in
`results/structured_calls.jsonl` and should be replayed at zero cost.

It printed `batches reused from the call log (no new tokens): 0` and spent **18,985 prompt and 20,765 completion
tokens**, the price of a complete naturalness pass, for a coverage gap of 16 lines. The reason is in the diff of
one batch: the user body of the naturalness prompt embeds the register standard, and earlier the same day two
reviewer decisions moved its prefix from `[DRAFT - needs the builder's sign-off ...]` to `[PART-SIGNED-OFF - ...]`.
The replay key is a hash of the exact prompt string, so every one of the 18 batches was, as far as the guard is
concerned, a question nobody had asked before. Nothing was wrong with the guard - **entry 18 already says this in
words**: "the replay is keyed on model + system + user text, so changing a prompt cannot inherit an answer from
the old prompt: it just misses." Two things were wrong. The summary prose in README and PRD §11 had turned that
mechanism into "cost is never paid twice for the same answer", which is a promise the code never made; and I read
entry 18's sentence on Monday, did not connect it to the sheet edit I had made two hours earlier, and found out
with 40k tokens instead. Editing `data/relationship_sheet.yaml` re-prices naturalness and relationship together
and the tool says nothing beforehand.

What the money bought: naturalness now judges **100 of 100 lines** with 49 flags where the partial pass had 40,
`errors` is empty, the report's coverage line is gone, and the structured arm's untouched issue lines went from
three (`E01-L001`, `E05-L003`, `E05-L014`) to one (`E05-L003`). Type recall for the check moved 27 → 31 of the
reviewer's 58 naturalness issues. Every Step D figure in this repository was re-scored from the re-run artifact
and re-quoted; the workshop total is now **134 requests, 181,911 prompt and 129,851 completion tokens**, and a
clean full pass prices at about 130,000 of the 200,000 daily tokens rather than 127,000. Two lessons kept: state
resumability as *prompt-text* replay, not as free re-runs, and treat a signed-off input file as a change to the
experiment, because it invalidates the cached answers that were produced under the old one.

**27. Two numbers arrived in a draft paragraph, and neither was in the build.** The text described "an assumed
speech rate of about 6.5 akshara per second" and "the 28% acceptance rate for timing". The first matches nothing:
`config.yaml` is `syllables_per_second: null`, `data/calibration.json` does not exist, and
`results/structured_flags.json` records `"syllables_per_second": 3.5, "rate_source": "override passed on the
command line - not calibrated"`. The second was not an acceptance pass either - the sheet behind it split 87
approved / 87 dismissed with **zero** rows disagreeing with the scorer, no `editor_action_ts` anywhere, and a
note on every row saying `editor to confirm`, and its per-check rates reproduced `scores.json` precision exactly
(timing 0.275, naturalness 0.633, relationship 0.238, script 1.000). "28% acceptance for timing" was timing's
precision wearing the name of the metric PRD §9 uses to drop a check, which makes the drop decision an
assumption dressed as a measurement - the same family of error as entry 22. Neither number went into a document,
and `data/annotation/decisions.csv` still ships all 174 rows `pending` because the statuses are the reviewer's
to give.

What could honestly be done instead was: bound the rate from text already in the repo.
`scripts/derive_rate.py` divides the reviewer's own `corrected_line` akshara by that line's slot and gets a
median **5.83 akshara/s** (n=83), where the draft's own text demands 6.11 and the run used 3.5; it writes
`data/calibration_derived.json`, which `src/config.py` does not read, so a derived number can never quietly
become the calibration. Re-pricing timing at 5.83 costs nothing - the check is plain Python - and via
`--checks timing --rate 5.83 --merge structured` gives 37 flags instead of 69, precision 0.275 → 0.459,
false positives 50 → 20, and 16 rather than 18 of the reviewer's 19 timing instances. The honest limits of that
are written into the file: a rate derived from corrected lines makes those lines fit by construction, and the
reviewer annotated the 3.5 list, so `results/scores.json` keeps describing the run that was actually graded and
this one sits beside it as `results/scores_timing_derived583.json`. The ten hand-timed seconds are still the
only thing that can close this.

**28. The first real acceptance batch says the check the arithmetic wanted to drop is the one worth fixing.**
Ten `relationship` flags, the ten highest-severity ones, graded by the reviewer: 1 accept, 4 accept-but-modify,
5 dismiss. Acceptance 0.5 where precision is 0.238, which is the first time in this project the two metrics of
PRD §9 disagree, and they disagree for a reason worth writing down rather than a reason worth averaging out.

The dismissals are not "the model hedged". **Two are wrong listeners**: `E01-L017` ("Tell that to the tide,
Mistress") is addressed to Caine, and `E03-L010` is addressed to Silas, so the check was judging each line
against the register rules of somebody the line was never spoken to. **Two are the sheet being wrong, not the
line**: `E03-L031` uses `నాన్నా`, which is exactly right for a daughter to her father and simply is not in
`expected_address_terms`, and `E05-L011` has a constable say `హల్లొరాన్ గారు`, which the reviewer calls natural
where the sheet expects a title. **One is a rule applied to nothing**: `E03-L008` is "He bought them.", a
four-word reply that needs no address term in Telugu. And all four accept-but-modify rows give the *same*
reason, which the check never looks at: Mistress Caine addresses Edda with `మీరు` where an aunt uses `నువ్వు`,
so the flag was right that the register was wrong and wrong about what to do about it every single time - it
proposed prepending a title, and the reviewer replaced four whole lines instead.

Two decisions followed, and both were made to keep the two kinds of statement separate. The builder kept the
check rather than dropping it, on 10 of 21 flags, with the other 17 batches explicitly allowed to change it -
so `scripts/score.py` still emits `checks_to_drop: ["relationship"]` from the pre-registered thresholds and
`data/check_overrides.json` now carries the human decision beside it as `checks_retained_by_override`, with
evidence, who decided, the n and when to revisit. Nothing moves a threshold to fit a conclusion, which is the
same discipline that kept `recall_legacy_flagcount` in entry 25 instead of overwriting it. The other decision
was to *not* apply the sheet fixes yet. Adding `నాన్నా` and the Caine→Edda pronoun register to
`data/relationship_sheet.yaml` rewrites the prompt prefix that naturalness and relationship both quote, and
entry 26 priced that at 18 full batches. One sheet edit after the acceptance pass, not eleven.

## Small, real, worth writing down



**8. Windows console encoding.** Printing Telugu through a cp1252 console raised `UnicodeEncodeError`
in eleven scripts at once. `src/console.py:force_utf8()` is now the first statement in every `main()`.

**9. A check's return contract changed and the report crashed.** `timing.run` was changed to return
`(flags, table, summary)`; `report.write_markdown` was still iterating the old 2-tuple and raised
`TypeError: string indices must be integers`. The fix was the contract, not a defensive `if`.

**10. YAML integers.** `episodes: 2` in the alias map crashed `in_range` with
`'int' object has no attribute 'split'`. The parser coerces now; the config format was never promised
to be all strings.

## Struck from the submitted documents

**11. Two confidential-pack statistics.** The addendum quotes a median slot of 2.0 s and 21% of lines
under 1.5 s, measured once from Kuku's confidential input pack. Kuku has not approved citing them, so
they are struck from the two-page doc and replaced with our own corpus numbers: median tight slot
**2.6 s**, **10%** of lines under 1.5 s, median English delivery **3.18 words/s**
(`docs/corpus_statistics.md`). Ours are from a screenplay we wrote, which makes them weaker as
evidence about production microdrama and stronger as evidence we can actually show you the file.
