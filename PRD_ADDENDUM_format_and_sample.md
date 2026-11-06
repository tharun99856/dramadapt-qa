# DramAdapt QA — Input Format and Sample Plan (Addendum, v2)

Companion to `PRD.md` v2. Draft v2, 6 November 2026. Kuku AI Generalist Assignment, Problem 3.

**Where v2 disagrees with `PRD.md`, this addendum wins on format and sample questions.**

---

## 1. What changed from addendum v1

v1 documented Kuku's confidential input pack: the show title, the folder name, its per-episode content, character identities read out of its scripts, and statistics computed from its files. **None of that belongs in a repository, a demo, or a submitted raw-output folder — including behind an unlisted link.**

v2 keeps the *shape* of the format (it is a reasonable industry shape, and the interview may hand us a new show in something like it) and re-bases every concrete value on our own original screenplay, `HARBOUR OF THORNS`.

| v1 section | v2 status |
|---|---|
| §2 Source data (show name, pack folder path) | **Removed from this document.** See §8, "Pack format compatibility". |
| §3 Observed file format | Kept as a format *specification* we author to, not as an observation about Kuku files. |
| §4 Measured facts (episodes 1–15) | Replaced with measurements of our own screenplay (`results/format_report.json`). Two pack-derived aggregates survive under the confidentiality rule in `PRD.md` §10. |
| §5 Quirks the system must handle | Kept — all of them were reproduced deliberately in our own screenplay so the parser has to handle them. |
| §6 Character and relationship sheet | Replaced with our own cast (`data/relationship_sheet.json`). |
| §7 Parser requirements and acceptance tests | Kept, re-pointed at our files. |
| §8 Timing check | Kept. |
| §9 Phase 0 sample plan | Kept, re-pointed at our files. |
| §10 Changes to the main PRD | Applied in `PRD.md` v2. |
| §11 Open items | Updated in §9 below. |

## 2. Source data

- Show: **HARBOUR OF THORNS**, an original English-language microdrama written by the builder for this experiment.
- Location: `data/screenplay/`, six episode files, plain text, one per episode.
- File names follow `episode-NNN.txt`.
- Everything in it is our own work: safe to commit, publish, and submit as raw output.

## 3. File format specification

Each file has:

1. A header with three one-line fields: `EPISODE NUMBER`, `EPISODE LOGLINE`, `CONTINUITY NOTES`.
2. A `[SCRIPT START]` marker and a `[SCRIPT END]` marker.
3. One or more scenes. Each scene has a `SCENE NN` line, a scene heading (`INT.`/`EXT.`, place, time of day), a scene start time, a scene end time, then Actions and dialogue.
4. Blocks. A block is a label ending in a colon, then a `[start - end]` time bracket, then text. Block types are `CAMERA` (shot description), `ACTION` (what happens), `SOUND FX` (sound and music), and speaker blocks. A speaker block has the speaker name plus a delivery tag in brackets (emotion words), then the `[start - end]` bracket, then the spoken line in double quotes on the next line.
5. Times are `minutes:seconds.tenths` and are **absolute within the episode**. A new scene continues from the previous scene's end time and does not restart at zero.
6. Speaker labels may carry extra tags such as `O.S.`, `V.O.` or `Off-screen` before the delivery tag.

## 4. Measured facts (our own screenplay)

Written to hit the distribution needed for a realistic QA test, then **recomputed by `scripts/format_report.py` after the fact** — the numbers below are filled in by that script into `results/format_report.json`, not asserted here by hand.

Structural targets we authored against, and the two pack-derived aggregates that motivate them:

- slot per line: median around 2.0 s, with roughly a fifth of lines under 1.5 s — this matches the two aggregates quoted in `PRD.md` §10, measured once from the confidential pack.
- line length: median around 5–6 words, with a tail of long lines at 12+ words.
- some lines deliberately share a slot boundary so overlaps exist.

Run `python scripts/format_report.py` and paste the real totals into the two-page doc. **Do not submit the doc with these targets described as measurements.**

## 5. Quirks the system must handle

Deliberately present in our screenplay, each with a parser or check requirement attached:

1. **Many labels, few characters.** One character appears under several labels; the alias map resolves them (`§6`).
2. **One label reused for different people.** `THE COMPANY CLERK` is used for two different men in different episodes; the alias map is keyed by label **and episode range**, not label alone.
3. **Split sentences.** Lines ending in an ellipsis followed by a line from the same speaker starting with one. Telugu is verb-final, so fragments cannot be translated one at a time: group them into chains, run the meaning check on the whole chain, and the timing check per slot.
4. **Voice-over and off-screen lines.** Kept and tagged; their slots can overlap on-screen action.
5. **Overlaps inside the source.** If the previous line's estimate runs past the next line's start because the *source* windows overlap, do not report it as a Telugu timing error.
6. **Header drift.** Labels must be matched case-insensitively; headings use an en dash in some places and a hyphen in others; whitespace varies. Both dash types and both heading cases appear in our files on purpose.
7. **Period setting.** The English is 19th-century coastal (titles, "Master", "Mistress", "My child"). Decision: keep the period and translate into period-appropriate Telugu, in the style of dubbing, not a modern or Indian-setting transposition. QA judges against that standard.
8. **English only in the source.** Telugu is added by us as a first pass, so every record needs room for it.

## 6. Character and relationship sheet

Held in `data/relationship_sheet.json`, which is the editable alias map plus per-episode registers. Cast (all original):

