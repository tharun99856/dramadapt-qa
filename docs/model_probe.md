# Model probe for Telugu

PRD section 3 lists this as an open item to resolve before choosing a default: *"test two models on
Telugu before choosing a default, because Telugu quality varies a lot between models."* Done on
6 November 2026 against a free-tier Groq key. Every line below is real model output, not a paraphrase.

## What this key can actually serve

`GET /models` on the account returns 11 entries. The chat-capable ones are:

| Model | Usable for Telugu? |
|---|---|
| `openai/gpt-oss-120b` | yes |
| `openai/gpt-oss-20b` | no - ran out of tokens before emitting Telugu |
| `qwen/qwen3.8-27b` | yes |
| `allam-2-7b` | Arabic/English focused, not tried for Telugu |
| `meta-llama/llama-prompt-guard-2-*` | classifiers, not chat |
| `canopylabs/orpheus-*`, `whisper-large-v3*` | speech models |

**`llama-3.1-8b-instant` is not on this account.** Requested by the builder, then verified: 404
`model_not_found` for `llama-3.1-8b-instant`, for `meta-llama/llama-3.1-8b-instant`, and for
`llama-3.3-70b-versatile`. It does not appear in the catalog listing either. This is the situation
`docs/public_evidence.md` already flagged as *critical* - "any cost figure or run using the 8B line
item is measuring a model that is no longer purchasable self-serve". We cannot benchmark a model the
free tier no longer serves, so the default moved to the strongest Telugu-capable model on the key.

Worth saying out loud, because it is also a PRD section 12 risk: an 8B-class first pass would have
made the error rate look worse than a production pipeline's would be. Using a 120B model is the
conservative choice - if the QA checks still find problems at that size, the problems are real.

## Side-by-side on four lines of the actual screenplay

Prompt: the fixed Step A instruction from `config.yaml`, temperature 0.

| English (slot) | `openai/gpt-oss-120b` | `qwen/qwen3.8-27b` |
|---|---|---|
| `The lamp stays lit.` (2.2 s) | `దీపం వెలిగినట్టే ఉంటుంది.` (10 akshara) | `వెలుగు ఆగదు.` (6) |
| `Promise me you will not sign her paper.` (3.4 s) | `దయచేసి, మీరు ఆమె పత్రాన్ని సంతకం చేయరని నాకొక వాగ్దానం చేయండి.` (27) | `ఆమె పత్రం సంతకం చేయకూడదు, మాట ఇవ్వండి.` (17) |
| `Father does not sign. That is the answer.` (1.8 s) | `తండ్రి సంతకం చేయడు. ఇదే సమాధానం.` (14) | `తండ్రి సంతకం చేయడు. ఇదే సమాధానం.` (14) |
| `Aunt. That is what you called me at Christmastide.` (1.8 s) | `అమ్మమ్మా, క్రిస్మస్ కాలంలో మీరు నన్ను ఇలా పిలిచారు.` (18) | `అమ్మమ్మ. క్రిస్మస్‌లో అలా పిలిచావు.` (12) |

## What the probe decided

1. **Default: `openai/gpt-oss-120b`.** Correct verb-final order, correct honorific plural with the
   father (`చేయడు` vs the plural forms elsewhere), Telugu script throughout. `gpt-oss-20b` cannot do
   the job at 700 output tokens, and 20B is the size a "small model" comparison would need anyway.
   **Comparison model: `qwen/qwen3.8-27b`,** set in `config.yaml` so Step A runs twice and PRD
   section 12's "one model flatters or damages the result" risk has a second data point.
2. **Both models make the same relationship error.** The instruction says explicitly *"do not convert
   English titles into Indian kinship terms"*, and both rendered Mistress Caine's "Aunt" as
   `అమ్మమ్మ` - **grandmother** - not `అత్తయ్య` (aunt by marriage). Two different model families, same
   mistake, against a written instruction. That is the strongest available argument that the
   relationship check is not decoration, and it is a finding about models generally, not about this
   screenplay.
3. **Both models overrun the slot, and the bigger one is worse.** 27 akshara for a 3.4 s slot needs
   roughly 8 akshara/s to fit, which nobody speaks. This is the timing check's whole premise, measured
   before the check was even run.
4. **Token accounting on `gpt-oss` includes reasoning tokens.** Two short lines cost 185 prompt /
   310 completion. Cost per line is therefore dominated by thinking, not by the Telugu, and that is
   why `batching.max_prompt_tokens` caps by tokens rather than by lines alone.

## The full 100-line Step A run, measured

Same fixed prompt, temperature 0, scene-batched, run on 6 November 2026. These are the API's own
usage figures from `results/run_log.json`, not estimates.

| Model | Requests | Prompt tokens | Completion tokens | Lines returned | Lines with **zero Telugu letters** |
|---|---|---|---|---|---|
| `openai/gpt-oss-120b` | 18 | 34,599 | 21,137 | 100 / 100 | **20** |
| `qwen/qwen3.8-27b` | 18 | 37,416 | 5,245 | 100 / 100 | **0** |

Only 9 of 100 lines come out identical between the two models, so the comparison is a real second
data point rather than a reroll.

**The 20 lines are the reason there is a fifth check.** They are not empty and they are not English
- they are Telugu words written in the Latin alphabet, e.g. `Meeru seal ki kooda layakaledu. Aameyi
teesukondi.` for `You are not worth a seal. Take her away.` A dubbing artist cannot read that on a
studio floor, and the timing check cannot count akshara in it, yet a general-purpose "review this
translation" prompt sees a correct Telugu sentence and says nothing. `src/checks/script.py` counts
letters instead of asking, costs zero model calls, and flags all 20 plus 2 mixed-script lines.
Nothing about this was predicted: it appeared only after the run was real.

`gpt-oss-120b` remains the default because it is the better translator on the four-line comparison
above and the script failure is caught mechanically; the comparison model is kept in `config.yaml`
so Step A runs twice and PRD section 12's "one model flatters or damages the result" risk stays
measurable.

Pricing is deliberately left `null` in `config.yaml`: this is a free-tier key, so the honest measured
figure is tokens, and `results/run_log.json` reports `cost_usd: null` with `priced: false` instead of
multiplying out a rate nobody charged us.
