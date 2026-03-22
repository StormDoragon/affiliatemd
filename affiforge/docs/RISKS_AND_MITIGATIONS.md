# Risks and Mitigations (Honest)

## 1) Google AI content penalties

- Risk: Thin, generic, or unverified AI-first pages may be de-ranked by Helpful Content systems.
- Mitigation: Always require a human editorial pass before publish, attach cited sources, and enforce a content refresh schedule.
- Operating rule: No post can move to published status without editor approval metadata.

## 2) Amazon Associates Terms of Service violations

- Risk: Generating fake customer-review style content can violate Amazon policy and risk account penalties.
- Mitigation: Never generate "customer reviews" or fabricated testimonials; generate only editorial/comparison content.
- Operating rule: Prompt and template guards must block first-person buyer claims unless verified by internal testing notes.

## 3) Reddit API rate limits

- Risk: Excessive anonymous scraping can trigger throttling and unstable ingestion.
- Mitigation: Use user OAuth where possible and apply exponential backoff with retry jitter.
- Operating rule: Scanner jobs must honor per-client quotas and queue delayed retries when 429 responses are returned.

## 4) AI hallucination on pricing

- Risk: LLM-generated prices may be incorrect, outdated, or fabricated.
- Mitigation: Always pull live product pricing via Amazon PA-API at generation time.
- Operating rule: Pricing fields in generated content are invalid unless stamped with fresh PA-API retrieval timestamps.
