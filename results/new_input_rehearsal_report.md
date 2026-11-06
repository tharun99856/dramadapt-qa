# DramAdapt QA report - new_input_rehearsal

Generated 2026-11-06T13:41:17+00:00. Model: `None`.

## Summary

- Lines reviewed: **34**
- Lines with Telugu attached: **0** of 34  *(the rest were not judged - see below)*
- Checks completed: **2** of 2
- Lines flagged: **0**
- Flags by check: 
- Flags by severity: 
- Model coverage: no LLM check ran on this run
- Timing: rate **3.5** akshara/s, no lines measured
- Requests: 0 for 3 scene batches (prompt tokens 0, completion tokens 0, cost None)

**Coverage warning:** 34 lines have no Telugu text, so no check could run on them. A missing line is not a clean line.

## Flagged lines

| flag | line | check | severity | verdict | English | Telugu | slot | evidence | suggestion | status |
|---|---|---|---|---|---|---|---|---|---|---|
| - | - | - | - | - | no flags | | | | | |

## Not flagged

every line was flagged or was never judged

## Flagged by nothing because nothing read it (34 lines)

E01-L001, E01-L002, E01-L003, E01-L004, E01-L005, E01-L006, E01-L007, E01-L008, E01-L009, E01-L010, E01-L011, E01-L012, E01-L013, E01-L014, E01-L015, E01-L016, E01-L017, E01-L018, E01-L019, E01-L020, E01-L021, E01-L022, E01-L023, E01-L024, E01-L025, E01-L026, E01-L027, E01-L028, E01-L029, E01-L030, E01-L031, E01-L032, E01-L033, E01-L034

## Reading this report

- Timing flags are risk against the English performance window, not failure: dubbing can retime a line.
- Naturalness flags are advisory only and carry no score.
- Nothing here is auto-approved. Every flag needs an editor action.
- Akshara counts in the timing column are machine counts of Telugu syllables by `src/telugu.py`: one per base letter, minus one per virama, so a conjunct counts once.
- Absent from the flag list is not the same as cleared: no line in this run has Telugu attached, so nothing was judged on it. Check the coverage lines above before reading this as a pass.
