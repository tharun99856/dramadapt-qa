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
structured pass costs about 129k of those 200k tokens - measured per check over 18 scene batches:
meaning 35,571, relationship 54,292, naturalness 38,984 extrapolated from its 14 answered batches -
one day of free tier is about 1.5 full passes. That is why `run_structured.py` and `run_qa.py` replay
any batch whose exact prompt is already in the label's call log (`--fresh` forces a real re-request),
so a run interrupted by the budget can be finished later without paying twice. The replay is keyed on
model + system + user text, so changing a prompt cannot inherit an answer from the old prompt: it just
misses. This is what turned today's dead end into a free re-score: 47 of 54 batches came back from the
log, one request was actually spent, and the 30-refusal finding above cost nothing to discover.

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
half on unseen input is still not run, and the docs now say that instead of implying it was. Second, the report itself was laundering the gap: for
the unseen episode it printed "Every line was read by every check that could run on it" two lines below
a warning that no line had Telugu, and then listed all 34 as "Not flagged". `write_markdown` now counts
lines with no Telugu alongside refused batches and declined verdicts, and puts them under "Flagged by
nothing because nothing read it" instead of under cleared. `tests/run_tests.py` asserts the pass claim
is withheld, which is now 76 self-tests.

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
