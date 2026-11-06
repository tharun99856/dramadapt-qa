# Corpus statistics (our own screenplay)

Measured by `scripts/corpus_stats.py` over 6 episode files in `data/screenplay/`.
Every figure here is ours; none of it comes from Kuku's confidential input pack.

- Dialogue lines: **184** (per episode: ep1=32, ep2=32, ep3=34, ep4=28, ep5=34, ep6=24)
- Tight slot per line: median **2.6 s**, mean 2.512 s, min 1.2 s, max 5.0 s
- Lines in slots under 1.5 s: **19 (10%)**
- English line length: median 7.5 words, mean 7.897, max 18.0
- English speaking rate (slots >= 1 s): median **3.182 words/s**, p90 4.118, max 5.833
- Gap between one line's end and the next start: median 0.6 s, p90 2.8 s; consecutive overlaps: 1
- Split-sentence chains: **3** (interlocked=2, same-speaker=4)
- Voice-over lines: 8 | off-screen lines: 8
- Speaker labels as written: 13 | canonical characters after the alias map: 11
- Lines of 12 words or more: 25
- Loose window minus tight window: median 0.6 s (this is the slack a dubbing line can borrow before it collides with the next line)

## Canonical characters

- Brother Anselm
- Company clerk (Caine's man, grey coat)
- Company clerk (shipping office, grey beard)
- Constable Roe
- Delia
- Edda Halloran
- Halloran (Edda's father)
- Joss Marek
- Mistress Caine
- Silas Vane
- Voice of the lamp

## What these numbers are used for

- The slot distribution sets the timing thresholds: with 10% of lines under 1.5 s, short slots are over-sampled in Phase 0.
- The speaking rate is the English baseline the Telugu/English duration ratio is reported against.
- The overlap count is why the timing check reports risk against two windows instead of one.
- The chain count is why the meaning check runs on chains, not fragments.
