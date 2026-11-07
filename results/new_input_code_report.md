# DramAdapt QA report - new_input_code

Generated 2026-11-06T16:40:28+00:00. Model: `None`.

## Summary

- Lines reviewed: **34**
- Lines with Telugu attached: **34** of 34
- Checks completed: **2** of 2
- Lines flagged: **32**
- Flags by check: script=9, timing=24
- Flags by severity: high=28, medium=5
- Model coverage: no LLM check ran on this run
- Timing: rate **3.5** akshara/s (override passed on the command line - not calibrated), median estimate/slot ratio **2.338**, p90 3.175, max 5.079 - **92%** of measured lines overrun their slot by more than 15%. A share near 1.0 means this check is shortlisting nothing, so read the ratio before trusting the list.
- Requests: 0 for 3 scene batches (prompt tokens 0, completion tokens 0, cost None)

## Flagged lines

| flag | line | check | severity | verdict | English | Telugu | slot | evidence | suggestion | status |
|---|---|---|---|---|---|---|---|---|---|---|
| E01-L026_script | E01-L026 | script | high | not_in_telugu_script | You could have just signed. | Meeru sarigga sign chesina.  | 1.8 | no Telugu letters; 4 Latin words, detected script LATIN: 'Meeru sarigga sign chesina.' | re-render this line in Telugu script before it goes to the studio | pending |
| E01-L027_script | E01-L027 | script | high | not_in_telugu_script | I could have. It is a very short word. | Nenu chesanu. Idi chala chinna padam.  | 1.8 | no Telugu letters; 6 Latin words, detected script LATIN: 'Nenu chesanu. Idi chala chinna … | re-render this line in Telugu script before it goes to the studio | pending |
| E01-L028_script | E01-L028 | script | high | not_in_telugu_script | Then why did you not write it? | Appudu meeru enduku raayaledu?  | 1.8 | no Telugu letters; 4 Latin words, detected script LATIN: 'Appudu meeru enduku raayaledu?' | re-render this line in Telugu script before it goes to the studio | pending |
| E01-L029_script | E01-L029 | script | high | not_in_telugu_script | Because somebody has to be the one who did not. | Endukante, oka vadu raayakunda undali.  | 2.4 | no Telugu letters; 5 Latin words, detected script LATIN: 'Endukante, oka vadu raayakunda … | re-render this line in Telugu script before it goes to the studio | pending |
| E01-L030_script | E01-L030 | script | high | not_in_telugu_script | Aparna. | Aparna.  | 1.6 | no Telugu letters; 1 Latin words, detected script LATIN: 'Aparna.' | re-render this line in Telugu script before it goes to the studio | pending |
| E01-L031_script | E01-L031 | script | high | not_in_telugu_script | Don't use that here. | Idi ikkada vadakandi.  | 1.6 | no Telugu letters; 3 Latin words, detected script LATIN: 'Idi ikkada vadakandi.' | re-render this line in Telugu script before it goes to the studio | pending |
| E01-L032_script | E01-L032 | script | high | not_in_telugu_script | Nobody is in a stairwell for the cameras. | Kameralu kosam stairwell lo evaru levaru.  | 1.8 | no Telugu letters; 6 Latin words, detected script LATIN: 'Kameralu kosam stairwell lo eva… | re-render this line in Telugu script before it goes to the studio | pending |
| E01-L033_script | E01-L033 | script | high | not_in_telugu_script | You are the second person tonight who has told me where I am allowed to be honest. | Meeru raatri lo nannu nijam cheppadaniki anumatam ichina rendu vyakti lo rendu.  | 2.2 | no Telugu letters; 12 Latin words, detected script LATIN: 'Meeru raatri lo nannu nijam ch… | re-render this line in Telugu script before it goes to the studio | pending |
| E01-L034_script | E01-L034 | script | high | not_in_telugu_script | I will be last. | Nenu kooda aakhiri ga untanu.  | 1.6 | no Telugu letters; 5 Latin words, detected script LATIN: 'Nenu kooda aakhiri ga untanu.' | re-render this line in Telugu script before it goes to the studio | pending |
| E01-L020_timing_overlaps_next_line | E01-L020 | timing | high | overlaps_next_line | You will sign it, or I will find someone who has. | మీరు దాన్ని సంతకం చేస్తారు, లేక నేను ఇప్పటికే సంతకం చేసినవారిని కనుగొంటాను. ~9.143s/32ak | 1.8 | estimate 9.14s > loose window 2.20s (tight slot 1.80s, 5.08x the slot, 32 akshara at 3.5/… | cut about 24 akshara | pending |
| E01-L009_timing_overlaps_next_line | E01-L009 | timing | high | overlaps_next_line | That he used your silence as a signature. | అతను మీ నిశ్శబ్దాన్ని సంతకంగా ఉపయోగించాడు. ~5.143s/18ak | 1.6 | estimate 5.14s > loose window 3.80s (tight slot 1.60s, 3.21x the slot, 18 akshara at 3.5/… | cut about 5 akshara | pending |
| E01-L018_timing_overlaps_next_line | E01-L018 | timing | high | overlaps_next_line | They are close enough for a hospital. | వీటిని ఆసుపత్రి కోసం సరిపడా దగ్గరగా ఉన్నాయి. ~5.714s/20ak | 1.8 | estimate 5.71s > loose window 2.20s (tight slot 1.80s, 3.17x the slot, 20 akshara at 3.5/… | cut about 12 akshara | pending |
| E01-L021_timing_overlaps_next_line | E01-L021 | timing | high | overlaps_next_line | Then you have already signed it. | అప్పుడు మీరు ఇప్పటికే దాన్ని సంతకం చేశారు. ~4.857s/17ak | 1.6 | estimate 4.86s > loose window 2.00s (tight slot 1.60s, 3.04x the slot, 17 akshara at 3.5/… | cut about 10 akshara | pending |
| E01-L013_timing_overlaps_next_line | E01-L013 | timing | high | overlaps_next_line | The family has a patient, Sir. Not a picture. | కుటుంబానికి ఒక రోగి ఉంది, సార్. ఇది చిత్రము కాదు. ~5.429s/19ak | 1.8 | estimate 5.43s > loose window 2.20s (tight slot 1.80s, 3.02x the slot, 19 akshara at 3.5/… | cut about 11 akshara | pending |
| E01-L004_timing_over_slot | E01-L004 | timing | medium | over_slot | Then I will be unofficial. | అప్పుడు నేను అధికారికంగా ఉండను. ~4.0s/14ak | 1.4 | estimate 4.00s exceeds the 1.40s slot by more than 15% (2.86x the slot, 14 akshara at 3.5… | trim to 5 akshara or less | pending |
| E01-L007_timing_overlaps_next_line | E01-L007 | timing | high | overlaps_next_line | He is quick about the parts with cameras. | కెమెరాలు ఉన్న భాగాల్లో ఆయన త్వరగా ఉంటాడు. ~5.143s/18ak | 1.8 | estimate 5.14s > loose window 2.20s (tight slot 1.80s, 2.86x the slot, 18 akshara at 3.5/… | cut about 10 akshara | pending |
| E01-L023_timing_overlaps_next_line | E01-L023 | timing | high | overlaps_next_line | That you asked the wrong person to be brave ... | మీరు తప్పు వ్యక్తిని ధైర్యంగా ఉండమని అడిగారు... ~5.143s/18ak | 1.8 | estimate 5.14s > loose window 2.20s (tight slot 1.80s, 2.86x the slot, 18 akshara at 3.5/… | cut about 10 akshara | pending |
| E01-L008_timing_overlaps_next_line | E01-L008 | timing | high | overlaps_next_line | Say what you actually mean, Sunny. | మీరు నిజంగా చెప్పదలిచినది చెప్పండి, సన్నీ. ~4.857s/17ak | 1.8 | estimate 4.86s > loose window 2.20s (tight slot 1.80s, 2.70x the slot, 17 akshara at 3.5/… | cut about 9 akshara | pending |
| E01-L016_timing_overlaps_next_line | E01-L016 | timing | high | overlaps_next_line | You transfer out on Friday. Do not make this your last impression. | మీరు శుక్రవారం బదిలీ అవుతారు. ఇది మీ చివరి ముద్రగా మార్చకండి. ~7.429s/26ak | 2.8 | estimate 7.43s > loose window 5.60s (tight slot 2.80s, 2.65x the slot, 26 akshara at 3.5/… | cut about 6 akshara | pending |
| E01-L001_timing_overlaps_next_line | E01-L001 | timing | high | overlaps_next_line | Bed four is asking for you again. | బెడ్ నాలుగు మిమ్మల్ని మళ్లీ అడుగుతోంది. ~4.0s/14ak | 1.6 | estimate 4.00s > loose window 2.00s (tight slot 1.60s, 2.50x the slot, 14 akshara at 3.5/… | cut about 7 akshara | pending |
| E01-L012_timing_overlaps_next_line | E01-L012 | timing | high | overlaps_next_line | The family already has the wheelchair ramp. That is the picture. | కుటుంబానికి ఇప్పటికే వీల్‌చెయిర్ ర్యాంప్ ఉంది. అది చిత్రమే. ~5.714s/20ak | 2.4 | estimate 5.71s > loose window 2.80s (tight slot 2.40s, 2.38x the slot, 20 akshara at 3.5/… | cut about 10 akshara | pending |
| E01-L014_timing_overlaps_next_line | E01-L014 | timing | high | overlaps_next_line | We are all on the same side of this, Doctor. | మేము అందరం దీనిలో ఒకే వైపు ఉన్నాం, డాక్టర్ గారు. ~5.143s/18ak | 2.2 | estimate 5.14s > loose window 2.60s (tight slot 2.20s, 2.34x the slot, 18 akshara at 3.5/… | cut about 9 akshara | pending |
| E01-L005_timing_overlaps_next_line | E01-L005 | timing | high | overlaps_next_line | Sir put his name on the discharge before you saw it. | సర్ మీరు చూసే ముందు డిశ్చార్జ్‌పై తన పేరు పెట్టాడు. ~4.857s/17ak | 2.2 | estimate 4.86s > loose window 2.60s (tight slot 2.20s, 2.21x the slot, 17 akshara at 3.5/… | cut about 8 akshara | pending |
| E01-L019_timing_overlaps_next_line | E01-L019 | timing | high | overlaps_next_line | Close enough is what people die of. | దగ్గరగా ఉండటం, ప్రజలు మరణించే కారణం. ~4.857s/17ak | 2.2 | estimate 4.86s > loose window 2.60s (tight slot 2.20s, 2.21x the slot, 17 akshara at 3.5/… | cut about 8 akshara | pending |
| E01-L002_timing_over_slot | E01-L002 | timing | medium | over_slot | Bed four always is. | బెడ్ నాలుగు ఎప్పుడూ అడుగుతుంది. ~3.429s/12ak | 1.6 | estimate 3.43s exceeds the 1.60s slot by more than 15% (2.14x the slot, 12 akshara at 3.5… | trim to 6 akshara or less | pending |
| E01-L023_timing_chain_over_slot | E01-L023 | timing | medium | chain_over_slot | That you asked the wrong person to be brave ... | మీరు తప్పు వ్యక్తిని ధైర్యంగా ఉండమని అడిగారు... ~5.143s/18ak | 1.8 | chain C01-001 (E01-L023, E01-L024) estimated 7.14s against 3.40s of combined slot (2.10x) | translate the whole chain as one Telugu sentence, then split it at a natural break | pending |
| E01-L006_timing_overlaps_next_line | E01-L006 | timing | high | overlaps_next_line | Sir is quick about things. | సర్ విషయాల్లో త్వరగా ఉంటాడు. ~3.143s/11ak | 1.6 | estimate 3.14s > loose window 2.00s (tight slot 1.60s, 1.96x the slot, 11 akshara at 3.5/… | cut about 4 akshara | pending |
| E01-L015_timing_overlaps_next_line | E01-L015 | timing | high | overlaps_next_line | Then read me the note. | అప్పుడు నోట్‌ను నాకు చదవండి. ~3.143s/11ak | 1.6 | estimate 3.14s > loose window 2.00s (tight slot 1.60s, 1.96x the slot, 11 akshara at 3.5/… | cut about 4 akshara | pending |
| E01-L017_timing_overlaps_next_line | E01-L017 | timing | high | overlaps_next_line | Those are not my initials. | అవి నా ఆరంభ అక్షరాలు కాదు. ~3.429s/12ak | 1.8 | estimate 3.43s > loose window 2.20s (tight slot 1.80s, 1.90x the slot, 12 akshara at 3.5/… | cut about 4 akshara | pending |
| E01-L003_timing_overlaps_next_line | E01-L003 | timing | high | overlaps_next_line | You are not supposed to take those calls tonight. | ఈ రాత్రి మీరు ఆ కాల్స్ తీసుకోవద్దు. ~3.429s/12ak | 2.0 | estimate 3.43s > loose window 2.40s (tight slot 2.00s, 1.71x the slot, 12 akshara at 3.5/… | cut about 4 akshara | pending |
| E01-L025_timing_over_slot | E01-L025 | timing | medium | over_slot | Both of you, my office, Monday. | మీ ఇద్దరూ, నా కార్యాలయం, సోమవారం. ~3.714s/13ak | 2.4 | estimate 3.71s exceeds the 2.40s slot by more than 15% (1.55x the slot, 13 akshara at 3.5… | trim to 9 akshara or less | pending |
| E01-L010_timing_overlaps_next_line | E01-L010 | timing | high | overlaps_next_line | I did not sign anything. | నేను ఏదీ సంతకం చేయలేదు. ~3.143s/11ak | 2.2 | estimate 3.14s > loose window 2.60s (tight slot 2.20s, 1.43x the slot, 11 akshara at 3.5/… | cut about 2 akshara | pending |
| E01-L024_timing_over_slot | E01-L024 | timing | medium | over_slot | ... on your last night. | ... మీ చివరి రాత్రిలో. ~2.0s/7ak | 1.6 | estimate 2.00s exceeds the 1.60s slot by more than 15% (1.25x the slot, 7 akshara at 3.5/… | trim to 6 akshara or less | pending |

## Not flagged

E01-L011, E01-L022

## Reading this report

- Timing flags are risk against the English performance window, not failure: dubbing can retime a line.
- Naturalness flags are advisory only and carry no score.
- Nothing here is auto-approved. Every flag needs an editor action.
- Akshara counts in the timing column are machine counts of Telugu syllables by `src/telugu.py`: one per base letter, minus one per virama, so a conjunct counts once.
- Every line was read by every check that could run on it.
