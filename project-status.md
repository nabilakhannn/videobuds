# VideoBuds — Project Status & Plan

> Last updated: 2026-02-28 (Phase 44 — Talking Avatar B-Roll Pipeline)

---

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Delete old DB for fresh start (optional)
rm -f videobuds.db

# Start the server
python3 run.py

# Open in browser
http://localhost:8080
```

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@videobuds.com | admin |
| Test User | user@videobuds.com | user |

> If the DB was created before the rebrand, admin email may still be `admin@scalebuds.com`. Delete `videobuds.db` and restart for a fresh seed.

---

## Current State Overview

VideoBuds is a Flask web application with:

- **Brand Management** — Create/manage brands with name, tagline, visual style, target audience, content pillars, brand guidelines (`brand_doc`), and photo libraries
- **AI Personas** — Define voice/tone/personality profiles with AI-generated prompt summaries
- **Campaign Engine** — 30-day social media campaign generation with calendar UI and export
- **Image Generation** — Multi-provider (Google Nano Banana, GPT Image) with model picker and pricing
- **Video Generation** — Multi-provider (Google Veo 3.1, Kling 3.0, Sora 2/Pro, Seedance, Minimax) with 4 providers (Google, WaveSpeed, Kie, Higgsfield) and faststart MP4 processing
- **Workflow Recipes** — 14 defined recipes, 8 fully wired:
  - Ad Video Maker (2-phase: script approval → video generation)
  - Photo to Ad (2-phase: vision analysis → image/video generation)
  - AI News Digest (single-phase: **grounded web search** → format, opt-in SEO/GEO/AEO)
  - Image Creator (AI-assisted prompt, style presets, platform selector, reference upload, brand photo library)
  - Video Creator (AI-assisted prompt, 6 video models incl. Seedance & Minimax, style/platform/duration, brand/persona, reference upload)
  - AI Content Machine (competitor analysis → hooks, psychology, patterns, strategy, content templates)
  - Talking Avatar (headshot + script → TTS → talking-head video via 3-tier fallback + optional B-roll pipeline via SEALCaM)
  - Influencer Content Kit (character photo + brief → multi-post planning → images + videos)
- **AI Content Editor** — Post-generation editing with brand/persona awareness, conversation history, accessible from any recipe output
- **Security** — Custom CSRF, rate limiting, security headers, ownership checks on all routes
- **Admin** — User management (activate/deactivate/delete), cost tracking dashboard

### Architecture

```
app/                     # Flask application package
├── __init__.py          # create_app() factory
├── config.py            # Flask config
├── extensions.py        # db, login_manager
├── security.py          # CSRF, rate limiting, security headers
├── models/              # 11 SQLAlchemy models
├── routes/              # 9 Flask blueprints (59 routes)
├── recipes/             # 13 workflow recipes (auto-discovered)
├── services/            # agent, model, prompt, script, editor, analytics
├── templates/           # 36+ Jinja2 templates
└── static/              # CSS, JS, uploads, generated images

tools/                   # AI generation tools (independent of Flask)
├── config.py            # API keys, costs, model registry
├── providers/           # google.py, kie.py, wavespeed.py, higgsfield.py, tts.py
├── create_image.py      # Image generation orchestrator
└── create_video.py      # Video generation orchestrator