- **Edda Halloran** — protagonist, keeps the lamp after her father's accident. Labels: `EDDA`, `EDDA HALORAN`, `THE KEEPER'S DAUGHTER`.
- **Halloran** — her father, retired keeper. Labels: `HALORAN`, `THE OLD KEEPER`. She says *Father*; he calls her *lass* and *Edda*.
- **Mistress Caine** — creditor, runs the harbour company; Edda's aunt by marriage. Labels: `MISTRESS CAINE`, `CAINE`, `THE COMPANY AGENT`. Edda calls her *Aunt Caine* in episode 1 and *Mistress Caine* from episode 3 — a deliberate address shift.
- **Joss Marek** — bargeman, accused of smuggling, later the buyer who can save the lamp. Labels: `JOSS`, `MAREK`, `THE BARGEMAN`. Edda uses *Marek* then *Joss*; the shift is a register test.
- **Brother Anselm** — harbour chaplain. Calls Edda *My child* and *Miss Halloran*; Edda calls him *Father Anselm*, which collides with *Father* for her own father — a deliberate ambiguity for the relationship check.
- **Delia** — the cook; informal, uses *love*, *lass*.
- **Silas Vane** — Caine's son, Edda's former betrothed. Labels: `SILAS`, `MASTER VANE`.
- Minor: `CONSTABLE ROE`, `THE COMPANY CLERK`, `VOICE OF THE LAMP` (child V.O.).

Address-shift moments worth testing (formal vs informal "you" and honorific choice in Telugu) are tagged in the sample selection with `address_shift: true` — at least 10 of them, so the relationship check has real work to do.

## 7. Parser requirements

Input: a folder of episode files, or a single file. Output: structured records plus a validation report.

Record fields:

- episode number, scene number, scene heading
- line id (`E01-L012`)
- speaker label as written, canonical speaker, delivery tag
- flags: voice-over, off-screen, part of a chain, address shift
- start and end in seconds; tight window; loose window
- spoken text; Telugu text (empty until added)
- nearby action text: the `ACTION` and `CAMERA` blocks just before the line
- episode logline and continuity notes
- source file name and line number

Rules:

- Labels matched case-insensitively, with tolerant whitespace and either dash type.
- Dialogue means a labeled block whose label is not `CAMERA`, `ACTION` or `SOUND FX`, and whose text is in double quotes.
- **Never silently drop a block.** Anything unparsed goes into the validation report with file name and line number.
- Tight window = `end − start`. Loose window = next dialogue line's `start` − this line's `start`, capped at scene end. For the last line in a scene, scene end − `start`.
- A chain is a line ending in an ellipsis followed by a line from the same speaker that starts with one.
- The alias map is keyed by label and episode range. An unknown label produces a warning and is kept as written.
- Output is JSON and CSV in a deterministic order.

Acceptance tests (`scripts/test_parser.py`):

1. **Count test** — dialogue lines parsed per episode equal an independent count of labeled blocks with quoted text.
2. `end > start` for every dialogue line, otherwise the line is reported.
3. No dialogue record has an empty speaker or empty text.
4. All six episodes parse with zero silent drops, and the report lists every warning.
5. **Header drift test** — the uppercase-heading episode and the en-dash episode parse correctly.
6. **New-format test** — a deliberately malformed sample produces a clear format report, not a crash and not silently wrong output. This matters because the interview run may use a new show.

## 8. Pack format compatibility

If a real Kuku episode is handed over during the interview, `src/parser.py` can be pointed at a local folder path. Rules for that:

- the pack stays outside the repository, never committed, never uploaded, never pasted into the doc;
- output of a pack run goes to a throwaway directory and is not part of the submission;
- the demo continues to run on our own screenplay;
- any question about pack data is answered by re-running the parser in front of the interviewer, not by sharing a file.

## 9. Phase 0 sample plan (100 lines)

- Source: all six episodes of `data/screenplay/`.
- Do **not** take the first 100 lines — take about 17 per episode with a recorded random seed, then enforce these minimums (`scripts/sample_lines.py` fails loudly if one is unmet):
  - ≥15 lines with slots under 1.5 s
  - ≥3 whole split-sentence chains
  - ≥5 voice-over or off-screen lines
  - ≥10 lines at address-shift moments
  - ≥10 threats or accusations, for the meaning-drift test
  - ≥10 tender or intimate lines, for the register test
  - ≥5 long lines of 12 words or more
- Keep whole chains together even if that nudges the total.
- Store the selection (`data/annotation/sample_selection.json`, seed recorded). Shuffle the order for blind annotation (`blind_annotation.csv`) and keep the stored order separately.
- Emotion and relationship columns ship with the blind sheet; QA results columns do **not**, so annotation cannot be primed.

## 10. Definition of done for the data work

- All six episodes parse, with a validation report showing zero silent drops.
- The alias map and relationship sheet are confirmed by the builder for every episode used in Phase 0.
- The 100-line sample is selected with a recorded seed and the minimums met.
- `results/format_report.json` holds the real totals, and §4 quotes them instead of the targets.
- Nothing in `data/`, `results/` or the submitted raw outputs derives from Kuku's pack.

## 11. Open items

1. Calibrate the Telugu reading rate with 10 lines read aloud (`PRD.md` §7.3 check 3).
2. Test two candidate models on Telugu before choosing a default; report both.
3. Write one paragraph on the Telugu register for the period setting, so the first pass and the QA share the same standard.
4. Re-run `scripts/format_report.py` after any screenplay edit.
5. Fill `docs/public_evidence.md` with citable public localization-quality examples; strike every UNVERIFIED line before submitting.
