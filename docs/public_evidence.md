# Public evidence log — DramAdapt QA

Every claim here is from a public source, independent of any Kuku material. Access date for all URLs: **2026-11-06**.
Rule: nothing marked UNVERIFIED may appear in the two-page doc or be cited in the walkthrough.

## A. Localization / dubbing quality in short-form drama

1. ReelShort lists English plus 21 additional languages; DramaBox English plus 15 additional languages. DramaBox library ≈2,000+ dubbed/translated Chinese-origin titles; ReelShort ≈200+ English originals.
   — https://dodofanz.com/blog/reelshort-vs-dramabox/ ; https://filmustage.com/blog/short-drama-apps-compared-reelshort-vs-dramabox-in-2026/
   *Status: secondary sources, app-store-derived. Use as "reported", not "audited".*
2. Dubbing is thin relative to the language claims: AppGrowing ad-intelligence counts DramaBox running seven to eight dub language tags across at least 14 titles, while ReelShort relies mainly on subtitle overlays with only three to four titles explicitly dubbed.
   — https://appgrowing.net/blog/dramabox-vs-reelshort-two-short-drama-ad-playbooks-in-the-same-month
   *Status: usable. This is the strongest public support for "a language label is not a finished localization" — which is the gap DramAdapt QA sits in.*
3. Practitioner statement on failure mode: "Many teams still treat localization as an afterthought. That approach regularly produces subtitles that obscure faces, dialogue that feels stiff."
   — https://artlangs.com/news-detail/Navigating-Vertical-Short-Drama-Translation-for-Platforms-Like-ReelShort-and-DramaBox
   *Status: usable as a practitioner view, not as data.*
4. Throughput claim: FlexTV localized into 12+ languages with "one person handles 10 episodes a day to 100" and costs cut "over 80%".
   — https://www.allvoicelab.com/blog/flextv-scaled-multilingual-content-production-with-allvoicelab
   *Status: VENDOR-AUTHORED MARKETING CASE STUDY. Do not cite the numbers. Cite at most "vendors advertise order-of-magnitude throughput gains from AI localization, which is why a quality gate matters" and name it as vendor-authored.*
5. Viewer complaint, anecdotal: "Some that are English dub. The AI voices are HORRIBLE."
   — https://www.reddit.com/r/Filmmakers/comments/1hj8rww/short_dramas_please_help_me_understand/
   *Status: ANECDOTE. Non-expert, unverifiable. May appear only as "viewer complaints exist", never as a count.*
6. Indian analogue: Kadhai Shorts, described as India's first dedicated Tamil vertical micro-drama platform, 9:16, 1–2 minute episodes, new episodes weekly.
   — https://kadhaishorts.com/
   *Status: self-description by the company. Usable for format/length facts, not for market size.*

**Search that came back empty — record it so nobody repeats it:** no working public source was found reporting a **Telugu- or Tamil-specific** dubbing/translation complaint for ReelShort, DramaBox, ShortMax, FlexTV, GoodShort or MoboReels, and no audited episodes-per-month figure for any of them. UNVERIFIED. Do not imply such a source exists.

## B. Model choice, cost and the Telugu capability caveat

7. **`llama-3.1-8b-instant` is deprecated.** Groq announced 2026-06-17 and shut it down 2026-08-16 for free and developer tiers, recommending `openai/gpt-oss-20b`. `llama-3.3-70b-versatile` likewise retires toward `gpt-oss-120b` / `qwen/qwen3.6-27b`.
   — https://console.groq.com/docs/deprecations
   *Status: critical. Any cost figure or run using the 8B line item is measuring a model that is no longer purchasable self-serve.*
8. Both deprecated models now show "Enterprise — Contact Sales" in Groq's live pricing table; no public per-token price exists for them. Currently priced self-serve: `openai/gpt-oss-20b` $0.075 in / $0.30 out per 1M; `openai/gpt-oss-120b` $0.15 / $0.60; `qwen/qwen3.8-27b` $0.80 / $4.00.
   — https://console.groq.com/docs/models
9. Free-tier limits, per model: `gpt-oss-20b` and `gpt-oss-120b` = 30 requests/minute, 1,000 requests/day, 8,000 tokens/minute, 200,000 tokens/day.
   — https://console.groq.com/docs/rate-limits
   *Status: design constraint. The 8K TPM ceiling, not cost, is what forces scene batching to be capped by tokens rather than by scene alone.*
10. Last widely-listed 8B price, $0.05 in / $0.08 out per 1M, is **historical and not officially confirmed** for a live endpoint.
    — https://www.layer3labs.io/guides/groq-pricing ; https://www.cloudzero.com/blog/groq-pricing/
    *Status: UNVERIFIED against Groq. Never put this number in the doc.*

11. **TeluguEval** (Gundam & Mamidi, LoResLM @ ACL 2026, pp. 212–224), English→Telugu accuracy, Table 1: Llama-3.1-8B falls from GSM8K 90.95 → 48.10, ARC-Easy 91.5 → 36.0, Winogrande 66.0 → 56.0, CaseHOLD 58.99 → 33.09. Sarvam-m-24B holds GSM8K(Te) 86.67 and ARC(Te) 86.5; Gemini-2.0-Flash GSM8K(Te) 91.90. Authors: "only Sarvam-m and Gemini maintained accuracy above 75% on Telugu inputs. All other models, including Meta's 8B models, fell below 50%." Reported failure modes: script sensitivity, option-selection bias, repetition loops, unintended code-switching.
    — https://aclanthology.org/2026.loreslm-1.20/
    *Status: strong, peer-reviewed, and it is about multiple-choice reasoning rather than translation — say so when citing it. This is the citable basis for the model-choice confound and for keeping the naturalness check advisory-only.*
12. **Sarvam-1** (2024-10-24): a 2.8B Indic model vs Llama 3.1 8B on Indic-average TriviaQA 90.62 vs 61.47; per-language Telugu figures (MMLU 44.58 vs 37.43; ARC 57.04 vs 44.78) are published inside an image.
    — https://www.sarvam.ai/blogs/sarvam-1
    *Status: TriviaQA comparison quotable with "vendor-reported"; the Telugu table inside the image is UNVERIFIED — do not transcribe it from memory.*
13. **IndicGenBench** (Singh et al., arXiv:2404.16816): LLaMA-7B vs 65B on Flores-In, 11.5/21.6 vs 18.1/32.7 — roughly a 57% relative gain going 7B→65B on Indic generation.
    — https://arxiv.org/html/2404.16816v2
    *Status: usable. Supports "scale matters for Indic generation" without claiming a Telugu-specific translation score.*
14. No published Llama-3.1-8B-vs-70B **Telugu translation** (COMET/BLEURT) head-to-head was found. TeluguST-46 (IJCNLP-AIST 2025 Findings) covers Telugu→English *speech* translation only, i.e. the wrong direction and modality.
    — https://aclanthology.org/2025.findings-ijcnlp.77/
    *Status: UNVERIFIED / absent. If the doc needs a Telugu MT number, it has to come from our own Phase 0 run, which is exactly why Phase 0 exists.*

## C. How this changes the argument

- The problem is evidenced by public structure (§A2: many language labels, few actually dubbed) plus our own measured error rate — not by a Kuku file.
- The QA-not-translation claim (§1, §5 of the PRD) is now load-bearing: with §B11 we should not pretend any small model is producing a shippable Telugu first pass, and we should not be judged on the first pass.
- Cost (§11) must be measured on `gpt-oss-20b` or `gpt-oss-120b`, and the batching design is constrained by the 8K TPM free-tier ceiling (§B9), which is a concrete, defensible engineering reason for token-capped batches.
