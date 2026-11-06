# Phase 0 blind annotation sheet
#
# Fill in: verdict, error_types, severity, corrected_line, reviewer_confidence.
# verdict      : acceptable | needs_revision
# error_types  : any of meaning;relationship;timing;naturalness;script (semicolon separated, blank if acceptable)
# severity     : high | medium | low  (high = would wreck the scene if dubbed as it is)
# corrected    : your own Telugu line for that slot, not the machine's
# confidence   : high | medium | low  (how sure you are about your own judgement)
#
# Do NOT open results/structured_flags.json or results/baseline_flags.json before you finish this file.
# Judge the Telugu against the English and the slot. A line that is merely 'not how you would write it'
# but would play fine on screen is acceptable.
#
# generated: 2026-11-06T12:32:29+00:00
# sample seed: 20261106
# telugu file: data\telugu\first_pass.json
# telugu provenance: {"method": "api", "provider_base_url": "https://api.groq.com/openai/v1", "model": "openai/gpt-oss-120b", "temperature": 0, "generated": "2026-11-06T12:23:57+00:00", "sample_seed": 20261106, "measured": true, "note": "machine first pass - stand-in, not a human localization"}
# lines: 100 | already filled when this sheet was rebuilt: 0
