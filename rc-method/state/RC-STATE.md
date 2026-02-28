# RC Method State: Customer Lookalike Agent

## Phase

Current: 2 - Define

## Gates

| Phase          | Status   | Date       | Feedback                                                                 |
| -------------- | -------- | ---------- | ------------------------------------------------------------------------ |
| 1 - Illuminate | approved | 2026-02-20 | Competitive research complete. 10 tools analyzed. Market gaps identified. |
| 2 - Define     | pending  |            | PRD-v2.md ready for review. 17 gaps from v1 fixed.                       |
| 3 - Architect  | pending  |            |                                                                          |
| 4 - Sequence   | pending  |            |                                                                          |
| 5 - Validate   | pending  |            |                                                                          |
| 6 - Forge      | pending  |            |                                                                          |
| 7 - Connect    | pending  |            |                                                                          |
| 8 - Compound   | pending  |            |                                                                          |

## Artifacts

- rc-method/prds/PRD-v2.md (symlink to /PRD-v2.md)
- skills/icp.md
- skills/messaging.md
- skills/email-sequences.md
- skills/tofu-use-cases.md
- skills/content-links.md
- Competitive Analysis (from research agent)
- PRD.md v1.0 (archived, superseded by v2)

## Decisions

| # | Decision | Why | Date |
|---|----------|-----|------|
| 1 | Flat pricing, no credits | #1 user complaint across all competitors | 2026-02-20 |
| 2 | Supabase over raw PostgreSQL | RLS built-in, auth built-in, real-time subscriptions | 2026-02-20 |
| 3 | Trigger.dev over BullMQ | Serverless, checkpoint/resume built-in, retry built-in | 2026-02-20 |
| 4 | Gmail drafts only (no direct send) for MVP | Avoids deliverability infra. User stays in control. | 2026-02-20 |
| 5 | Customer-anchored outreach as core differentiator | No competitor does this. Hard to copy without deal data. | 2026-02-20 |
| 6 | Free trial (5 customers, no Gmail) | Drive signups without requiring payment | 2026-02-20 |

## UX

Score: not scored (will score in Phase 5 - Validate)
Mode: not set
