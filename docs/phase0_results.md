# Phase 0 result

Written 2026-11-07T07:59:01+00:00 by `scripts/score.py`. Every figure below is computed from `blind_annotation.csv` (the reviewer's blind annotation) and the two run files.

## What the reviewer found

- Lines needing revision: **81 of 100**
- Issue types: meaning=46, naturalness=58, relationship=11, script=24, timing=19
- Evaluator: one Telugu evaluator (the builder), one language, 100 lines. No inter-rater agreement is claimed. Provenance of these verdicts, stated plainly because it affects how much weight they carry: they were recorded in ten batches in a chat session with an AI assistant, and a share of them were recorded against a grade the assistant drafted and the reviewer then reviewed, changed or accepted. The reviewer approved every row, so the judgement on the sheet is the reviewer's, but this is human-reviewed AI-suggested annotation, not independent human annotation, and it must not be described as that. One block (rows 61-70) was first graded against ten lines the assistant invented and has been re-graded against the file; see docs/failure_log.md entry 22.

## Reviewer standard, as decided (data/relationship_sheet.yaml, read at run time)

- Status: PART-SIGNED-OFF - two decisions are the reviewer's own (see reviewer_decisions); the rest of draft_paragraph is still unconfirmed against the episodes
- Joss Marek addresses Edda Halloran with the singular informal నువ్వు in every episode, because he is a rough bargeman speaking to a young woman he is close to - the reviewer's decision of 2026-11-07, which supersedes the draft note limiting the informal form to episode 4 onward.
- Name spellings: caine=కేన్, halloran=హల్లొరాన్
- The Step A draft column keeps its own variants on purpose: it is byte-identical to `data/telugu/first_pass.json`, and saved flags quote it, three of them `script` flags that exist only because the draft left a name in Latin script. Normalising it there would break that evidence, so the standard is recorded as a decision, not written over the output.

## The two systems on identical inputs

Two readings are given because they answer different questions. Instance coverage asks how much of what the reviewer found each system named; line level asks whether the system put a flag on a line the reviewer marked, which is what a dubbing director actually experiences.

| system | flags | precision | instances credited | recall (instances) | issue lines found | line recall | line precision | false positives |
|---|---|---|---|---|---|---|---|---|
| DramAdapt structured | 174 | 0.506 | 86/158 | 0.544 | 80/81 | 0.988 | 0.879 | 86 |
| generic single-prompt baseline | 58 | 0.897 | 109/158 | 0.69 | 52/81 | 0.642 | 0.897 | 6 |

Recall here is instances credited over instances reported. The figure previously submitted as "recall" divided a flag count by a mixed denominator and read 0.55 for structured and 0.248 for baseline against a true instance count of 158; both arms' old denominators (160 and 210) counted something other than reviewer issues.

## Per check

| check | flags | precision | of its own type | type recall | overall recall | false positives |
|---|---|---|---|---|---|---|
| meaning | 13 | 0.846 | 10/46 | 0.217 | 0.063 | 2 |
| naturalness | 49 | 0.633 | 31/58 | 0.534 | 0.196 | 18 |
| relationship | 21 | 0.238 | 5/11 | 0.455 | 0.032 | 16 |
| script | 22 | 1.0 | 22/24 | 0.917 | 0.139 | 0 |
| timing | 69 | 0.275 | 18/19 | 0.947 | 0.114 | 50 |

## Comparison at similar precision

Baseline precision is 0.897. At that precision or better, structured QA reaches recall n/a (severity cut: n/a).

Severity sweep, structured:

- keep >= high: 84 flags, precision 0.536, recall 0.285
- keep >= medium: 125 flags, precision 0.456, recall 0.348
- keep >= low: 174 flags, precision 0.506, recall 0.544

## Reviewer acceptance rate

Not measured yet: no acceptance decisions have been recorded. This is the metric that shows
whether a flag is *useful*, not just whether it fires - fill in the acceptance sheet and re-run.

Sheet: `python scripts/make_acceptance_sheet.py`

## Seeded errors (separate from the main result)

**Not measured.** structured_seeded_flags.json does not exist, so nothing here was run against the seeded draft. The 9 edits in seeded_manifest.json were never scored.

To run it for real: `python scripts/run_seeded.py && python scripts/run_structured.py --telugu-file data/telugu/first_pass_seeded.json --label structured_seeded`


## Thresholds and decision

- **genuine_issues_at_least_10**: PASS - {"value": 81}
- **structured_recall_at_least_0_5**: PASS - {"value": 0.544, "basis": "reviewer (line, type) instances credited / instances the reviewer reported", "value_legacy_flagcount": 0.55}
- **structured_beats_baseline_at_similar_precision**: FAIL - {"baseline_precision": 0.897, "baseline_recall": 0.69, "structured_at_that_precision": {"available": false, "target_precision": 0.897, "reason": "no severity cut reaches that precision", "points": [{"at_least": "high", "flags": 84, "precision": 0.536, "recall": 0.285}, {"at_least": "medium", "flags": 125, "precision": 0.456, "recall": 0.348}, {"at_least": "low", "flags": 174, "precision": 0.506, "recall": 0.544}]}}
- **false_positives_reported**: PASS - {"structured": 86, "baseline": 6}
- **naturalness_precision_reported_separately**: PASS - {"value": 0.633}
- **acceptance_rate_available**: FAIL - {"checks_with_decisions": []}
- **line_level_reported**: PASS - {"structured": {"issue_lines_found": 80, "issue_lines_total": 81, "recall": 0.988, "precision": 0.879}, "baseline": {"issue_lines_found": 52, "issue_lines_total": 81, "recall": 0.642, "precision": 0.897}, "note": "did the system put any flag on a line the reviewer marked, and how many of the lines it touched were ones the reviewer marked - the operational reading"}
- **instance_coverage_reported**: PASS - {"structured": "86/158", "baseline": "109/158", "note": "one untyped baseline flag credits every type the reviewer named on that line, so the baseline leads on this row while flagging fewer issue lines"}

**Decision: NO-GO**

## Caveats

- acceptance rate not measured: no decisions recorded yet
- seeded errors not measured: no run against the seeded draft exists, so any seeded number in a document is unsupported

Checks to drop: relationship (low precision, or the reviewer keeps dismissing them).

## False positives, by hand

Every flag below was judged as a false positive by the reviewer. Listing them is the honest part of the result.

| line | speaker | English | Telugu |
|---|---|---|---|
| E01-L001 | Edda Halloran | The lamp stays lit. | దీపం వెలిగేలా ఉంది. |
| E01-L003 | Edda Halloran | I set it down an hour ago. | నేను దాన్ని ఒక గంటకు ముందు పెట్టాను. |
| E01-L006 | Halloran (Edda's father) | Promise me you will not sign her paper. | వాగ్దానం చేయి, నీవు ఆమె పత్రాన్ని సంతకం చేయవద్దు. |
| E01-L014 | Mistress Caine | The debt is mine, the deed is mine, the winter is mine. | బాకీ నా, ఒప్పందం నా, శీతాకాలం నా. |
| E01-L015 | Edda Halloran | Say it once more. | దయచేసి, మళ్ళీ ఒకసారి చెప్పండి. |
| E01-L017 | Joss Marek | Tell that to the tide, Mistress. | ఆ మాటను జలానికి చెప్పండి, Mistress. |
| E01-L021 | Edda Halloran | By your authority. Yes. | మీ అధికారంతో. అవును. |
| E01-L024 | Silas Vane | She always says no ... | మిస్ హాలొరన్, ఆమె ఎప్పుడూ 'లేదు' అంటుంది... |
| E01-L025 | Silas Vane | ... until the price is right. | ... ధర సరైనంత వరకు. |
| E01-L026 | Halloran (Edda's father) | Edda, my girl, do not ... | ఎడ్డా, నా అమ్మాయా, చేయవద్దు... |
| E01-L027 | Halloran (Edda's father) | ... sign nothing tonight. | ... ఈ రాత్రి ఏదీ సంతకం చేయకు. |
| E02-L004 | Joss Marek | Ticket burnt with the ship. | టికెట్ నౌకతో కాలిపోయింది. |
| E02-L006 | Edda Halloran | So it is you filling his head. | అలా అయితే, మీరు, Marek, అతని తల నింపుతున్నారా? |
| E02-L007 | Joss Marek | His head was full already. | అతని తల ఇప్పటికే నిండిపోయింది. |
| E02-L009 | Company clerk (Caine's man, grey coat) | Mistress Caine will hear of this. | Mistress Caine దీనిని వినిపిస్తారు. |
| E02-L010 | Delia | Eat, love. He will want you standing. | తిను, ప్రియ. అతను నిన్ను నిలబడి ఉండాలని కోరుతాడు. |
| E02-L011 | Edda Halloran | He wants the lamp. | అతను దీపాన్ని కోరుకుంటున్నారు. |
| E02-L013 | Edda Halloran | That is the same thing. | అది అదే విషయం. |
| E02-L015 | Brother Anselm | Miss Halloran. The company offers charity for the keeper's w | మిస్ హల్లొరాన్, కంపెనీ కీపర్ శీతాకాలానికి దానం అందిస్తోంది. |
| E02-L020 | Edda Halloran | Father does not sign. That is the answer. | తండ్రి సంతకం చేయడు. అది సమాధానం. |
| E02-L026 | Joss Marek | Your father taught me to read a gate in '61. | Mee thandri naaku 61 lo darwaza chadavadam nerpindi. |
| E02-L028 | Edda Halloran | Hush now, Father. I am here. | Shanthamga undi, Nanna. Nenu ikkada unna. |
| E02-L031 | Joss Marek | Lock the gate, Edda. It is you he means. | Darwaza nilipi, Edda. Aadani artham meeru. |
| E03-L002 | Edda Halloran | I have an hour, Mistress Caine. | Naaku oka gaṇṭa undi, Mistress Caine. |
| E03-L003 | Mistress Caine | You have the tide. It is less. | Mee daggara aapada undi. Adi takkuva. |
| E03-L008 | Edda Halloran | He bought them. | Avaadu vatini konnaadu. |
| E03-L010 | Edda Halloran | What do you want, Silas, out of a dead man's paper? | Silas Vane, mruthyu vyakti patra nundi meeru emi korukuntunn |
| E03-L014 | Joss Marek | Someone did. From the stair. | ఎవరో చేశారు. మెట్ల నుండి. |
| E03-L017 | Joss Marek | Your light is my work. | నీ వెలుగు నా పని. |
| E03-L018 | Edda Halloran | Then tell me what a '61 inquiry letter costs a keeper's daug | మారెక్, ‘61 విచారణ లేఖ ఒక కీపర్ కుమార్తెకు ఎంత ఖర్చవుతుందో చ |
| E03-L024 | Edda Halloran | Aunt would have said that nicer. | అంటీ, అది మరింత బాగుగా చెప్పేవారు. |
| E03-L025 | Halloran (Edda's father) | You went to the house. My girl, why did you go? | నీవు ఇంటికి వెళ్లావు, నా అమ్మాయి. ఎందుకు వెళ్లావు? |
| E03-L029 | Edda Halloran | I will not let them take it. | నేను వాళ్లు దాన్ని తీసుకెళ్లనివ్వను. |
| E03-L030 | Halloran (Edda's father) | Say it as a promise, not a ... | దాన్ని వాగ్దానంగా చెప్పు, సవాల్‌గా కాదు— |
| E03-L031 | Edda Halloran | ... a dare. I hear you, Father. | నేను వినుతున్నాను, నాన్నా. |
| E04-L001 | Edda Halloran | Keep it turning. Keep it turning. | తిరుగుతూ ఉండు. తిరుగుతూ ఉండు. |
| E04-L004 | Joss Marek | LIGHT THE STAIR! Somebody light the stair! | సీడీని వెలిగించండి! ఎవరో సీడీని వెలిగించండి! |
| E04-L006 | Joss Marek | Then he'll be wet and right, in that order. | అప్పుడు అతను తడిగా, సరైనవాడిగా ఉంటుంది, ఆ క్రమంలో. |
| E04-L007 | Edda Halloran | Turn to him. Turn to him, he is my father's water. | తిరుగు అతనికి. తిరుగు అతనికి, అతను నా తండ్రి నీరు. |
| E04-L009 | Edda Halloran | Nobody's. The bar held. | ఎవరికి కూడా కాదు. బార్ నిలిచింది. |

## Missed issues

- E01-L001 (meaning)
- E01-L004 (meaning)
- E01-L004 (naturalness)
- E01-L005 (naturalness)
- E01-L006 (naturalness)
- E01-L014 (meaning)
- E01-L017 (meaning)
- E01-L024 (meaning)
- E01-L025 (naturalness)
- E01-L026 (naturalness)
- E01-L029 (meaning)
- E01-L030 (naturalness)
- E02-L006 (script)
- E02-L007 (meaning)
- E02-L007 (naturalness)
- E02-L010 (naturalness)
- E02-L013 (naturalness)
- E02-L020 (naturalness)
- E02-L026 (meaning)
- E02-L028 (meaning)
- E02-L030 (meaning)
- E02-L030 (naturalness)
- E02-L031 (meaning)
- E03-L003 (meaning)
- E03-L006 (meaning)
- E03-L008 (naturalness)
- E03-L010 (meaning)
- E03-L011 (meaning)
- E03-L011 (timing)
- E03-L012 (naturalness)
- E03-L014 (meaning)
- E03-L018 (meaning)
- E03-L023 (meaning)
- E03-L024 (meaning)
- E03-L024 (naturalness)
- E03-L025 (naturalness)
- E03-L031 (naturalness)
- E04-L001 (meaning)
- E04-L006 (meaning)
- E04-L007 (meaning)
- E04-L013 (meaning)
- E04-L015 (naturalness)
- E04-L017 (meaning)
- E04-L025 (naturalness)
- E04-L027 (meaning)
- E04-L027 (relationship)
- E05-L003 (meaning)
- E05-L003 (naturalness)
- E05-L007 (naturalness)
- E05-L011 (naturalness)
- E05-L014 (relationship)
- E05-L017 (meaning)
- E05-L017 (naturalness)
- E05-L019 (naturalness)
- E05-L022 (meaning)
- E05-L022 (relationship)
- E05-L027 (script)
- E05-L032 (meaning)
- E06-L002 (meaning)
- E06-L004 (meaning)

## Cost actually spent

- structured: {"requests_total": 73, "requests_measured": 73, "requests_unmeasured_provenance": 0, "by_kind": {"meaning": 18, "relationship": 18, "naturalness": 37}, "prompt_tokens": 88128, "completion_tokens": 80891, "cost_usd": null, "priced": false, "models": ["openai/gpt-oss-120b"]}
- baseline: {"requests_total": 18, "requests_measured": 18, "requests_unmeasured_provenance": 0, "by_kind": {"baseline": 18}, "prompt_tokens": 9633, "completion_tokens": 14990, "cost_usd": null, "priced": false, "models": ["openai/gpt-oss-120b"]}
