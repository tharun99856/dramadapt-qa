# Parser validation report

## Summary

- files: 6
- blocks: 259
- non_dialogue_blocks: 75
- dialogue_lines: 184
- chains: 3
- voice_over: 8
- off_screen: 8
- canonical_speakers: 11

## Acceptance tests

- count episode-001.txt: parser=32 independent=32
- count episode-002.txt: parser=32 independent=32
- count episode-003.txt: parser=34 independent=34
- count episode-004.txt: parser=28 independent=28
- count episode-005.txt: parser=34 independent=34
- count episode-006.txt: parser=24 independent=24
- end>start for all lines: PASS
- no empty speaker/text: PASS
- silent drops: 0 | alias-map misses: 0 | total warnings: 3
- header drift (episode-004 en dash heading parsed): PASS
- new-format fixture: parsed=1 reported_warnings=5 (no crash)

## Result

PASS

## Warnings

- `episode-002.txt:161` [fragment] E02-L025 trails off with no following fragment
- `episode-002.txt:161` [fragment] E02-L025 starts mid-sentence with no previous fragment
- `episode-005.txt:124` [fragment] E05-L023 starts mid-sentence with no previous fragment