references/              # Runtime data
├── inputs/              # User-uploaded input files
└── outputs/             # Generated assets (images, videos, debug JSON)
```

---

## All Completed Phases (1–26)

| Phase | Name | Summary |
|-------|------|---------|
| 1 | Core App Scaffold | Flask factory, SQLAlchemy, Flask-Login, base template |
| 2 | Brand Hub | Brand CRUD, questionnaire, AI brand doc generation |
| 3 | Campaign Engine | Campaign creation, 30-day calendar, post management |
| 4 | Image Generation Pipeline | Multi-provider image gen with Google, Kie, WaveSpeed |
| 5 | Post Management & Calendar UI | Post editor, calendar view, drag-and-drop |
| 6 | AI Agent Integration | Creative Director agent (analyze, plan, caption, prompt) |
| 7 | Multi-Provider Architecture | Provider abstraction layer, automatic routing |
| 8 | Admin vs User Dashboard | Separate admin dashboard with real costs |
| 9 | Dual Pricing System | Retail vs cost pricing, generation tracking |
| 10 | Higgsfield API Integration | Higgsfield provider for Nano Banana |
| 11 | Design Overhaul | "The Co-Founder" dark theme |
| 12 | VideoBuds Rebrand | Renamed from ScaleBuds, light/dark theme toggle |
| 13 | Security Enhancements | Security headers, rate limiting, input validation |
| 14 | Workflow Recipes System | Recipe/RecipeRun models, registry, library UI, run pages |
| 15 | AI Personas | UserPersona model, wizard, AI prompt summary generation |
| 16 | Script AI Agent | Research + write viral scripts in user's voice |
| 17 | Model Picker & Pricing | Model catalog, pricing page, dynamic price badges |
| 18 | Ad Video Maker Wired | First end-to-end recipe (image + video generation) |
| 19 | Compound Engineering | Multimodal Gemini, 2-phase execution, script approval |
| 20 | Polish & Hardening | Security audit, E2E check, SOLID refactor, bug fixes |
| 21 | News Digest Recipe | Gemini-powered news research + formatting |
| 22 | Bug Fixes & Features | CSRF, .gitignore, requirements.txt, account settings, pagination |
| 23 | Photo to Ad Wired | 2-phase vision analysis → image/video generation |
| 24 | Video Quality Fixes | Duration fix (8s), moov atom faststart, playsinline |
| 25 | Photo Library Upload Fix | CSRF bypass for AJAX, error feedback on uploads |
| 26 | Gap Analysis | Brand/persona integration gaps documented, action plan created |
| 27 | Brand/Persona Integration | Dropdowns, execute() wiring, AI prompt injection, brand voice UI, photo library |
| 28A | Security Hardening | Forced SECRET_KEY in production, input size limits (client + server) |
| 28B | Resilience Hardening | News Digest error handling, thread triple-fallback, stale run reaper |
| 28C | Persona Expansion | Persona support in agent_service (4 funcs) and script_to_scenes() |
| 28D | Code Quality | Extract simple_md filter, recipe timeout config, hide stub recipes |
| 29 | Gap Fixes & E2E Verification | History recipe_map, video error banner, inactive route guard, seed brand/persona, campaign persona wiring, DB is_enabled sync |
| 30 | OWASP Top 10 Security Hardening | Open redirect prevention, CSP, HSTS, session cookie hardening, password/email validation, security event logging — 44 unit tests |
| 31 | Ad Video Maker Bug Fixes & UX Hardening | HTMX HTTP 286 polling stop, video preload=auto, brand/persona selectors always visible, StaticPool test config — 19 unit tests |
| 32 | News Digest SEO/GEO/AEO Optimization | Opt-in SEO checkbox, enhanced blog format prompt (SEO+GEO+AEO), metadata JSON parsing, bonus SEO metadata card — 29 unit tests |

---

## Phase 32 — News Digest SEO / GEO / AEO Optimization (2026-02-27)

### Goal
Add an opt-in **SEO / GEO / AEO Optimization** checkbox to the News Digest recipe that, when enabled with the Blog Post format, produces a search-engine-optimized blog with keyword-rich structure, AI-overview-friendly facts, FAQ section, and a bonus SEO metadata card.

### Implementation (Option B — Opt-in Checkbox)

| Change | Description |
|--------|-------------|
| **InputField** | `seo_optimize` checkbox added as last field — `field_type="checkbox"`, `required=False` |
| **Format instructions** | `_build_seo_format_instructions()` replaces default blog instructions when SEO is active — covers keyword usage, heading hierarchy, GEO source attribution, AEO FAQ section |
| **Metadata parsing** | `_extract_seo_metadata()` splits Gemini response on `---SEO_METADATA_JSON---` separator; handles malformed JSON and markdown fences gracefully |
| **Metadata card** | `_format_seo_metadata()` renders title tag, meta description, primary/secondary keywords, FAQ schema, internal link suggestions |
| **Flag gating** | `seo_optimize = inputs.get("seo_optimize") == "1" and output_format == "blog"` — checkbox has no effect on email/LinkedIn |
| **Progress labels** | Step 0 and Step 3 labels dynamically reflect SEO mode |
| **Step count** | Remains at 4 — no progress bar impact |

### Files Changed
- `app/recipes/news_digest.py` — single-file change (InputField + 3 helper methods + execute flow)
- `tests/test_news_digest_seo.py` — 29 unit tests (7 test classes)

### Test Coverage (29 tests)
- **TestSEOInputField** (3) — checkbox presence, position, help text
- **TestSEOFormatInstructions** (6) — SEO/GEO/AEO sections, FAQ request, metadata fields
- **TestSEOMetadataExtraction** (6) — happy path, no separator, empty, malformed JSON, markdown fences, content preservation
- **TestSEOMetadataFormatting** (3) — full, minimal, empty metadata
- **TestSEOFlagGating** (4) — blog/email/linkedin/unchecked combinations
- **TestSEOIntegration** (5) — mocked Gemini end-to-end: SEO blog, non-SEO blog, email+SEO, progress labels
- **TestStepCount** (2) — step count unchanged, how-to-use updated

---

## Phase 31 — Ad Video Maker Bug Fixes & UX Hardening (2026-02-27)

### User-Reported Bugs
1. **Page keeps refreshing after video is created** — HTMX polling never stopped, continuously replacing the DOM (resetting video playback).
2. **Generated video doesn't play fully** — Caused by (1) DOM replacement + `preload="metadata"` preventing full download.
3. **No option to add branding or persona** — Brand/persona selectors were hidden behind a collapsible toggle that users couldn't find.

### Fixes Applied

| # | Bug | Root Cause | Fix | File |
|---|-----|-----------|-----|------|
| G1 | Infinite polling | `run_status` always returned HTTP 200 | Return HTTP 286 for terminal statuses (`completed`, `failed`, `cancelled`, `awaiting_approval`) — HTMX standard for "stop polling" | `app/routes/recipes.py` |
| G2 | Video won't play fully | `preload="metadata"` + DOM replacement by G1 | Changed to `preload="auto"` + G1 fix stops DOM replacement | `app/templates/recipes/_run_progress.html` |
| G3 | Brand/persona hidden | Collapsible `<div hidden>` with toggle button | Made selectors always visible, removed toggle. Fixed `url_for` for persona creation link. | `app/templates/recipes/run.html` |

### Unit Tests Added — 19 Tests, ALL PASS

| Test Class | Tests | Description |
|------------|:-----:|-------------|
| `TestHtmxPollingStop` | 7 | HTTP 286 for all terminal statuses, 200 for active, non-HTMX always 200 |
| `TestVideoPlayback` | 3 | `preload="auto"` present, `controls` and `playsinline` attributes |
| `TestBrandPersonaVisibility` | 7 | Selectors always visible, "Create" links when empty, form values posted |
| `TestHtmxAccessControl` | 2 | Auth required for HTMX poll, cross-user access blocked (404) |

### Test Infrastructure Improvements
- `app/config.py` `TestingConfig` — Added `SQLALCHEMY_ENGINE_OPTIONS` with `StaticPool` for reliable in-memory SQLite in tests
- Test fixtures use `create_app("testing")` for proper DB isolation
- `autouse` fixture clears Flask-Login `g._login_user` between tests to prevent context leakage

### Test Suite Summary (Post-Phase 32)

| File | Tests | Status |
|------|:-----:|:------:|
| `tests/test_filters.py` | 23 | ✅ |
| `tests/test_recipe_timeout.py` | 7 | ✅ |
| `tests/test_recipe_active.py` | 12 | ✅ |
| `tests/test_gap_fixes.py` | 13 | ✅ |
| `tests/test_owasp.py` | 44 | ✅ |
| `tests/test_phase31_fixes.py` | 19 | ✅ |
| `tests/test_news_digest_seo.py` | 29 | ✅ |
| **Total** | **147** | **✅ ALL PASS** |

### E2E Verification — 18 Checks, ALL PASS

| Check | Status |
|-------|:------:|
| HTTP 286 for `completed` | ✅ |
| HTTP 286 for `failed` | ✅ |
| HTTP 286 for `cancelled` | ✅ |
| HTTP 286 for `awaiting_approval` | ✅ |
| HTTP 200 for `running` | ✅ |
| HTTP 200 for `pending` | ✅ |
| Video `preload="auto"` present | ✅ |
| `preload="metadata"` absent | ✅ |
| `brand_id` selector visible | ✅ |
| `persona_id` selector visible | ✅ |
| "Brand & Persona" heading visible | ✅ |
| Unauthenticated poll → 302 | ✅ |
| Cross-user poll → 404 | ✅ |
| CSP header present | ✅ |
| X-Content-Type-Options present | ✅ |
| X-Frame-Options present | ✅ |
| StaticPool active in testing | ✅ |

---

## Gap Analysis: Brand/Persona Integration

### User Feedback

> "Why brand and persona is separate places, shouldn't it be in one place under brand voice... also, how these persona and brand is going to impact the recipes, as those are in separate, and no option to select the knowledge, persona, or brand while creating the scripts, images, videos."

### Identified Gaps

1. **No selector in recipe run form** — `app/templates/recipes/run.html` has no dropdowns for selecting a Brand or Persona before running a recipe.

2. **Recipes never receive Brand/Persona objects** — `RecipeRun` has `brand_id` and `persona_id` foreign keys, but `BaseRecipe.execute()` only receives `inputs`, `run_id`, and `user_id`. The Brand and Persona objects are never passed to the recipe.

3. **Working recipes ignore brand context** — Ad Video Maker and Photo to Ad use multimodal AI for product analysis, but don't inject brand voice, target audience, or persona tone into their prompts. This leads to generic ad copy.

4. **Disconnected UI** — Brands and Personas exist in separate sidebar sections. There's no visual link showing how they relate to each other or to Recipes.

5. **No "knowledge" selection** — Users can't select which brand photos, brand document, or persona guidelines to use when running a recipe.

### Why Brand and Persona Should Stay Separate

- **Distinct entities** — A Brand is *what* the company is (identity, market position, visuals). A Persona is *how* the brand communicates (tone, voice, personality).
- **Many-to-many** — One brand can use multiple personas (corporate vs casual). One persona can serve multiple brands (freelancer's voice across clients).
- **Modularity** — Independent management and reuse. Define a persona once, apply to any brand.
- **AI prompting** — `UserPersona.ai_prompt_summary` guides style/tone. `Brand.brand_doc` provides broader context. Both are valuable but serve different roles.

The problem isn't the separation — it's the **lack of connection and utilization** in the recipe execution flow.

---

## Action Plan: Brand/Persona Integration — ✅ COMPLETE (Phase 27)

### Phase A — Wire the Plumbing ✅

**Task 1: Add Brand and Persona Dropdowns to Recipe Run Form** ✅
- Added `<select>` inputs for `brand_id` and `persona_id` to `run.html`
- Populated from `current_user.brands` and `current_user.personas`
- Both optional with "None" default
- `app/routes/recipes.py` GET handler passes brands and personas to template

**Task 2: Pass Brand and Persona Objects to `execute()`** ✅
- `_execute_recipe` in `app/routes/recipes.py` fetches Brand/Persona from DB, passes to `recipe.execute()`
- `_launch_recipe_execution` and `approve_script` forward brand_id/persona_id for Phase 2
- IDs stored on `RecipeRun.brand_id` and `RecipeRun.persona_id`

**Task 3: Update `BaseRecipe.execute()` Signature** ✅
- `app/recipes/base.py` now accepts `brand=None` and `persona=None` keyword arguments
- All concrete recipe implementations inherit the new signature

### Phase B — Use the Context ✅

**Task 4: Inject Brand/Persona Context into Working Recipes** ✅
- `build_brand_context()` and `build_persona_context()` static helpers on `BaseRecipe`
- `ad_video_maker.py` — brand/persona context injected into scene-writing prompt
- `photo_to_ad.py` — brand/persona context injected into concept-writing prompt

### Phase C — UX Polish & Advanced Knowledge ✅

**Task 5: Add "Brand Voice" Section to Brand Detail Page** ✅
- "Brand Voice" sidebar card on `brands/detail.html` — lists personas with name, tone, "Default" badge
- "New Persona" button for quick creation
- `app/routes/brands.py` `show_brand()` passes `active_brand` and `personas`

**Task 6: Auto-Inject Brand Photo Library as Reference Context** ✅
- `get_brand_reference_paths()` static helper on `BaseRecipe` — queries `ReferenceImage` by brand and purpose
- `ad_video_maker.py` production phase adds brand product photos as extra `reference_paths`
- `photo_to_ad.py` production phase adds brand product photos as extra `reference_paths`

### Phase D — Audit & Gap Fix ✅

**Audit: All recipes and services verified for brand/persona usage** ✅
- `news_digest.py` — `execute()` now accepts `brand=None, persona=None`; brand voice and persona tone injected into the formatting prompt
- `script_service.py` — already fully brand/persona-aware across `write_script()`, `rewrite_script()`, `research_and_write()`, `write_scripts_multi()`
- `agent_service.py` — brand-aware; persona support deferred (only used by campaign/brand management routes, not recipe execution)
- 10 placeholder recipes have no AI calls — brand/persona integration deferred until implementation

---

## Other Pending Work

### Recipes to Wire (6 remaining stubs)
All currently return "Coming Soon" messages:

| Recipe | Slug | Complexity |
|--------|------|------------|
| Social Scraper | `social-scraper` | Medium |
| Motion Capture | `motion-capture` | High |
| Multi-Scene Video | `multi-scene-video` | High |
| Style Cloner | `style-cloner` | High |
| Clip Factory | `clip-factory` | High |
| Vertical Reframe | `vertical-reframe` | Medium |

### Deployment
- Vercel project exists: "poistionedup" (connected to GitHub)
- Pending: custom domain, web analytics, speed insights

### Future Enhancements
- ~~`agent_service.py` persona support~~ ✅ Done (Phase 28C)
- ~~`script_to_scenes()` persona support~~ ✅ Done (Phase 28C)
- ~~Wire persona into campaign routes~~ ✅ Done (Phase 29 — `campaigns.py` now passes selected persona to `plan_campaign`)
- ~~Wire persona into remaining routes (api.py, generate.py)~~ ✅ Done (Phase 41 — persona now passed in generate_single, generate_for_day, agent_suggest_captions, agent_enhance_prompt)
- Ralph Loop learning: store user feedback on approved/rejected scripts for prompt improvement
- Content Repurposer pipeline (Clip Factory, Vertical Reframe)
- Social Publisher integration
- Multi-user collaboration on brands/campaigns

---

## Ralph Loop Full Audit (2026-02-27)

### Methodology
Compound Engineering with Ralph Loop: Research → Analyze → Learn → Plan → Hypothesize → Test

### Security Audit — ✅ PASS

| Area | Status | Detail |
|------|:------:|--------|
| Authentication | ✅ | Flask-Login with `@login_required` on all sensitive routes |
| CSRF | ✅ | Session-based tokens via `app/security.py`, timing-safe compare |
| Rate Limiting | ✅ | Token-bucket on `/login` and `/register` (5 req/min) |
| Security Headers | ✅ | CSP, HSTS, X-Frame-Options, X-Content-Type-Options, Referrer-Policy |
| XSS Prevention | ✅ | `html.escape()` in `simple_md` filter before markdown rendering |
| SQL Injection | ✅ | All queries via SQLAlchemy ORM (parameterized) |
| File Upload | ✅ | `validate_upload()` — extension whitelist + magic byte MIME verification + per-field size limits + `secure_filename()` |
| Path Traversal | ✅ | `send_from_directory()` validates root |
| Session Security | ✅ | `SECRET_KEY` enforced in production (RuntimeError); session cookies HttpOnly + SameSite=Lax + Secure (prod) |
| Open Redirect | ✅ | `is_safe_url()` + `safe_redirect()` on all redirect targets (login, brand switch, brand activate) |
| Password Validation | ✅ | ≥8 chars, uppercase, lowercase, digit, special char |
| Email Validation | ✅ | Format, length ≤254, domain validation |
| Security Logging | ✅ | Login success/failure, registration, admin actions logged via `security` logger |

### End-to-End Flow Check — ✅ PASS

All recipe execution flows verified: GET form → POST with brand/persona → background thread → `execute()` with brand/persona → AI prompt injection → asset generation → DB update.

### SOLID Principles Review — 🟢 B+

| Principle | Grade | Notes |
|-----------|:-----:|-------|
| Single Responsibility | B+ | Clean separation; minor: `simple_md` inline in `__init__.py` |
| Open/Closed | A | Recipe auto-discovery; new recipe = one file |
| Liskov Substitution | A | All recipes honor `BaseRecipe.execute()` contract |
| Interface Segregation | B | `BaseRecipe` helpers available to all, used by few — acceptable |
| Dependency Inversion | B- | Direct imports standard for Flask+SQLite scale |

### Gap Analysis — Action Plan

#### 🟠 HIGH Priority — ✅ COMPLETE (Phase 28A)

| # | Gap | Status | Detail |
|---|-----|:------:|--------|
| H1 | Static `SECRET_KEY` fallback | ✅ | `ProductionConfig` raises `RuntimeError` if default key used; `DevelopmentConfig` logs warning |
| H2 | No input size limits | ✅ | `maxlength` on form fields (500 text / 5000 textarea); server-side validation in POST handler; error re-renders preserve brand/persona dropdowns |

#### 🟡 MEDIUM Priority — ✅ ALL COMPLETE (Phase 28B + 28C)

| # | Gap | Status | Detail |
|---|-----|:------:|--------|
| M1 | `agent_service` has no persona support | ✅ | Added `persona=None` keyword param to `plan_campaign`, `write_captions`, `build_smart_prompt`, `select_photos`. Added `_persona_context()` helper. Persona voice injected into all Gemini prompts when provided. |
| M2 | `script_to_scenes()` has no persona support | ✅ | Added `persona_id=None` + `persona=None` params. Persona voice context injected into storyboard prompt so visual scenes match the persona's style. |
| M3 | No error handling on Gemini API failures in recipes | ✅ | News Digest: research call raises `RuntimeError` with user-friendly message; format call gracefully falls back to raw stories |
| M4 | Background thread crash → "Running…" forever | ✅ | Triple-fallback: inner try/except sets `status='failed'`; secondary try/except ensures DB write; outer catch-all prevents silent thread death. Stale run reaper marks runs stuck >60 min as failed. |

#### 🟢 LOW Priority

| # | Gap | Status | Detail |
|---|-----|:------:|--------|
| L1 | `simple_md` filter inline in `__init__.py` | ✅ | Extracted to `app/filters.py` with `register_filters(app)`. 23 unit tests. |
| L2 | No recipe execution timeout | ✅ | `RECIPE_TIMEOUT_MINUTES` config (default 30). Reaper reads from config. 7 unit tests. |
| L3 | 10 placeholder recipes clutter UI | ✅ | `is_active = False` on 9 stubs (Image Creator now active); `get_all_recipes()` / `recipe_count()` / `get_recipes_by_category()` filter by default. 12 unit tests. |

### Proposed Phases — ✅ ALL COMPLETE

| Phase | Items | Status |
|-------|-------|:------:|
| Phase 28A — Security Hardening | H1, H2 | ✅ |
| Phase 28B — Resilience | M3, M4 | ✅ |
| Phase 28C — Persona Expansion | M1, M2 | ✅ |
| Phase 28D — Code Quality | L1, L2, L3 | ✅ |
| Phase 29 — Gap Fixes & E2E | P0 + P1 fixes | ✅ |
| Phase 30 — OWASP Top 10 | A01, A05, A07, A09 | ✅ |
| Phase 31 — Ad Video Maker Fixes | G1, G2, G3 | ✅ |
| Phase 32 — SEO/GEO/AEO for News Digest | Opt-in SEO checkbox | ✅ |
| Phase 33 — Enhance Image Creator (6 features) | AI Prompt Assistant, Reference Upload, Style Presets, Platform Selector, Negative Prompt, Brand Photo Library | ✅ |
| Phase 34A — Video Creator Recipe | Wire stub → 4 video models, brand/persona, platform/style/duration inputs, AI-assisted prompt | ✅ |
| Phase 34B — OWASP A04 File Upload Hardening | Magic byte MIME validation, per-field size limits, secure_filename defence-in-depth | ✅ |
| Phase 34C — SQLAlchemy Deprecation Fix | Replace all 22 Query.get() → db.session.get() across 9 files | ✅ |
| Phase 34D — AI Content Machine Recipe | Competitor analysis → hooks, psychology, patterns, strategy, content templates | ✅ |
| Phase 35 — E2E Playwright Testing | 71 browser tests: auth, security headers, navigation, recipe forms, brand/persona, CSRF, API endpoints, stub blocking | ✅ |
| Phase 36 — Higgsfield Seedance & Minimax Video Models | Added 2 cost-effective video models via Higgsfield provider; 56 new unit tests; 527 total tests passing | ✅ |
| Phase 37 — Brand Guideline System Prompt Enhancement | Enriched brand/persona context, added creative directives system; 63 new tests; 519 total tests passing | ✅ |
| Phase 38 — Extended Video Duration Options | Added 15s/20s duration options, per-model max clamping, scaled timeouts; 14 new tests; 531 total tests passing | ✅ |
| Phase 39 — Output Rendering Bug Fixes & Gap Analysis | Fixed image preview not showing for Image Creator, fixed title/label key mismatch in output template, corrected stub count in docs; 531 tests passing | ✅ |
| Phase 40 — AI Content Editor + News Digest Grounding | AI editor for post-gen refinement with brand/persona context; Gemini Google Search grounding for real-time news; 42 new tests; 573 total tests passing | ✅ |
| Phase 41 — Talking Avatar + Influencer Content Kit + Persona Wiring | Activated Talking Avatar (TTS + 3-tier talking head fallback), built Influencer Content Kit, wired persona into generate.py + api.py; 59 new tests; 632 total tests passing | ✅ |
| Phase 42 — Gap Analysis & Hardening | Fixed 6 stub recipe signatures (crash on activation), added E2E tests for talking-avatar + influencer-content-kit; 12 new E2E tests; 715 total tests (632 unit + 83 E2E) | ✅ |

---

## Phase 41 — Talking Avatar + Influencer Content Kit + Persona Wiring (2026-02-28)

### Methodology
Compound Engineering + Ralph Loop: Research → Analyze → Learn → Plan → Hypothesize → Test

### Goal
1. **Activate Talking Avatar** — wire existing talking head pipeline (Gemini TTS + Higgsfield Speak v2/talking_photo + WaveSpeed InfiniteTalk) into a recipe.
2. **Build Influencer Content Kit** — multi-post planning + image/video generation from a character photo and brief.
3. **Wire persona into remaining routes** — `generate.py` and `api.py` agent endpoints now pass persona context to AI calls.

### Implementation

**11 files modified/created:**

| File | Change |
|------|--------|
| `tools/providers/tts.py` | **NEW** — Gemini 2.5 Flash Preview TTS: text → WAV audio, 8 voices, retry logic, PCM→WAV conversion |
| `app/recipes/talking_avatar.py` | **REWRITTEN** — Full pipeline: headshot analysis → script generation → TTS → media upload → 3-tier video fallback (Speak v2 → talking_photo → InfiniteTalk) |
| `app/recipes/influencer_content_kit.py` | **REWRITTEN** — Character analysis → multi-post planning → parallel image + video generation per post |
| `app/routes/generate.py` | Updated `_run_generation`, `generate_single`, `generate_for_day`, `_bulk_generate_worker` to pass persona context |
| `app/routes/api.py` | Updated `agent_suggest_captions`, `agent_enhance_prompt` to pass persona context |
| `tests/test_phase41.py` | **NEW** — 59 tests across 6 test classes |
| `tests/test_recipe_active.py` | Updated: stub count 8→6, active recipes now include talking-avatar + influencer-content-kit |

### Talking Avatar Pipeline

| Stage | Detail |
|-------|--------|
| **Headshot** | User uploads a photo; Gemini Vision analyses for face presence |
| **Script** | User provides script or AI generates one from brief + brand/persona |
| **TTS** | Gemini 2.5 Flash Preview generates WAV audio (8 voice presets) |
| **Media Upload** | Audio + image uploaded to WaveSpeed CDN |
| **Video (3-tier fallback)** | 1) Higgsfield Speak v2 → 2) Higgsfield talking_photo → 3) WaveSpeed InfiniteTalk |

### Test Coverage (59 new tests)

| Test Class | Tests | Description |
|------------|:-----:|-------------|
| `TestTTSProvider` | 11 | Empty/long text, missing API key, voice fallback, generation, retries, WAV format |
| `TestTalkingAvatarRecipe` | 22 | Activation, inputs, steps, missing fields, TTS failure, upload failure, 3-tier fallback, voice presets, script gen, cost tracking |
| `TestInfluencerContentKit` | 13 | Activation, inputs, steps, missing fields, validation, execution, failure handling, scene parsing |
| `TestPersonaWiring` | 7 | Persona passed in `_run_generation`, `generate_single`, `agent_suggest_captions`, `agent_enhance_prompt`, bulk worker exists |
| `TestProviderRegistry` | 3 | TTS/talking-head providers registered, cost entries exist |
| `TestRecipeRegistry` | 3 | Both recipes in registry, active count = 8 |

### Test Results
- **59 new tests** — all passing
- **632 total unit tests** — all passing, zero regressions
- **71 E2E tests** — unchanged

---

## Phase 40 — AI Content Editor + News Digest Grounding (2026-02-27)

### Methodology
Compound Engineering + Ralph Loop: Research → Analyze → Learn → Plan → Hypothesize → Test

### Goal
1. **Differentiate News Digest from ChatGPT** by using Gemini Google Search grounding so the recipe fetches *real-time* web data instead of relying on training data.
2. **Add an AI Content Editor** so users can refine any generated text output (scripts, blogs, newsletters, ad copy) conversationally — with full brand/persona context.

### Implementation

**8 files modified/created:**

| File | Change |
|------|--------|
| `app/services/editor_service.py` | **NEW** — `refine_content()` with input validation, prompt building, response parsing, brand/persona context injection, conversation history management |
| `app/services/agent_service.py` | Added `_call_gemini_grounded()` — Google Search grounding for real-time web search via Gemini |
| `app/routes/api.py` | Added `/api/recipes/chat` POST endpoint for AI editor — JSON input, CSRF-free (login-required), brand/persona lookup, error handling |
| `app/routes/recipes.py` | Updated `run_status` to pass `user_brands` and `user_personas` to template for editor context |
| `app/templates/recipes/_content_editor.html` | **NEW** — Editor modal UI with textarea, instruction input, chat history, submit button, spinner |
| `app/templates/recipes/_run_progress.html` | Added "Edit with AI" button on text outputs, included editor partial, added JavaScript for modal interaction |
| `app/recipes/news_digest.py` | Research step now calls `_call_gemini_grounded()` instead of `_call_gemini()` |
| `tests/test_editor_service.py` | **42 new tests** — 8 test classes covering all components |
| `tests/test_news_digest_seo.py` | Updated 5 integration tests to mock `_call_gemini_grounded` |

### AI Content Editor Features

| Feature | Detail |
|---------|--------|
| **Brand-aware editing** | Editor prompt includes full brand context (colours, voice, hashtags, logo, guidelines) |
| **Persona-aware editing** | Editor prompt includes persona context (tone, bio, voice style, keywords) |
| **Conversation history** | Client-side managed history (no PII stored); up to 20 turns per session |
| **Input validation** | Max 50K chars content, 2K chars instruction, history sanitisation |
| **Response parsing** | Splits refined content from explanation via `---EDITOR_EXPLANATION---` separator |
| **Graceful fallback** | If AI fails, returns user-friendly error without crashing |
| **Security** | Login required, input length limits, history sanitisation, no DB writes for chat |

### Test Coverage (42 new tests)

| Test Class | Tests | Description |
|------------|:-----:|-------------|
| `TestInputValidation` | 7 | Empty/whitespace/too-long content and instruction |
| `TestHistorySanitisation` | 9 | None, empty, valid, invalid role, non-dict, truncation, long text |
| `TestPromptBuilding` | 5 | Content/instruction/brand/persona/history in prompt |
| `TestResponseParsing` | 4 | Separator, no separator, code fences, multiple separators |
| `TestRefineContent` | 5 | Success, AI failure, brand/persona/history in prompt (mocked Gemini) |
| `TestGroundedGemini` | 3 | Grounding payload, fallback on error, no candidates |
| `TestNewsDigestGrounding` | 2 | Method exists, research step uses grounded call |
| `TestEditorChatRoute` | 7 | Missing content/instruction 400, success 200, ValueError 400, RuntimeError 502, Exception 500, no JSON 400 |

### Test Results
- **42 new tests** — all passing
- **573 total tests** — all passing, zero regressions

---

## Phase 37 — Brand Guideline System Prompt Enhancement (2026-02-27)

### Methodology
Compound Engineering + Ralph Loop: Research → Analyze → Learn → Plan → Hypothesize → Test

### Goal
Integrate production-grade brand guideline system prompts (from R38/Split AI/R44 JSON templates) into all visual-output recipes so that every generated image and video is truly on-brand, on-persona, diverse, and viral-quality.

### Implementation

**5 files modified, 1 new test file:**

| File | Change |
|------|--------|
| `app/recipes/base.py` | Enriched `build_brand_context` (colours, voice, hashtags, caption template, logo, enforcement). Enriched `build_persona_context` (bio). New `build_creative_directives()` for universal quality rules |
| `app/recipes/image_creator.py` | `_build_assisted_prompt` injects creative directives with UGC detection |
| `app/recipes/video_creator.py` | `_build_assisted_prompt` injects creative directives with UGC detection |
| `app/recipes/photo_to_ad.py` | `_execute_script` injects creative directives into concept prompt |
| `tests/test_brand_context.py` | **63 new tests** — brand context, persona context, creative directives, recipe integration |

### Test Results
- **63 new tests** — all passing
- **519 total tests** — all passing, zero regressions

---

## Phase 36 — Higgsfield Seedance & Minimax Video Models (2026-02-27)

### Methodology
Compound Engineering + Ralph Loop: Research → Analyze → Learn → Plan → Hypothesize → Test

### Goal
Add Seedance (ByteDance) and Minimax as cost-effective video generation models (~$0.05/video) via the Higgsfield provider, expanding the Video Creator recipe from 4 to 6 models.

### Implementation

**Files modified (7):**

| File | Change |
|------|--------|
| `tools/providers/higgsfield.py` | Added `_VIDEO_MODELS` dict, `submit_video()`, `poll_video()` for async video generation |
| `tools/create_video.py` | Added "seedance" and "minimax" to `_resolve_model()` mapping and `max_wait` timeout logic |
| `tools/providers/__init__.py` | Registered both models in `VIDEO_PROVIDERS` with `higgsfield` as default provider |
| `tools/config.py` | Added cost entries `("seedance","higgsfield")` and `("minimax","higgsfield")`, added `HIGGSFIELD_VIDEO_MODELS` config dict |
| `app/services/model_service.py` | Added both models to `MODEL_CATALOG` with provider details, pricing, and free-tier flags |
| `app/recipes/video_creator.py` | Added both to `_MODEL_MAP`, updated description, `how_to_use` table, and model selector help text |
| `tests/test_higgsfield_video.py` | **56 new tests** covering provider registry, submit/poll, costs, catalog, recipe integration, security edge cases |

**Video model lineup (6 models, 4 providers):**

| Model | Provider | Cost | Quality |
|-------|----------|------|---------|
| Veo 3.1 | Google AI Studio | $0.50 | Cinematic |
| Kling 3.0 | WaveSpeed / Kie | $0.30 | Great |
| Sora 2 | WaveSpeed | $0.30 | Good |
| Sora 2 Pro | WaveSpeed / Kie | $0.30 | Excellent |
| Seedance | Higgsfield | $0.05 | Good |
| Minimax | Higgsfield | $0.05 | Excellent |

### Test Results
- **56 new tests** in `tests/test_higgsfield_video.py` — all passing
- **527 total tests** — all passing, zero regressions

---

## Phase 35 — E2E Playwright Testing (2026-02-27)

### Methodology
Compound Engineering + Ralph Loop: Research → Analyze → Learn → Plan → Hypothesize → Test

### Goal
Full end-to-end browser testing of all active recipes, navigation, security controls, brand/persona management, and stub recipe blocking using Playwright with Chromium.

### Implementation
- **Session-scoped fixtures**: Single browser launch, one login per role (admin + user), all tests reuse the session cookies — avoids rate-limiting (15 req/min on `/login`)
- **Anonymous context**: Separate unauthenticated context for access-control tests
- **12 test classes, 71 tests** across all application features

### Test Coverage (71 tests)

| Test Class | Tests | Description |
|------------|:-----:|-------------|
| `TestAuth` | 4 | Login page loads, admin session active, unauthenticated redirect, recipe auth guard |
| `TestSecurityHeaders` | 4 | CSP, X-Content-Type-Options, X-Frame-Options, Referrer-Policy |
| `TestNavigation` | 5 | Dashboard, recipes library, brands, campaigns, pricing pages load correctly |
| `TestRecipeLibrary` | 4 | 6 active recipes visible, stubs hidden, stub detail/run return 404 |
| `TestAdVideoMakerRecipe` | 5 | Detail, run form, file upload, brand selector, persona selector |
| `TestPhotoToAdRecipe` | 4 | Detail, run form, file upload, brand/persona selectors |
| `TestNewsDigestRecipe` | 5 | Detail, run form, topic field, SEO checkbox, format selector |
| `TestImageCreatorRecipe` | 8 | Detail, form, prompt, style, platform, model, reference upload, brand/persona |
| `TestVideoCreatorRecipe` | 7 | Detail, form, prompt, model, duration, style, brand/persona |
| `TestContentMachineRecipe` | 6 | Detail, form, competitor content, analysis mode, platform, brand/persona |
| `TestBrandManagement` | 2 | Brand list, create form |
| `TestPersonaManagement` | 2 | Persona list, create form |
| `TestCSRF` | 3 | CSRF token on login, recipe run, brand create forms |
| `TestRecipeHistory` | 1 | History page loads |
| `TestAdminFeatures` | 1 | Admin dashboard shows content |
| `TestUserIsolation` | 2 | Non-admin user can access home and recipes |
| `TestAPIEndpoints` | 2 | 404 for missing file, auth required for API |
| `TestRecipeDocumentation` | 6 | All 6 active recipes show how-to-use instructions |

### Files Changed

| File | Change |
|------|--------|
| `tests/test_e2e_playwright.py` | **71 E2E tests** — 12 test classes, session-scoped Playwright fixtures |

### Test Suite Summary (Post-Phase 35)

| File | Tests | Status |
|------|:-----:|:------:|
| `tests/test_filters.py` | 23 | ✅ |
| `tests/test_recipe_timeout.py` | 7 | ✅ |
| `tests/test_recipe_active.py` | 12 | ✅ |
| `tests/test_gap_fixes.py` | 13 | ✅ |
| `tests/test_owasp.py` | 44 | ✅ |
| `tests/test_phase31_fixes.py` | 19 | ✅ |
| `tests/test_news_digest_seo.py` | 29 | ✅ |
| `tests/test_image_creator.py` | 78 | ✅ |
| `tests/test_video_creator.py` | 73 | ✅ |
| `tests/test_content_machine.py` | 66 | ✅ |
| `tests/test_upload_security.py` | 36 | ✅ |
| `tests/test_e2e_playwright.py` | 71 | ✅ |
| **Total** | **471** | **✅ ALL PASS** |

---

## Phase 34 — Video Creator + OWASP A04 + SQLAlchemy Fix + AI Content Machine (2026-02-27)

### Methodology
Compound Engineering + Ralph Loop: Research → Analyze → Learn → Plan → Hypothesize → Test

### Phase 34A — Video Creator Recipe

| # | Change | Detail |
|---|--------|--------|
| VC1 | **Activate recipe** | `is_active = True` — stub → fully wired |
| VC2 | **11 input fields** | creation_mode, prompt, reference_image, style_preset (8 presets), platform (9 platforms), negative_prompt, model (4 video models), aspect_ratio (3), duration (4s/6s/8s), video_count (1/2/4) |
| VC3 | **4 video models** | Google Veo 3.1, Kie AI Kling 3.0, Kie AI Sora 2 Pro, WaveSpeed Kling 3.0 |
| VC4 | **AI-assisted prompting** | Gemini crafts video prompt from plain-English description, brand context, style, platform hints |
| VC5 | **Reference image analysis** | Gemini Vision analyses uploaded reference → analysis injected into prompt |
| VC6 | **Brand Photo Library** | Auto-pulls brand reference images via `get_brand_reference_paths()` |
| VC7 | **Multi-video generation** | 1, 2, or 4 videos per run with per-video progress and error isolation |
| VC8 | **Input validation (OWASP)** | Whitelist validation for model, ratio, duration, count, style, platform, mode |

### Phase 34B — OWASP A04 File Upload Hardening

| # | Change | Detail |
|---|--------|--------|
| FU1 | **`validate_upload()` utility** | Centralized in `app/security.py` — extension whitelist + magic bytes + size + secure_filename |
| FU2 | **Magic byte verification** | `_check_magic_bytes()` reads first 12 bytes of stream, compares against known signatures for PNG, JPEG, GIF, WEBP, PDF, WEBM, MP3, WAV |
| FU3 | **Per-field size limits** | `MAX_UPLOAD_SIZE_BYTES` dict: image=10MB, video=100MB, audio=25MB, document=20MB, recipe_input=10MB |
| FU4 | **Applied to all upload endpoints** | `app/routes/recipes.py`, `app/routes/api.py` (campaign references + brand photos) |

### Phase 34C — SQLAlchemy Deprecation Fix

| # | Change | Detail |
|---|--------|--------|
| SQ1 | **22 replacements across 9 files** | `Query.get()` → `db.session.get()`, `Query.get_or_404()` → `db.session.get_or_404()` |
| SQ2 | **Files updated** | api.py, dashboard.py, campaigns.py, generate.py, posts.py, export.py, recipes.py, prompt_service.py, script_service.py |
| SQ3 | **Zero deprecation warnings** | Full test suite runs clean |

### Phase 34D — AI Content Machine Recipe

| # | Change | Detail |
|---|--------|--------|
| CM1 | **New recipe** | `app/recipes/content_machine.py` — `is_active = True` |
| CM2 | **4 input fields** | competitor_content (textarea: paste competitor posts/URLs), platforms (multiselect: Instagram/YouTube/TikTok/LinkedIn/X), analysis_depth (select: quick/standard/deep), output_format (select: full_report/hooks_only/templates_only/psychology_only) |
| CM3 | **4-stage Gemini analysis** | Hook analysis → Psychology mapping → Pattern extraction → Strategy generation |
| CM4 | **Flexible output** | Full report or filtered sections (hooks, psychology, templates) |
| CM5 | **Brand/persona context** | Enriches all AI prompts with brand voice and persona tone |

### Files Changed

| File | Change |
|------|--------|
| `app/recipes/video_creator.py` | Complete rewrite — 11 input fields, 4 video models, AI Prompt Assistant, Reference Vision, Style Presets, Platform Selector, Negative Prompt, Brand Photo Library |
| `app/recipes/content_machine.py` | **NEW** — 4 input fields, 4-stage Gemini analysis pipeline, flexible output formats |
| `app/security.py` | Added `validate_upload()`, `_check_magic_bytes()`, `MAX_UPLOAD_SIZE_BYTES`, expanded `ALLOWED_UPLOAD_EXT` |
| `app/routes/recipes.py` | Uses `validate_upload()` for recipe file uploads; `db.session.get()` migration |
| `app/routes/api.py` | Uses `validate_upload()` for campaign/brand uploads; `db.session.get()` migration |
| `app/routes/dashboard.py` | `db.session.get()` migration |
| `app/routes/campaigns.py` | `db.session.get()` migration |
| `app/routes/generate.py` | `db.session.get()` migration |
| `app/routes/posts.py` | `db.session.get()` migration |
| `app/routes/export.py` | `db.session.get()` migration |
| `app/services/prompt_service.py` | `db.session.get()` migration |
| `app/services/script_service.py` | `db.session.get()` migration |
| `tests/test_video_creator.py` | **73 new tests** — 12 test classes |
| `tests/test_content_machine.py` | **66 new tests** — 8 test classes |
| `tests/test_upload_security.py` | **36 new tests** — 4 test classes |
| `tests/test_recipe_active.py` | Updated stub count 9 → 7, active set 4 → 6 |
| `tests/test_gap_fixes.py` | Updated stub recipe from `video-creator` to `clip-factory` |

### Test Suite Summary (Post-Phase 34)

| File | Tests | Status |
|------|:-----:|:------:|
| `tests/test_filters.py` | 23 | ✅ |
| `tests/test_recipe_timeout.py` | 7 | ✅ |
| `tests/test_recipe_active.py` | 12 | ✅ |
| `tests/test_gap_fixes.py` | 13 | ✅ |
| `tests/test_owasp.py` | 44 | ✅ |
| `tests/test_phase31_fixes.py` | 19 | ✅ |
| `tests/test_news_digest_seo.py` | 29 | ✅ |
| `tests/test_image_creator.py` | 78 | ✅ |
| `tests/test_video_creator.py` | 73 | ✅ |
| `tests/test_content_machine.py` | 66 | ✅ |
| `tests/test_upload_security.py` | 36 | ✅ |
| **Total** | **400** | **✅ ALL PASS** |

---

## Phase 33 — Activate Image Creator Recipe (2026-02-27)

### Methodology
Compound Engineering + Ralph Loop: Research existing tools layer → Wire to recipe → Validate with tests.

### Changes Applied

| # | Change | Detail |
|---|--------|--------|
| IC1 | **A: AI Prompt Assistant** | Assisted mode — user describes in plain English → Gemini crafts a detailed image prompt. Fallback to manual enrichment if API fails. |
| IC2 | **B: Reference Image Upload** | File upload field → Gemini Vision analyses style, colours, composition → analysis fed into prompt + passed to `generate_ugc_image(reference_paths=...)`. |
| IC3 | **C: Style Presets** | 8 presets (None, Product Shot, Social Graphic, Lifestyle, Flat Lay, Abstract, Portrait, Infographic) with prompt fragments injected into AI meta-prompt. |
| IC4 | **D: Platform Selector** | 9 platforms (Instagram Feed/Story, LinkedIn, YouTube Thumb, TikTok, Facebook, X, Website Hero) with auto-recommended aspect ratios and composition hints. |
| IC5 | **E: Negative Prompt** | Optional textarea — "things to exclude" injected into both Assisted and Manual prompt paths. |
| IC6 | **F: Brand Photo Library** | Auto-pulls up to 3 brand reference images via `get_brand_reference_paths()` and passes them to the image generator alongside any user-uploaded reference. |
| IC7 | Brand/Persona injection | `build_brand_context()` / `build_persona_context()` enrich the AI prompt with brand colours, style, audience, persona voice. |
| IC8 | Multi-image generation | 1, 2, or 4 images per run with per-image progress callbacks and error isolation. |
| IC9 | Input validation (OWASP) | Whitelist validation for model, ratio, count, style preset, platform, creation mode. Empty prompt rejection. Invalid model/ratio graceful fallback. |
| IC10 | Summary card | Shows mode, model, ratio, style, platform, brand, persona, reference status, negative prompt, image count, cost. |
| IC11 | Updated `test_recipe_active.py` | Adjusted stub count from 10 → 9 and active set from 3 → 4. |

### Unit Tests Added

| Test File | Tests | Description |
|-----------|:-----:|-------------|
| `tests/test_image_creator.py` | 78 | 13 test classes: InputFields, StylePresets, PlatformSelector, AssistedMode, ManualMode, ReferenceImage, BrandPhotoLibrary, ExecuteHappyPath, ExecuteErrors, SummaryCard, Validation, ProgressCallbacks, Metadata |

### Test Suite Summary (Post-Phase 33)

| File | Tests | Status |
|------|:-----:|:------:|
| `tests/test_filters.py` | 23 | ✅ |
| `tests/test_recipe_timeout.py` | 7 | ✅ |
| `tests/test_recipe_active.py` | 12 | ✅ |
| `tests/test_gap_fixes.py` | 13 | ✅ |
| `tests/test_owasp.py` | 44 | ✅ |
| `tests/test_phase31_fixes.py` | 19 | ✅ |
| `tests/test_news_digest_seo.py` | 29 | ✅ |
| `tests/test_image_creator.py` | 78 | ✅ |
| **Total** | **225** | **✅ ALL PASS** |

---

## Phase 29 — Gap Fixes & E2E Verification (2026-02-27)

### Methodology
User-reported bugs and compound engineering gap analysis → 6 targeted fixes with unit tests and E2E verification.

### Fixes Applied

| # | Priority | Fix | Detail |
|---|:--------:|-----|--------|
| F1 | P0 | History page recipe_map misses inactive recipes | `history()` now calls `get_all_recipes(include_inactive=True)` so stale run names display correctly |
| F2 | P0 | Video error not shown in output UI | Added yellow warning banner in `_run_progress.html` when media output's `value` field contains "error" |
| F3 | P0 | Inactive recipes accessible via detail URL | `detail()` and `run()` routes now `abort(404)` if `recipe.is_active is False` |
| F4 | P1 | No sample brand/persona for new users | `create_app()` now seeds "Sample Brand" + "Default Persona" for admin and test users |
| F5 | P1 | Persona not wired through campaign routes | `campaigns.py` fetches user personas → template has persona dropdown → `create_campaign()` passes persona to `plan_campaign()` |
| F6 | P1 | DB `is_enabled` not synced from class `is_active` | `_ensure_recipe_db_row()` now updates `is_enabled` whenever the DB flag diverges from the class attribute |

### Unit Tests Added

| Test File | Tests | Description |
|-----------|:-----:|-------------|
| `tests/test_gap_fixes.py` | 13 | History map, error banner, inactive guard, seed data, persona wiring, DB sync |

### Test Suite Summary (Post-Phase 29)

| File | Tests | Status |
|------|:-----:|:------:|
| `tests/test_filters.py` | 23 | ✅ |
| `tests/test_recipe_timeout.py` | 7 | ✅ |
| `tests/test_recipe_active.py` | 12 | ✅ |
| `tests/test_gap_fixes.py` | 13 | ✅ |
| **Total** | **55** | **✅ ALL PASS** |

### E2E Verification Checklist — ✅ ALL PASS

| Check | Status |
|-------|:------:|
| Active recipe count = 3 | ✅ |
| Inactive stubs blocked from detail/run URLs | ✅ |
| Admin has ≥1 brand + ≥1 persona (seeded) | ✅ |
| Test user has ≥1 brand + ≥1 persona (seeded) | ✅ |
| DB `is_enabled` synced with class `is_active` | ✅ |
| CSRF protection enabled | ✅ |
| Security headers registered | ✅ |
| All 6 recipe templates present | ✅ |
| Error banner in `_run_progress.html` | ✅ |
| Persona dropdown in campaign form | ✅ |

---

## Phase 30 — OWASP Top 10 Security Hardening (2026-02-27)

### Methodology
OWASP Top 10 audit using Ralph Loop: Research → Analyze → Learn → Plan → Hypothesize → Test

### OWASP Fixes Applied

| # | OWASP ID | Category | Fix | Detail |
|---|----------|----------|-----|--------|
| O1 | A01 | Broken Access Control — Open Redirect | ✅ | `is_safe_url(target)` validates redirect URLs; `safe_redirect(target)` returns safe fallback. Applied to login `next_page`, `activate_brand()` referrer, and `switch_brand()` referrer. |
| O2 | A05 | Security Misconfiguration — Missing Headers | ✅ | Added `Content-Security-Policy` (CSP) header with script/style/img/font sources. Added `Strict-Transport-Security` (HSTS) with 1-year max-age + includeSubDomains. |
| O3 | A05 | Security Misconfiguration — Session Cookies | ✅ | `SESSION_COOKIE_HTTPONLY = True`, `SESSION_COOKIE_SAMESITE = "Lax"`, `SESSION_COOKIE_SECURE = True` (production only). Direct assignment instead of `setdefault` to override Flask's `None` defaults. |
| O4 | A07 | Auth Failures — No Password Validation | ✅ | `validate_password(password)` enforces ≥8 chars, ≥1 uppercase, ≥1 lowercase, ≥1 digit, ≥1 special. Applied to registration and account password change. |
| O5 | A07 | Auth Failures — No Email Validation | ✅ | `validate_email(email)` validates format, length (≤254), and domain presence. Applied to registration. |
| O6 | A09 | Security Logging — No Event Logging | ✅ | Added `logging.getLogger("security")` events for: successful login, failed login (wrong password), failed login (unknown user), new user registration, user toggle (admin), user delete (admin), logout. |

### Unit Tests Added

| Test Class | Tests | OWASP ID | Description |
|------------|:-----:|----------|-------------|
| `TestIsSafeUrl` | 6 | A01 | Validates relative URLs, blocks external domains, handles None/empty |
| `TestSafeRedirect` | 3 | A01 | Safe URL passthrough, evil URL fallback, None handling |
| `TestValidatePassword` | 7 | A07 | Min length, uppercase, lowercase, digit, special char, valid password, empty |
| `TestValidateEmail` | 6 | A07 | Valid format, missing @, missing domain, too long, empty, whitespace |
| `TestCSPHeader` | 3 | A05 | CSP header present, contains script-src, contains style-src |
| `TestHSTSHeader` | 2 | A05 | HSTS header present, contains max-age |
| `TestSessionCookieConfig` | 3 | A05 | HttpOnly=True, SameSite=Lax, Secure flag behavior |
| `TestSecurityEventLogging` | 6 | A09 | Login success/failure logging, registration logging, admin action logging |
| `TestLoginOpenRedirect` | 4 | A01 | Login blocks external redirect, allows safe redirect |
| `TestRegisterValidation` | 5 | A07 | Registration rejects weak passwords and invalid emails |
| `TestBrandActivateRedirect` | 3 | A01 | Brand activate blocks open redirect via referrer |
| `TestBrandSwitchRedirect` | 2 | A01 | API brand switch blocks open redirect via referrer |

### Test Suite Summary (Post-Phase 30)

| File | Tests | Status |
|------|:-----:|:------:|
| `tests/test_filters.py` | 23 | ✅ |
| `tests/test_recipe_timeout.py` | 7 | ✅ |
| `tests/test_recipe_active.py` | 12 | ✅ |
| `tests/test_gap_fixes.py` | 13 | ✅ |
| `tests/test_owasp.py` | 44 | ✅ |
| **Total** | **99** | **✅ ALL PASS** |

---

## Known Issues

- Seeded admin email may be `admin@scalebuds.com` if DB was created before rebrand — delete `videobuds.db` and restart
- macOS quarantine attributes on `videobuds.db` can cause readonly errors — delete and let app recreate
- `KIE_API_KEY` not set: videos saved locally via `/api/outputs/` (no external hosting)
- `ffmpeg` required for moov atom faststart — gracefully skipped if not installed
- 6 stub recipes have `is_active = False` — Ad Video Maker, Photo to Ad, News Digest, Image Creator, Video Creator, AI Content Machine, Talking Avatar, and Influencer Content Kit are active (pass `include_inactive=True` to see stubs)
