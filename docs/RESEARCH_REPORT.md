# Research report

**Verified on 2026-11-20.** Findings are source-specific; this is not market-size research or legal advice.

| Source | Verified finding | Limitation |
|---|---|---|
| [GrowthBook](https://github.com/growthbook/growthbook) | Open-core experimentation/feature-flag platform with warehouse-native metrics, SDKs, SRM checks and multiple statistics methods. | GitHub README; features/licensing can change. |
| [Google Ads Experiment Center](https://support.google.com/google-ads/answer/16856494) | Separates campaign experiments from brand/search/conversion lift studies and describes randomized user or geographic controls. | Google Ads-specific, not a portable email workflow. |
| [Meridian GeoX](https://developers.google.com/meridian/geox) / [repo](https://github.com/google/meridian-geox) | Open-source publisher-agnostic geographic incrementality tooling; repository says v1.0.1 (2026). | Geo unit/model is not this MVP's participant email A/B use case. |
| [Microsoft SRM](https://www.microsoft.com/en-us/research/articles/diagnosing-sample-ratio-mismatch-in-a-b-testing/) (2020-09-14) | SRM is an end-to-end data-quality symptom; Microsoft says tests should pass SRM before effects and uses `<0.0005`. | Practitioner article citing KDD 2019; not a regulatory rule. |
| [Dube & Xu (2026)](https://link.springer.com/article/10.1007/s11129-025-09303-9) | Open-access case study of three email RCTs comparing human, LLM, hybrid and control policies at Wine Access. | Single firm; findings cannot generalize to users. |
| [Journal of Marketing DOI](https://journals.sagepub.com/doi/10.1177/00222437261476639) | Returned HTTP 403 in this environment. | Not used for substantive claims. |
| [FTC CAN-SPAM guide](https://www.ftc.gov/business-guidance/resources/can-spam-act-compliance-guide-business) | Commercial email needs truthful routing/subjects, address and opt-out handling. | US guidance; no product compliance claim. |
| [European Commission GDPR framework](https://commission.europa.eu/law/law-topic/data-protection/data-protection-eu_en) | GDPR applies in EU/EEA since 2018. | High-level guidance, not tenant-specific legal advice. |

## Boundary

The product hypothesis is a constrained, reviewable workflow connecting creative
provenance, preregistered measurement, allocation checks and an auditable
conclusion. It is neither a claim of unique experimentation functionality nor a
validated demand claim; interviews and pilots are required.
