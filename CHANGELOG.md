# VideoBuds — Complete Build Log

Everything that has been built, configured, and shipped in this project from start to finish.

> Last updated: 2026-02-28 (Phase 44 — Talking Avatar B-Roll Pipeline)

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Technology Stack](#technology-stack)
3. [Phase 1 — Core App Scaffold](#phase-1--core-app-scaffold)
4. [Phase 2 — Brand Hub](#phase-2--brand-hub)
5. [Phase 3 — Campaign Engine](#phase-3--campaign-engine)
6. [Phase 4 — Image Generation Pipeline](#phase-4--image-generation-pipeline)
7. [Phase 5 — Post Management & Calendar UI](#phase-5--post-management--calendar-ui)
8. [Phase 6 — AI Agent Integration](#phase-6--ai-agent-integration)
9. [Phase 7 — Multi-Provider Architecture](#phase-7--multi-provider-architecture)
10. [Phase 8 — Admin vs User Dashboard Separation](#phase-8--admin-vs-user-dashboard-separation)
11. [Phase 9 — Dual Pricing System](#phase-9--dual-pricing-system)
12. [Phase 10 — Higgsfield API Integration](#phase-10--higgsfield-api-integration)
13. [Phase 11 — Design Overhaul ("The Co-Founder" Theme)](#phase-11--design-overhaul-the-co-founder-theme)
14. [Phase 12 — VideoBuds Rebrand + Light/Dark Theme](#phase-12--videobuds-rebrand--lightdark-theme)
15. [Phase 13 — Security Enhancements](#phase-13--security-enhancements)
16. [Phase 14 — Workflow Recipes System](#phase-14--workflow-recipes-system)
17. [Phase 15 — AI Personas](#phase-15--ai-personas)
18. [Phase 16 — Script AI Agent](#phase-16--script-ai-agent)
19. [Phase 17 — Model Picker & Pricing Display](#phase-17--model-picker--pricing-display)
20. [Phase 18 — Ad Video Maker Wired (R38)](#phase-18--ad-video-maker-wired-r38)
21. [Phase 19 — Compound Engineering & Ralph Loop](#phase-19--compound-engineering--ralph-loop)
22. [Phase 20 — Polish, Security Hardening & Gap Analysis](#phase-20--polish-security-hardening--gap-analysis)
23. [Phase 21 — News Digest Recipe Wiring](#phase-21--news-digest-recipe-wiring)
24. [Phase 22 — Bug Fixes, Missing Features & Hardening](#phase-22--bug-fixes-missing-features--hardening)
25. [Phase 23 — Photo to Ad Recipe Wiring](#phase-23--photo-to-ad-recipe-wiring)
26. [Phase 24 — Video Quality & Playback Fixes](#phase-24--video-quality--playback-fixes)
27. [Phase 25 — Photo Library Upload Fix](#phase-25--photo-library-upload-fix)
28. [Phase 26 — Brand/Persona Gap Analysis & Integration Plan](#phase-26--brandpersona-gap-analysis--integration-plan)
29. [Phase 27 — Brand/Persona Integration Implementation](#phase-27--brandpersona-integration-implementation)
30. [Ralph Loop Full Audit](#ralph-loop-full-audit)
31. [Phase 28A — Security Hardening](#phase-28a--security-hardening)
32. [Phase 28B — Resilience Hardening](#phase-28b--resilience-hardening)
33. [Phase 28C — Persona Expansion](#phase-28c--persona-expansion)
34. [Phase 28D — Code Quality](#phase-28d--code-quality)
35. [Phase 29 — Gap Fixes & E2E Verification](#phase-29--gap-fixes--e2e-verification)
36. [Phase 30 — OWASP Top 10 Security Hardening](#phase-30--owasp-top-10-security-hardening)
37. [Phase 31 — Ad Video Maker Bug Fixes & UX Hardening](#phase-31--ad-video-maker-bug-fixes--ux-hardening)
38. [Phase 32 — News Digest SEO / GEO / AEO Optimization](#phase-32--news-digest-seo--geo--aeo-optimization)
39. [Phase 33 — Activate Image Creator Recipe](#phase-33--activate-image-creator-recipe)
40. [Phase 34 — Video Creator + OWASP A04 + SQLAlchemy Fix + AI Content Machine](#phase-34--video-creator--owasp-a04--sqlalchemy-fix--ai-content-machine)
41. [Phase 35 — E2E Playwright Testing](#phase-35--e2e-playwright-testing)
42. [Phase 36 — Higgsfield Seedance & Minimax Video Models](#phase-36--higgsfield-seedance--minimax-video-models)
43. [Phase 37 — Brand Guideline System Prompt Enhancement](#phase-37--brand-guideline-system-prompt-enhancement)
44. [Phase 38 — Extended Video Duration Options](#phase-38--extended-video-duration-options)
45. [Phase 39 — Output Rendering Bug Fixes & Gap Analysis](#phase-39--output-rendering-bug-fixes--gap-analysis)
46. [Phase 40 — AI Content Editor + News Digest Grounding](#phase-40--ai-content-editor--news-digest-grounding)
47. [Phase 41 — Talking Avatar + Influencer Content Kit + Persona Wiring](#phase-41--talking-avatar--influencer-content-kit--persona-wiring)
48. [Database Models](#database-models)
30. [All Routes & Endpoints](#all-routes--endpoints)
31. [All Templates](#all-templates)
32. [All Services](#all-services)
33. [All AI Providers](#all-ai-providers)
34. [Cost Configuration](#cost-configuration)
35. [Design System](#design-system)
36. [Configuration & Environment](#configuration--environment)
37. [Auto-Seeded Accounts](#auto-seeded-accounts)
38. [Master Plan (Future)](#master-plan-future)
39. [Bug Fixes & Resolutions](#bug-fixes--resolutions)

---

## Project Overview

**VideoBuds** is an AI-powered video and content creation studio for agency owners and creators. It provides:

- AI-powered brand onboarding and guideline generation
- 30-day campaign planning with AI-written captions and scene descriptions
- Multi-provider image generation (Google AI Studio, Kie AI, Higgsfield, WaveSpeed)
- Post approval workflows with AI learning from feedback
- Dual pricing (actual cost vs retail cost) for white-label reselling
- Admin dashboard with profit/margin tracking
- Export to ZIP (images + captions CSV)

**Powered by:** Flask + SQLAlchemy + HTMX + Tailwind CSS (no React/Vue build step)

---

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Backend | Flask (Python) |
| Database | SQLAlchemy ORM + SQLite |
| Auth | Flask-Login + werkzeug password hashing |
| Frontend | Tailwind CSS CDN + HTMX 1.9.10 |
| AI Text | Google Gemini 2.5 Flash |
| AI Images | Google Gemini 2.5 Flash / 3 Pro, Kie AI, Higgsfield, WaveSpeed |
| AI Video | Veo 3.1, Kling 3.0, Sora 2 Pro (planned) |
| Analytics | PostHog (optional, fails silently) |
| Server | Port 8080, Flask debug mode |

---

## Phase 1 — Core App Scaffold

**What was built:**
- Flask application factory (`app/__init__.py`)
- Configuration system with dev/prod modes (`app/config.py`)
- SQLAlchemy + Flask-Login extensions (`app/extensions.py`)
- Blueprint-based route registration (`app/routes/__init__.py`)
- Base template with Tailwind CDN + HTMX (`app/templates/base.html`)
- Run script on port 8080 (`run.py`)
- `.gitignore` for security (protects `.env`, `.db`, uploads, `.claude/`)

**Files created:**
- `app/__init__.py`
- `app/config.py`
- `app/extensions.py`
- `app/routes/__init__.py`
- `app/templates/base.html`
- `app/static/css/custom.css`
- `run.py`
- `.gitignore`

---

## Phase 2 — Brand Hub

**What was built:**
- Brand model with full identity fields (colors, voice, audience, pillars, visual style)
- Brand questionnaire model for AI onboarding
- Reference image model for photo libraries
- Brand CRUD routes (list, create, edit, delete, activate)
- AI-powered brand questionnaire with website/social scraping
- Auto-generated brand guidelines (markdown)
- Photo library with categories (product, personal, inspiration)
- Brand switcher dropdown in sidebar navigation

**Key features:**
- Multi-brand management — each user can have multiple brands
- Active brand concept — one brand is "active" at a time
- AI brand analysis scrapes website and social media for context
- Brand doc auto-generation creates full marketing guidelines

**Files created:**
- `app/models/brand.py`
- `app/models/questionnaire.py`
- `app/models/reference_image.py`
- `app/routes/brands.py`
- `app/templates/brands/list.html`
- `app/templates/brands/new.html`
- `app/templates/brands/detail.html`
- `app/templates/brands/questionnaire.html`
- `app/templates/brands/photo_library.html`

---

## Phase 3 — Campaign Engine

**What was built:**
- Campaign model with status tracking (draft → generating → review → approved → exported)
- Post model with per-day slots, captions, prompts, and status
- Campaign CRUD routes (list, create, delete)
- Calendar grid UI with weekly rows
- AI campaign planner fills all 30 days with captions + scene descriptions
- Style presets system (pop art, minimalist, corporate, UGC, flat lay, cinematic)
- Campaign intentions (brand awareness, product launch, engagement, education, seasonal, behind scenes, sales)
- Rotating content pillars and image types across days
- Cost estimation before generation

**Files created:**
- `app/models/campaign.py`
- `app/models/post.py`
- `app/routes/campaigns.py`
- `app/templates/campaigns/list.html`
- `app/templates/campaigns/new.html`
- `app/templates/campaigns/calendar.html`

---

## Phase 4 — Image Generation Pipeline

**What was built:**
- Generation model tracking every job (prompt, model, provider, costs, status)
- Generate routes for single, per-day, and bulk generation
- Google AI Studio provider (Gemini 2.5 Flash + 3 Pro image models)
- Kie AI provider (image + video models)
- Provider routing system mapping models to providers
- Async polling for non-synchronous providers
- Automatic image upload to Kie.ai for hosting
- Real-time generation status via HTMX polling (every 3s)

**Files created:**
- `app/models/generation.py`
- `app/routes/generate.py`
- `tools/providers/__init__.py`
- `tools/providers/google.py`
- `tools/providers/kie.py`
- `tools/config.py`

---

## Phase 5 — Post Management & Calendar UI

**What was built:**
- Post editor side panel loaded via HTMX
- Post card partial for calendar grid
- Creative controls with tabs (Style Preset, Mood Board, Full Prompt)
- Approve/reject workflow
- Reference image upload per campaign (mood board)
- Caption field with AI suggestion button
- Prompt override with AI enhancement button
- Export route with ZIP download (images + captions.csv)

**Files created:**
- `app/routes/posts.py`
- `app/routes/export.py`
- `app/routes/api.py`
- `app/templates/components/post_editor.html`
- `app/templates/components/post_card.html`
- `app/templates/components/style_picker.html`
- `app/templates/components/caption_suggestions.html`
- `app/templates/components/prompt_enhanced.html`
- `app/templates/campaigns/export.html`

---

## Phase 6 — AI Agent Integration

**What was built:**
- Agent service powered by Gemini 2.5 Flash
- `analyze_brand()` — deep brand analysis from questionnaire + web scraping
- `plan_campaign()` — generate captions and scene descriptions for every day
- `write_captions()` — 3 caption variants per post (emotional, educational, provocative)
- `build_smart_prompt()` — AI-enhanced image generation prompts
- `learn_from_feedback()` — stores approve/reject preferences in AgentMemory
- `select_photos()` — AI picks 1-3 most relevant photos from library
- AgentMemory model for long-term memory (brand briefs, preferences, campaign plans)
- Prompt service with style preset templates + AI fallback

**Files created:**
- `app/models/agent_memory.py`
- `app/services/agent_service.py`
- `app/services/prompt_service.py`

---

## Phase 7 — Multi-Provider Architecture

**What was built:**
- WaveSpeed AI provider (GPT Image 1.5, Kling 3.0, Sora 2/Pro)
- Provider override support (user can choose provider per generation)
- Sync vs async detection per provider
- Dynamic polling URL storage for WaveSpeed
- Cost service with per-provider pricing
- Analytics service with PostHog integration

**Files created:**
- `tools/providers/wavespeed.py`
- `app/services/cost_service.py`
- `app/services/analytics_service.py`

---

## Phase 8 — Admin vs User Dashboard Separation

**What was built:**
- `User.is_admin` boolean field
- Separate `_admin_dashboard()` and `_user_dashboard()` functions
- Admin dashboard: platform-wide stats (total users, brands, campaigns, revenue, actual cost, profit, margin)
- Admin dashboard: recent activity table, top users leaderboard
- User dashboard: personal stats (brands, campaigns, images generated, total spent)
- "View as User" toggle for admin to preview user experience
- "Viewing as User" banner at top of content area when toggled
- Admin badge in sidebar footer
- Session-based toggle (`session["admin_user_view"]`)

**Files modified:**
- `app/models/user.py` — added `is_admin` field
- `app/routes/dashboard.py` — split into admin/user views + toggle route
- `app/templates/dashboard/admin.html` — new admin-only template
- `app/templates/dashboard/index.html` — user dashboard
- `app/templates/base.html` — admin badge, toggle button, viewing banner

---

## Phase 9 — Dual Pricing System

**What was built:**
- `Generation.cost` — actual cost (what operator pays the AI provider)
- `Generation.retail_cost` — retail cost (what end users see)
- Separate cost tables: actual costs vs retail costs in `tools/config.py`
- Admin sees both actual + retail in dashboard
- Users only see retail pricing
- Profit = Revenue (retail) - Actual Cost
- Margin = Profit / Revenue × 100
- Free providers (Google AI Studio, Higgsfield) have $0.00 actual cost but normal retail pricing

---

## Phase 10 — Higgsfield API Integration

**What was built:**
- Higgsfield provider with Key ID:SECRET authentication format
- Support for nano-banana and nano-banana-pro image models
- Async submit/poll generation pattern
- Reference image URL support
- Custom dimension mapping from aspect ratios
- `HIGGSFIELD_API_KEY_ID` and `HIGGSFIELD_API_KEY_SECRET` env vars
- Registered in provider routing table with $0.00 actual cost

**Files created:**
- `tools/providers/higgsfield.py`

**Files modified:**
- `tools/config.py` — added Higgsfield API keys, costs, and provider mappings
- `tools/providers/__init__.py` — registered Higgsfield in routing

---

## Phase 11 — Design Overhaul ("The Co-Founder" Theme)

**What was built:**
Full visual redesign of all 20+ templates to match "The Co-Founder" platform aesthetic (deep navy/purple palette, fixed left sidebar navigation).

### Layout Changes
- **Before:** Top navigation bar with gray theme
- **After:** Fixed left sidebar (256px / w-64) with grouped nav sections

### Sidebar Structure
```
[VideoBuds Logo + Gradient Icon]
[Brand Switcher Dropdown]

CONTENT
  Dashboard        (home icon)
  Brands           (tag icon)
  Campaigns        (calendar icon)

STUDIO
  Video Studio     (film icon) — "Coming Soon" badge

─────────────────────────────
[Admin: View as User toggle]
[User avatar + name]
[Admin badge if admin]
[Sign Out]
```

### Color Mapping Applied
| Element | Old | New |
|---------|-----|-----|
| Page background | gray-900 | `#0D0B1A` |
| Sidebar | gray-800 | `#13111C` |
| Cards/surfaces | gray-800 | `#1A1730` |
| Card borders | gray-700 | `#2A2740` |
| Input fields | gray-700 | `#13111C` |
| Primary accent | `#0066FF` (blue) | `#7C3AED` (violet) |
| Primary hover | `#0055DD` | `#6D28D9` |
| Active nav text | blue-400 | `#A78BFA` (light purple) |
| Gradient | blue → pink | `#7C3AED` → `#3B82F6` |

### Files Modified (20 templates + CSS)
1. `app/templates/base.html` — Complete rewrite (top-nav → sidebar)
2. `app/static/css/custom.css` — Dark navy theme
3. `app/templates/auth/login.html` — Navy/purple centered form
4. `app/templates/auth/register.html` — Navy/purple centered form
5. `app/templates/dashboard/index.html` — New card colors
6. `app/templates/dashboard/admin.html` — Violet profit card, purple buttons
7. `app/templates/brands/list.html` — Updated colors
8. `app/templates/brands/new.html` — Updated colors
9. `app/templates/brands/detail.html` — Updated colors
10. `app/templates/brands/questionnaire.html` — Purple step indicators
11. `app/templates/brands/photo_library.html` — Updated colors
12. `app/templates/campaigns/list.html` — Updated colors
13. `app/templates/campaigns/new.html` — Updated colors
14. `app/templates/campaigns/calendar.html` — Updated grid + editor
15. `app/templates/campaigns/export.html` — Updated colors
16. `app/templates/components/post_editor.html` — Violet tabs, buttons, style cards
17. `app/templates/components/post_card.html` — Navy card backgrounds
18. `app/templates/components/style_picker.html` — Violet selected state
19. `app/templates/components/caption_suggestions.html` — Violet hover states
20. `app/templates/components/prompt_enhanced.html` — Violet accent
21. `app/templates/errors/404.html` — Violet icon + buttons
22. `app/templates/errors/500.html` — Navy theme buttons

### Mobile Support
- Sidebar hidden on screens < 1024px
- Hamburger menu toggle with overlay
- Off-canvas sidebar slides in from left

---

## Phase 12 — VideoBuds Rebrand + Light/Dark Theme

**What was built:**
Complete rebrand from "ScaleBuds" to "VideoBuds" and full theme redesign.

### Rebrand
- App name → "VideoBuds" across all code, templates, comments, and localStorage keys
- Database → `videobuds.db`
- localStorage key → `vb-dark-mode`
- All seeded email addresses updated

### Theme Redesign
User rejected the dark navy/purple theme and requested a white/light default with dark mode toggle.

| Element | New Light | New Dark |
|---------|-----------|----------|
| Page | `bg-gray-50` | `bg-[#0F0F0F]` |
| Cards | `bg-white` | `bg-[#1E1E1E]` |
| Sidebar | `bg-white` | `bg-[#1A1A1A]` |
| Inputs | `bg-white` | `bg-[#141414]` |
| Borders | `border-[#26A0D8]/20` | `border-[#26A0D8]/40` |
| Primary accent | `#F18523` (Pumpkin Pie) | Same |
| Secondary accent | `#26A0D8` (Azure Afternoon) | Same |

### Dark Mode Toggle
- Sun/moon icon button in sidebar footer
- Anti-flash script in `<head>` reads localStorage before render
- All 20+ templates support both modes with `dark:` Tailwind variants

**Files modified:** All 20+ templates, `custom.css`, `config.py`, `__init__.py`

---

## Phase 13 — Security Enhancements

**What was built:**
- `app/security.py` — centralised security module
- HTTP security headers middleware (`X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy`, `Cache-Control`)
- Rate limiting with in-memory token bucket (`_RateLimiter` class + `rate_limit` decorator)
  - Login: 15 attempts/min/IP
  - Registration: 5 attempts/min/IP
- `safe_int()` helper for safe integer parsing from form data
- CSRF tokens in all forms
- 429 error page (`app/templates/errors/429.html`)
- PostHog integration (`app/services/analytics_service.py`)
  - JS snippet conditionally injected into `base.html`
  - Server-side event tracking for login/register
  - User identification on auth

**Files created:**
- `app/security.py`
- `app/services/analytics_service.py`
- `app/templates/errors/429.html`

**Files modified:**
- `app/__init__.py` — register security headers, 429 handler
- `app/routes/auth.py` — rate limiting, PostHog tracking
- `app/templates/base.html` — PostHog JS snippet
- `app/config.py` — `POSTHOG_API_KEY`, `POSTHOG_HOST`

---

## Phase 14 — Workflow Recipes System

**What was built:**
A complete workflow automation system with 13 recipes, a generic UI, and background execution.

### Architecture
- `BaseRecipe` abstract class with metadata, input fields, steps, and `execute()` method
- `InputField` dataclass (name, label, type, required, default, choices, help_text)
- Auto-discovery registry in `app/recipes/__init__.py` — imports all modules, registers subclasses
- Public API: `get_all_recipes()`, `get_recipe(slug)`, `recipe_count()`, `get_recipes_by_category()`

### Database Models
- `Recipe` — catalog entries (slug, name, category, icon, usage_count, estimated_cost_label)
- `RecipeRun` — execution tracking (status, progress, inputs/outputs JSON, cost, error_message)

### 13 Recipes Defined
| # | Slug | Name | Category |
|---|------|------|----------|
| 1 | ad-video-maker | 🎬 Ad Video Maker | content-creation |
| 2 | influencer-content-kit | 🤳 Influencer Content Kit | content-creation |
| 3 | image-creator | 🖼️ Image Creator | content-creation |
| 4 | video-creator | 📹 Video Creator | content-creation |
| 5 | photo-to-ad | 📸 Photo-to-Ad | content-creation |
| 6 | talking-avatar | 🎭 Talking Avatar | video-studio |
| 7 | motion-capture | 🕺 Motion Capture | video-studio |
| 8 | multi-scene-video | 🎞️ Multi-Scene Video | video-studio |
| 9 | style-cloner | 🎨 Style Cloner | video-studio |
| 10 | clip-factory | ✂️ Clip Factory | repurpose-edit |
| 11 | vertical-reframe | 📐 Vertical Reframe | repurpose-edit |
| 12 | social-scraper | 🔍 Social Scraper | research-intelligence |
| 13 | news-digest | 📰 News Digest | research-intelligence |

### Routes (`app/routes/recipes.py`)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/recipes/` | Recipe library (card grid, categories) |
| GET | `/recipes/<slug>/` | Recipe detail (description + how-to-use) |
| GET/POST | `/recipes/<slug>/run/` | Run form + kick off execution |
| GET | `/recipes/run/<id>/status` | Run status page (HTMX polling) |
| POST | `/recipes/run/<id>/approve` | Approve script → launch Phase 2 |
| GET | `/recipes/run/<id>/status.json` | Run progress JSON |
| GET | `/recipes/history/` | Past runs table |

### Templates
- `recipes/library.html` — card grid with categories and count badge
- `recipes/detail.html` — description + Markdown how-to-use guide
- `recipes/run.html` — dynamic form from `get_input_fields()`
- `recipes/run_status.html` — HTMX page polling progress
- `recipes/_run_progress.html` — progress bar partial + results display
- `recipes/history.html` — past runs table

### Background Execution
- `_launch_recipe_execution()` spawns a daemon thread
- `_execute_recipe()` runs within `app.app_context()` in the thread
- `_make_progress_callback()` updates `RecipeRun` status in real-time
- HTMX polls `/progress` every 3 seconds for live updates

### Sidebar
- "Recipes" link added under "CONTENT" section
- Dynamic count badge showing `total_recipe_count`

**Files created:**
- `app/recipes/__init__.py`
- `app/recipes/base.py`
- `app/recipes/ad_video_maker.py` (+ 12 more recipe files)
- `app/models/recipe.py`
- `app/models/recipe_run.py`
- `app/routes/recipes.py`
- `app/templates/recipes/` (6 templates)

**Files modified:**
- `app/models/__init__.py` — import new models
- `app/models/user.py` — add relationships
- `app/routes/__init__.py` — register `recipes_bp`
- `app/__init__.py` — add `total_recipe_count` to global context, add `simple_md` filter
- `app/templates/base.html` — add Recipes sidebar link

---

## Phase 15 — AI Personas

**What was built:**
Brand voice and personality profile system.

### Database Model (`UserPersona`)
- user_id, name, is_default, tone, voice_style, bio, industry
- target_audience, brand_keywords (JSON), avoid_words (JSON)
- sample_phrases (JSON), writing_guidelines, ai_prompt_summary

### Routes (`app/routes/personas.py`)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/personas/` | List all personas |
| GET/POST | `/personas/create` | Multi-step creation wizard |
| GET/POST | `/personas/<id>/edit` | Edit persona |
| POST | `/personas/<id>/set-default` | Set as default |
| POST | `/personas/<id>/delete` | Delete persona |

### Features
- Multi-step creation wizard (JS-powered step navigation)
- AI-generated prompt summary from persona details (Gemini)
- Default persona concept — one per user
- JSON list fields for keywords, avoid words, sample phrases

**Files created:**
- `app/models/user_persona.py`
- `app/routes/personas.py`
- `app/templates/personas/index.html`
- `app/templates/personas/wizard.html`
- `app/templates/personas/edit.html`

---

## Phase 16 — Script AI Agent

**What was built:**
AI-powered script writing agent for viral video content.

### Service (`app/services/script_service.py`)
| Function | Description |
|----------|-------------|
| `write_script()` | Generate a script in user's voice |
| `research_topic()` | Research a topic for script context |
| `research_and_write()` | Research then write (combined) |
| `rewrite_script()` | Rewrite existing script in user's voice |
| `script_to_scenes()` | Decompose script into video scenes |
| `get_script_types()` | List all script type definitions |
| `get_script_type_choices()` | Choices for form dropdowns |

### Script Types
UGC, Tutorial, Vlog, Interview, Product Review, Testimonial, Behind-the-Scenes, Day-in-the-Life, Reaction, How-To, Explainer, Comparison

### Data Classes
- `ScriptResult` — single script output (title, script, hook, scenes, metadata)
- `ScriptBatch` — batch generation results

**Files created:**
- `app/services/script_service.py`

---

## Phase 17 — Model Picker & Pricing Display

**What was built:**
Complete model selection and pricing system integrated into the post editor.

### Model Catalog Service (`app/services/model_service.py`)
- `get_model_catalog(model_type)` — returns all models with pricing, providers, icons
- `get_model_choices(model_type)` — formatted for template consumption
- `get_model_price(model, provider)` — lookup cheapest price for a model
- Aggregates data from `tools.config` and `tools.providers`

### Reusable Model Picker (`app/templates/components/model_picker.html`)
- Radio-button card grid for model selection
- Per-model retail price display
- Green "FREE" badge for free-tier models
- Provider sub-selector for models with multiple providers
- Orange checkmark on selected model
- JS functions for selection handling

### Post Editor Integration
- New "Model" tab (default active) alongside Style Preset / Mood Board / Full Prompt
- Model picker included via Jinja `{% include %}` with context
- Generate button shows dynamic price badge (`$0.00` / `$0.07` etc.)
- Hidden form fields for `model` and `provider` synced by JS

### Post Model Persistence
- `Post.model` and `Post.provider` database columns added
- Routes read model/provider from form and persist to DB
- Helper `_get_model_context()` provides template data

### API Endpoint
- `GET /api/models` — returns full model catalog as JSON
- `GET /api/models?type=image` — filtered by type

### Standalone Pricing Page
- `GET /pricing` — table of all models, providers, pricing
- Free tier highlighting in green
- Added to sidebar under "You" section

**Files created:**
- `app/services/model_service.py`
- `app/templates/components/model_picker.html`
- `app/templates/dashboard/pricing.html`

**Files modified:**
- `app/models/post.py` — added `model`, `provider` columns
- `app/routes/posts.py` — inject model context, persist model/provider
- `app/routes/generate.py` — accept model/provider from form, pass to generation
- `app/routes/dashboard.py` — pricing route
- `app/routes/api.py` — `/api/models` endpoint
- `app/templates/components/post_editor.html` — Model tab + price badge
- `app/templates/base.html` — Pricing sidebar link

---

## Phase 18 — Ad Video Maker Wired (R38)

**What was built:**
The first fully end-to-end working recipe — "Ad Video Maker" (R38).

### Pipeline (verified working ✅)
1. **Step 0: Analyse** — Gemini text API analyses uploaded product photo + user script
2. **Step 1: Write creative scenes** — Gemini generates scene descriptions, motion prompts, ad copy (JSON array)
3. **Step 2: Generate scene images** — Google Nano Banana Pro creates hero images per scene
4. **Step 3: Create videos** — Google Veo 3.1 creates short videos from each generated image
5. **Step 4: Finalise output** — Collects all images, videos, and ad copy

### Key Technical Fixes
- `tools/create_video.py` updated to accept `image_path` parameter (not just `image_url`)
- Auto-detects local file paths: if `image_url` is not HTTP, treats as `image_path`
- Google provider's `submit_video()` handles local files via base64 encoding
- Kie/WaveSpeed providers accept `**kwargs` — safely ignore `image_path`
- Progress callback simplified — no nested `app_context()` (runs inside `_execute_recipe`'s context)
- Recipe file upload validates extensions against `ALLOWED_IMAGE_EXT`

### Cost Tracking
- Each step accumulates cost via `tools.config.get_actual_cost()`
- Final cost persisted to `RecipeRun.cost` and `RecipeRun.retail_cost`

### Results Display
- `_run_progress.html` shows output cards with download links
- Images/videos displayed inline with labels
- Ad copy shown as text snippets

**Files modified:**
- `app/recipes/ad_video_maker.py` — full `execute()` implementation
- `app/routes/recipes.py` — background thread execution, file validation
- `tools/create_video.py` — `image_path` support + auto-detection
- `app/templates/recipes/_run_progress.html` — results display

---

## Phase 19 — Compound Engineering & Ralph Loop

**What was built:**
Complete refactoring of the Ad Video Maker to implement multimodal AI, product-anchored prompts,
a 2-phase execution workflow with script approval, and organized asset storage. Plus comprehensive
security audit and end-to-end verification.

### Problem Identified
The Ad Video Maker was generating off-brand content (e.g., showing skincare when given sunglasses).
Root cause: AI was performing **text-only** analysis — it never actually "saw" the product image.
Additionally, there was no way to review or approve scripts before expensive video generation.

### Gap Analysis Results
| Gap | Severity | Solution |
|-----|----------|----------|
| Text-only image analysis | Critical | Multimodal Gemini (`_call_gemini_with_image`) |
| No script approval | Critical | 2-phase execution with `awaiting_approval` status |
| Generic prompts | High | Product-anchored scenes using vision analysis |
| Unorganized assets | Medium | Structured `run_<id>/` directories |
| Missing output serving | High | `/api/outputs/<filename>` route |
| Veo RAI filter blocking | High | `personGeneration: "allow_adult"` parameter |
| KIE_API_KEY required | Medium | Local fallback when key not set |
| Stale DB URLs | Low | Data migration script for existing runs |

### Compound Engineering Architecture
```
Phase 1 (SCRIPT)
  ┌─────────────────────────────────────────────┐
  │ 1. Multimodal Vision → product analysis     │
  │ 2. Product-anchored scene writing           │
  │ → status: awaiting_approval                 │
  └─────────────────┬───────────────────────────┘
                    │ User reviews & edits
                    ▼
Phase 2 (PRODUCTION)
  ┌─────────────────────────────────────────────┐
  │ 3. Generate images (Nano Banana Pro)        │
  │ 4. Generate videos (Veo 3.1)               │
  │ 5. Organize assets → run_<id>/              │
  │ → status: completed                         │
  └─────────────────────────────────────────────┘
```

### Ralph Loop Implementation
| Step | Action | Implementation |
|------|--------|---------------|
| **Research** | Multimodal image analysis | `_call_gemini_vision()` — AI sees the actual product |
| **Analyze** | Extract product identity | Detailed prompt extracts type, colors, materials, features |
| **Learn** | Product context injection | Vision analysis injected into scene-writing prompt |
| **Plan** | Product-anchored scenes | Every scene must reference the exact product |
| **Hypothesize** | Approval gate | User reviews/edits before production (feedback loop) |

### Multimodal Gemini Integration
New function `_call_gemini_with_image()` in `app/services/agent_service.py`:
- Accepts text prompt + local image path
- Opens image file, detects MIME type, base64-encodes
- Sends multipart request to Gemini's `generateContent` API
- Returns text response from the model
- Fallback to text-only if image is unavailable

### 2-Phase Execution Workflow
- `execute()` dispatches to `_execute_script()` or `_execute_production()` based on `inputs['_phase']`
- Phase 1 returns `{"phase": "script", "outputs": [...]}` → route sets status to `awaiting_approval`
- New route `POST /recipes/run/<id>/approve` — collects edited scenes, launches Phase 2
- Phase 2 receives approved scenes in `inputs['_approved_scenes']`

### Script Approval UI
- `_run_progress.html` renders editable scene fields when `run.status == 'awaiting_approval'`
- Each scene shows: description (textarea), motion prompt (input), ad copy (input)
- "Approve & Generate Videos" button POSTs to approve endpoint
- HTMX polling pauses during `awaiting_approval` status

### Asset Organization
- All generated files saved to `references/outputs/run_<id>/`
- File naming: `input_product.jpg`, `scene_1_image.jpg`, `scene_1_video.mp4`
- `metadata.json` contains run ID, scenes, cost, output count
- Reference image copied into run directory for provenance

### Video Pipeline Fixes
1. **`personGeneration: "allow_adult"`** — prevents Veo RAI filter from blocking UGC content
2. **RAI filter detection** — checks for `raiMediaFilteredReasons` in API response
3. **Robust response parsing** — multiple fallback paths for extracting video URI
4. **Debug logging** — dumps full Veo JSON to `veo_debug_*.json` for troubleshooting
5. **Local video fallback** — saves locally when `KIE_API_KEY` not set, serves via `/api/outputs/`
6. **Auth headers on download** — adds API key when downloading from Google-hosted URIs

### Output Serving
- New route: `GET /api/outputs/<filename>` in `app/routes/api.py`
- Serves files from `references/outputs/` directory
- Protected with `@login_required`
- `send_from_directory()` with proper MIME type detection

### Security Audit (Passed ✅)
| Area | Status | Details |
|------|--------|---------|
| Authentication | ✅ | All routes use `@login_required` (except auth) |
| Authorization | ✅ | All queries filter by `current_user.id` |
| CSRF | ✅ | Tokens in all forms |
| Rate Limiting | ✅ | Auth routes rate-limited (15 login/min, 5 register/min) |
| Security Headers | ✅ | X-Content-Type-Options, X-Frame-Options, etc. |
| File Upload | ✅ | Extension validation via `ALLOWED_UPLOAD_EXT` |
| `| safe` Filter | ✅ | Only on developer-authored content (recipe how_to_use) |
| SQL Injection | ✅ | All queries use SQLAlchemy ORM (parameterized) |

### E2E Compile Check (Passed ✅)
- All 8 critical routes verified: `/recipes/`, detail, run, status, approve, status.json, history, `/api/outputs/`
- All 13 recipes registered and importable
- AdVideoMaker has all methods: `execute`, `_execute_script`, `_execute_production`
- Flask app starts without errors

### Data Migration
- Existing RecipeRun entries had absolute file paths in outputs JSON
- Migration script converted paths to web-accessible `/api/outputs/<filename>` format
- Stuck "running" run marked as "failed"

**Files created:**
- None (all changes to existing files)

**Files modified:**
- `app/services/agent_service.py` — added `_call_gemini_with_image()` multimodal function
- `app/recipes/ad_video_maker.py` — complete rewrite with 2-phase architecture, vision AI, asset organization
- `app/routes/recipes.py` — 2-phase execution handling, `approve_script` route, ALLOWED_UPLOAD_EXT
- `app/models/recipe_run.py` — added `awaiting_approval` to status docstring
- `app/templates/recipes/_run_progress.html` — approval UI, inline video/image display, editable scenes
- `app/templates/recipes/run_status.html` — HTMX polling control based on status
- `app/routes/api.py` — `/api/outputs/<filename>` serving route
- `tools/providers/google.py` — `personGeneration`, RAI detection, response parsing, local fallback, debug logging
- `tools/create_video.py` — `image_path` auto-detection

---

## Phase 20 — Polish, Security Hardening & Gap Analysis

**What was built:**
Final polish pass covering clean text rendering, security hardening, E2E verification,
gap analysis, and SOLID principles review.

### Clean Text Outputs
- **Problem:** AI-generated text outputs displayed raw markdown formatting (e.g., `*` for lists, `**` for bold) in the recipe run UI and brand detail pages.
- **Fix:**
  1. Replaced `<pre>` tags with `<div>` elements and applied `| simple_md | safe` filter in `_run_progress.html` for both `awaiting_approval` and `completed` output sections.
  2. Enhanced the `simple_md` Jinja filter in `app/__init__.py` to correctly render `*` as unordered list items (in addition to existing `-` support).
  3. Applied `| simple_md | safe` to `brand.brand_doc` in `app/templates/brands/detail.html`.

### Video Generation Path Resolution
- **Problem:** `create_video.py` failed to generate videos when the input `image_url` was `/api/outputs/filename.jpg` — not a direct file path or remote URL.
- **Fix:** Modified `tools/create_video.py` to resolve `/api/outputs/<filename>` paths to their local filesystem equivalents (`PROJECT_ROOT/references/outputs/filename`) before passing to the video generation provider.

### CSRF Token on Approval Form
- **Problem:** The script approval form in `_run_progress.html` was missing a CSRF token.
- **Fix:** Added `<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">` to the form.

### SQLite Readonly Database Fix
- **Problem:** `OperationalError: attempt to write a readonly database` on login due to macOS extended attributes (`com.apple.provenance`) on `videobuds.db`.
- **Fix:** Deleted the old database file and let the Flask app recreate a fresh one on startup. Documented in "Known Issues" for future reference.

### Full Security Audit (Passed ✅)
Systematic review of every route, template, and form:

| Area | Status | Details |
|------|--------|---------|
| Authentication | ✅ | All routes use `@login_required` (except auth) |
| Authorization | ✅ | All DB queries filter by `current_user.id` |
| CSRF | ✅ | All POST forms have `csrf_token` hidden fields |
| Rate Limiting | ✅ | Auth routes rate-limited (15 login/min, 5 register/min) |
| Security Headers | ✅ | `register_security_headers()` called in `create_app()` |
| File Upload | ✅ | Extension validation via `ALLOWED_UPLOAD_EXT` |
| `| safe` Filter | ✅ | Only on developer-authored content + `simple_md` filtered AI output |
| SQL Injection | ✅ | All queries use SQLAlchemy ORM (parameterized) |
| XSS | ✅ | Jinja2 auto-escaping on; `| safe` only after `simple_md` sanitization |

### E2E Compile & Runtime Check (Passed ✅)
8 critical checks verified:

1. ✅ All 6 blueprints registered (auth, dashboard, brands, campaigns, recipes, personas)
2. ✅ All 50+ routes importable and accessible
3. ✅ All 13 recipes registered in the recipe registry
4. ✅ AdVideoMaker has `execute`, `_execute_script`, `_execute_production` methods
5. ✅ All 11 models importable
6. ✅ All 6 services importable
7. ✅ All 5 tool modules importable
8. ✅ Flask app starts, creates DB tables, seeds users, responds to HTTP

### Gap Analysis Results

| Gap | Severity | Status | Action |
|-----|----------|--------|--------|
| 12 stub recipes | Medium | Known | Implement `execute()` per recipe when needed |
| No automated tests | Low | Deferred | Add pytest suite in future phase |
| No CI/CD pipeline | Low | Deferred | GitHub Actions when repository is public |
| No input sanitization on recipe text fields | Low | Acceptable | Jinja2 auto-escaping handles display; DB uses ORM |
| No rate limiting on recipe runs | Low | Acceptable | Compute cost limits natural abuse |
| No pagination on history page | Low | Acceptable | Small user base, will add when needed |

### SOLID Principles Review

| Principle | Status | Evidence |
|-----------|--------|----------|
| **Single Responsibility** | ✅ | Each recipe in its own file; each service handles one domain; routes separated by blueprint |
| **Open/Closed** | ✅ | `BaseRecipe` ABC — new recipes extend without modifying existing code; provider system pluggable |
| **Liskov Substitution** | ✅ | All recipe subclasses honour `BaseRecipe` contract; all providers honour submit/poll interface |
| **Interface Segregation** | ✅ | `InputField` dataclass is minimal; recipe metadata separate from execution |
| **Dependency Inversion** | ✅ | Routes depend on abstract recipe interface, not concrete implementations; services injected via imports |

### All 13 Recipes Audited
Every recipe file verified for:
- Correct class name and `slug` attribute
- Valid `get_input_fields()` returning `InputField` list
- Valid `get_steps()` returning step definitions
- `execute()` either fully implemented (AdVideoMaker) or raises `NotImplementedError` with clear message
- Proper `how_to_use` markdown guide
- Category and icon set

**Files modified:**
- `app/__init__.py` — `simple_md` filter enhanced for `*` list items
- `app/templates/recipes/_run_progress.html` — `simple_md | safe` for text outputs, CSRF token
- `app/templates/brands/detail.html` — `simple_md | safe` for brand doc
- `tools/create_video.py` — `/api/outputs/` path resolution

---

## Database Models

### User
| Field | Type | Notes |
|-------|------|-------|
| id | Integer | Primary key |
| email | String(120) | Unique, required |
| password_hash | String(256) | Werkzeug hash |
| display_name | String(100) | Optional |
| is_admin | Boolean | Default: False |
| created_at | DateTime | Auto-set |
| last_login_at | DateTime | Updated on login |

### Brand
| Field | Type | Notes |
|-------|------|-------|
| id | Integer | Primary key |
| user_id | Integer | Foreign key → User |
| name | String(100) | Required |
| tagline | String(300) | Optional |
| logo_path | String(500) | Optional |
| colors_json | Text | JSON string |
| voice_json | Text | JSON string |
| target_audience | Text | Free text |
| content_pillars | Text | JSON array |
| visual_style | Text | Free text |
| never_do | Text | Free text |
| hashtags | Text | Free text |
| caption_template | Text | Free text |
| brand_doc | Text | Markdown guidelines |
| is_active | Boolean | One per user |
| created_at / updated_at | DateTime | Auto-set |

### Campaign
| Field | Type | Notes |
|-------|------|-------|
| id | Integer | Primary key |
| brand_id | Integer | Foreign key → Brand |
| user_id | Integer | Foreign key → User |
| name | String(200) | Required |
| start_date | Date | Campaign start |
| end_date | Date | Campaign end |
| status | String(20) | draft/generating/review/approved/exported |
| style_preset | String(50) | Default: pop_art |
| mood_json | Text | JSON string |
| total_cost | Float | Accumulated cost |
| post_count | Integer | Default: 30 |
| intention | String(100) | Campaign goal |
| created_at / updated_at | DateTime | Auto-set |

### Post
| Field | Type | Notes |
|-------|------|-------|
| id | Integer | Primary key |
| campaign_id | Integer | Foreign key → Campaign |
| day_number | Integer | 1-30 |
| scheduled_date | Date | Calculated from campaign start |
| caption | Text | Post caption |
| image_prompt | Text | Resolved prompt |
| content_pillar | String(100) | From brand pillars |
| image_type | String(50) | ugc/studio/detail/lifestyle/cgi/flatlay |
| image_url | String(500) | Hosted URL |
| image_path | String(500) | Local path |
| status | String(20) | draft/generating/generated/approved/rejected |
| style_preset | String(50) | Override or inherited |
| custom_prompt | Text | User override |
| created_at / updated_at | DateTime | Auto-set |

### Generation
| Field | Type | Notes |
|-------|------|-------|
| id | Integer | Primary key |
| post_id | Integer | Foreign key → Post |
| campaign_id | Integer | Foreign key → Campaign |
| brand_id | Integer | Foreign key → Brand |
| user_id | Integer | Foreign key → User |
| prompt | Text | Full prompt sent |
| model | String(50) | nano-banana / nano-banana-pro / etc. |
| provider | String(50) | google / kie / higgsfield / wavespeed |
| aspect_ratio | String(20) | 1:1 / 16:9 / etc. |
| status | String(20) | pending/processing/success/failed |
| result_url | String(500) | Hosted image URL |
| local_path | String(500) | Local file path |
| error_message | Text | On failure |
| cost | Float | Actual cost (operator pays) |
| retail_cost | Float | Retail cost (user sees) |
| started_at / completed_at | DateTime | Timing |
| created_at | DateTime | Auto-set |

### BrandQuestionnaire
| Field | Type | Notes |
|-------|------|-------|
| id | Integer | Primary key |
| brand_id | Integer | Foreign key → Brand |
| question_key | String(100) | Question identifier |
| answer | Text | User's answer |
| created_at | DateTime | Auto-set |

### ReferenceImage
| Field | Type | Notes |
|-------|------|-------|
| id | Integer | Primary key |
| brand_id | Integer | Foreign key → Brand |
| campaign_id | Integer | Foreign key → Campaign (optional) |
| file_path | String(500) | Local path |
| hosted_url | String(500) | Remote URL |
| purpose | String(50) | product/personal/inspiration/mood |
| created_at | DateTime | Auto-set |

### AgentMemory
| Field | Type | Notes |
|-------|------|-------|
| id | Integer | Primary key |
| brand_id | Integer | Foreign key → Brand |
| memory_type | String(50) | brand_brief/preference/campaign_plan |
| campaign_id | Integer | Optional |
| content | Text | Memory content |
| created_at | DateTime | Auto-set |

### UserPersona
| Field | Type | Notes |
|-------|------|-------|
| id | Integer | Primary key |
| user_id | Integer | Foreign key → User |
| name | String(100) | Required |
| is_default | Boolean | One per user |
| tone | String(50) | e.g. "friendly", "professional" |
| voice_style | String(50) | e.g. "conversational", "authoritative" |
| bio | Text | Brand bio / backstory |
| industry | String(100) | User's industry |
| target_audience | Text | Who the content is for |
| brand_keywords_json | Text | JSON array of keywords |
| avoid_words_json | Text | JSON array of words to avoid |
| sample_phrases_json | Text | JSON array of example phrases |
| writing_guidelines | Text | Free text guidelines |
| ai_prompt_summary | Text | AI-generated prompt summary |
| created_at / updated_at | DateTime | Auto-set |

### Recipe
| Field | Type | Notes |
|-------|------|-------|
| id | Integer | Primary key |
| slug | String(100) | Unique, URL-safe |
| name | String(200) | Display name |
| description | Text | Short description |
| category | String(50) | Category key |
| icon | String(10) | Emoji icon |
| is_enabled | Boolean | Default: True |
| usage_count | Integer | Default: 0 |
| estimated_cost_label | String(50) | e.g. "~$0.50" |
| created_at / updated_at | DateTime | Auto-set |

### RecipeRun
| Field | Type | Notes |
|-------|------|-------|
| id | Integer | Primary key |
| recipe_id | Integer | Foreign key → Recipe |
| user_id | Integer | Foreign key → User |
| brand_id | Integer | Optional FK → Brand |
| persona_id | Integer | Optional FK → UserPersona |
| status | String(20) | pending/running/awaiting_approval/completed/failed/cancelled |
| steps_completed | Integer | Default: 0 |
| total_steps | Integer | Default: 0 |
| current_step_label | String(200) | Human-readable step name |
| inputs_json | Text | JSON — user inputs |
| outputs_json | Text | JSON — recipe outputs |
| error_message | Text | On failure |
| cost | Float | Actual cost |
| retail_cost | Float | Retail cost |
| model_used | String(100) | Model identifier |
| started_at / completed_at | DateTime | Timing |
| created_at | DateTime | Auto-set |

---

## All Routes & Endpoints

### Authentication
| Method | Path | Description |
|--------|------|-------------|
| GET/POST | `/login` | Login page + authenticate |
| GET/POST | `/register` | Registration page + create account |
| GET | `/logout` | Sign out |

### Dashboard
| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Main dashboard (admin or user view) |
| POST | `/admin/toggle-user-view` | Toggle admin ↔ user perspective |
| GET | `/pricing` | Standalone pricing page |

### Brands
| Method | Path | Description |
|--------|------|-------------|
| GET | `/brands/` | List all brands |
| GET | `/brands/new` | New brand form |
| POST | `/brands/` | Create brand |
| GET | `/brands/<id>` | Brand detail/edit |
| POST | `/brands/<id>` | Update brand |
| POST | `/brands/<id>/activate` | Set as active brand |
| DELETE | `/brands/<id>` | Delete brand |
| GET/POST | `/brands/questionnaire` | AI brand questionnaire |
| GET | `/brands/<id>/photos` | Photo library |
| POST | `/brands/<id>/generate-doc` | Auto-generate brand guidelines |

### Campaigns
| Method | Path | Description |
|--------|------|-------------|
| GET | `/campaigns/` | List campaigns |
| GET | `/campaigns/new` | New campaign form |
| POST | `/campaigns/` | Create campaign (AI plans all 30 days) |
| GET | `/campaigns/<id>/calendar` | Calendar grid view |
| POST | `/campaigns/<id>/delete` | Delete campaign |

### Posts
| Method | Path | Description |
|--------|------|-------------|
| GET | `/campaigns/<id>/posts/<day>` | Get post editor (HTMX) |
| POST | `/campaigns/<id>/posts/<day>` | Update post (save/approve/reject) |

### Generation
| Method | Path | Description |
|--------|------|-------------|
| POST | `/generate/post/<id>` | Generate single image (JSON) |
| POST | `/generate/campaign/<id>/day/<day>` | Generate for day (HTMX) |
| POST | `/generate/campaign/<id>` | Bulk generate all draft posts |
| GET | `/generate/status/<id>` | Poll generation status (HTMX) |

### Export
| Method | Path | Description |
|--------|------|-------------|
| GET | `/export/campaigns/<id>` | Export preview page |
| POST | `/export/campaigns/<id>` | Download ZIP |

### API
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/brands/switch` | Switch active brand |
| POST | `/api/prompt/preview` | Preview prompt for style |
| GET | `/api/campaigns/<id>/stats` | Campaign stats JSON |
| POST | `/api/references/<cid>/upload` | Upload campaign reference |
| GET | `/api/references/<cid>` | List campaign references |
| POST | `/api/references/<id>/delete` | Delete reference |
| POST | `/api/brands/<id>/photos/upload` | Upload brand photo |
| GET | `/api/brands/<id>/photos` | List brand photos |
| POST | `/api/photos/<id>/delete` | Delete photo |
| POST | `/api/agent/suggest-captions/<pid>` | AI caption suggestions |
| POST | `/api/agent/enhance-prompt/<pid>` | AI prompt enhancement |
| GET | `/api/models` | Model catalog JSON (supports `?type=image\|video`) |

### Recipes
| Method | Path | Description |
|--------|------|-------------|
| GET | `/recipes/` | Recipe library (card grid, categories) |
| GET | `/recipes/<slug>/` | Recipe detail page |
| GET/POST | `/recipes/<slug>/run/` | Run form + kick off execution |
| GET | `/recipes/run/<id>/status` | Run status page |
| POST | `/recipes/run/<id>/approve` | Approve script → launch Phase 2 |
| GET | `/recipes/run/<id>/status.json` | Run progress JSON |
| GET | `/recipes/history/` | Past runs table |

### Output Files
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/outputs/<filename>` | Serve generated files (images, videos) |

### Personas
| Method | Path | Description |
|--------|------|-------------|
| GET | `/personas/` | List personas |
| GET/POST | `/personas/create` | Creation wizard |
| GET/POST | `/personas/<id>/edit` | Edit persona |
| POST | `/personas/<id>/set-default` | Set default persona |
| POST | `/personas/<id>/delete` | Delete persona |

---

## All Templates

| # | Template | Purpose |
|---|----------|---------|
| 1 | `base.html` | Sidebar layout, nav, flash messages, HTMX progress bar |
| 2 | `auth/login.html` | Login form (standalone, no sidebar) |
| 3 | `auth/register.html` | Registration form (standalone) |
| 4 | `dashboard/index.html` | User dashboard — personal stats |
| 5 | `dashboard/admin.html` | Admin dashboard — platform stats, revenue, profit |
| 6 | `brands/list.html` | Brand cards grid |
| 7 | `brands/new.html` | Create brand form |
| 8 | `brands/detail.html` | Edit brand + sidebar info |
| 9 | `brands/questionnaire.html` | AI brand onboarding (multi-step) |
| 10 | `brands/photo_library.html` | Upload/manage brand photos |
| 11 | `campaigns/list.html` | Campaign cards with status badges |
| 12 | `campaigns/new.html` | Create campaign + cost estimator |
| 13 | `campaigns/calendar.html` | 30-day calendar grid + editor panel |
| 14 | `campaigns/export.html` | Export preview + download |
| 15 | `components/post_editor.html` | HTMX partial — edit post in side panel |
| 16 | `components/post_card.html` | HTMX partial — calendar grid card |
| 17 | `components/style_picker.html` | HTMX partial — 6 style preset cards |
| 18 | `components/caption_suggestions.html` | HTMX partial — AI caption variants |
| 19 | `components/prompt_enhanced.html` | HTMX partial — AI-enhanced prompt |
| 20 | `errors/404.html` | Page not found |
| 21 | `errors/500.html` | Server error |
| 22 | `errors/429.html` | Too many requests |
| 23 | `dashboard/pricing.html` | Standalone pricing page |
| 24 | `components/model_picker.html` | Reusable AI model picker widget |
| 25 | `recipes/library.html` | Workflow recipe card grid |
| 26 | `recipes/detail.html` | Recipe detail + how-to-use |
| 27 | `recipes/run.html` | Dynamic recipe run form |
| 28 | `recipes/run_status.html` | Run status page (HTMX) |
| 29 | `recipes/_run_progress.html` | Progress bar partial + results |
| 30 | `recipes/history.html` | Past recipe runs table |
| 31 | `personas/index.html` | Persona list |
| 32 | `personas/wizard.html` | Multi-step creation wizard |
| 33 | `personas/edit.html` | Edit persona form |

---

## All Services

### Agent Service (`app/services/agent_service.py`)
AI Creative Director powered by Gemini 2.5 Flash.

| Function | Description |
|----------|-------------|
| `analyze_brand()` | Deep brand analysis from questionnaire + web scraping |
| `plan_campaign()` | Generate captions + scene descriptions for all days |
| `write_captions()` | 3 caption variants (emotional, educational, provocative) |
| `build_smart_prompt()` | AI-enhanced image generation prompt |
| `learn_from_feedback()` | Store approve/reject in AgentMemory |
| `select_photos()` | AI picks most relevant photos from library |

### Prompt Service (`app/services/prompt_service.py`)
Style presets + prompt building.

| Function | Description |
|----------|-------------|
| `build_prompt()` | Route to AI agent or template fallback |
| `build_prompt_template()` | Template-based prompt from style preset |

### Cost Service (`app/services/cost_service.py`)
Dual pricing calculations.

| Function | Description |
|----------|-------------|
| `get_generation_cost()` | Unit cost for model/provider |
| `get_user_cost()` | Total spend for a user |
| `get_campaign_cost()` | Total spend for a campaign |
| `get_brand_cost()` | Total spend for a brand |
| `estimate_campaign_cost()` | Pre-generation estimate |

### Analytics Service (`app/services/analytics_service.py`)
PostHog tracking (optional).

| Function | Description |
|----------|-------------|
| `init_posthog()` | Initialize PostHog client |
| `track()` | Capture events |
| `identify()` | Set user traits |

### Model Service (`app/services/model_service.py`)
AI model catalog and pricing.

| Function | Description |
|----------|-------------|
| `get_model_catalog()` | All models with pricing, providers, icons |
| `get_model_choices()` | Models formatted for template/form consumption |
| `get_model_price()` | Cheapest price for a model/provider |

### Script Service (`app/services/script_service.py`)
AI script writing agent.

| Function | Description |
|----------|-------------|
| `write_script()` | Generate script in user's voice |
| `research_topic()` | Research topic for script context |
| `research_and_write()` | Research then write (combined) |
| `rewrite_script()` | Rewrite existing script in user's voice |
| `script_to_scenes()` | Decompose script into video scenes |
| `get_script_types()` | List all script type definitions |

### Security Module (`app/security.py`)
Centralised security utilities.

| Component | Description |
|-----------|-------------|
| `register_security_headers()` | HTTP security headers middleware (CSP, HSTS, session cookies) |
| `_RateLimiter` | In-memory token bucket rate limiter |
| `rate_limit()` | Decorator for route rate limiting |
| `safe_int()` | Safe integer parsing from form data |
| `is_safe_url()` | Open redirect prevention (A01) |
| `safe_redirect()` | Safe redirect with fallback (A01) |
| `validate_password()` | Password complexity validation (A07) |
| `validate_email()` | Email format validation (A07) |

---

## All AI Providers

### Google AI Studio (`tools/providers/google.py`)
| Model | API Model | Type | Sync |
|-------|-----------|------|------|
| nano-banana | gemini-2.5-flash-image | Image | Yes |
| nano-banana-pro | gemini-3-pro-image-preview | Image | Yes |
| veo-3.1 | veo-3.1-generate-preview | Video | No |

Features: Inline base64 reference images, auto-upload to Kie.ai for hosting.

### Kie AI (`tools/providers/kie.py`)
| Model | API Model | Type | Sync |
|-------|-----------|------|------|
| nano-banana-pro | — | Image | No |
| kling-3.0 | kling-3.0/video | Video | No |
| sora-2-pro | sora-2-pro-image-to-video | Video | No |

Features: Async submit/poll, reference URLs, parallel task polling.

### Higgsfield AI (`tools/providers/higgsfield.py`)
| Model | Type | Sync |
|-------|------|------|
| nano-banana | Image | No |
| nano-banana-pro | Image | No |

Features: Key ID:SECRET auth, async polling, custom dimension mapping.

### WaveSpeed AI (`tools/providers/wavespeed.py`)
| Model | API Model | Type | Sync |
|-------|-----------|------|------|
| gpt-image-1.5 | openai/gpt-image-1.5/edit | Image | No |
| kling-3.0 | — | Video | No |
| sora-2 | — | Video | No |
| sora-2-pro | — | Video | No |

Features: Dynamic polling URLs, quality/size parameter mapping.

---

## Cost Configuration

### Retail Costs (shown to users)

| Model | Google | Kie | Higgsfield | WaveSpeed |
|-------|--------|-----|------------|-----------|
| nano-banana | $0.04 | — | $0.04 | — |
| nano-banana-pro | $0.13 | $0.09 | $0.13 | — |
| gpt-image-1.5 | — | — | — | $0.07 |
| veo-3.1 | $0.50 | — | — | — |
| kling-3.0 | — | $0.30 | — | $0.30 |
| sora-2-pro | — | $0.30 | — | $0.30 |

### Actual Costs (operator pays)

| Provider | Actual Cost | Notes |
|----------|-------------|-------|
| Google AI Studio | $0.00 | Free tier |
| Higgsfield | $0.00 | Unlimited plan |
| Kie AI | Same as retail | Pay-per-use |
| WaveSpeed | Same as retail | Pay-per-use |

### Profit Tracking
- Revenue = sum of all `Generation.retail_cost` (successful only)
- Actual Cost = sum of all `Generation.cost` (successful only)
- Profit = Revenue - Actual Cost
- Margin = (Profit / Revenue) × 100%

---

## Design System

### Color Palette (Current — Light/Dark Theme)
| Token | Light | Dark | Usage |
|-------|-------|------|-------|
| Page background | `bg-gray-50` | `bg-[#0F0F0F]` | Body |
| Sidebar | `bg-white` | `bg-[#1A1A1A]` | Fixed left sidebar |
| Card surface | `bg-white` | `bg-[#1E1E1E]` | All cards, panels |
| Card border | `border-[#26A0D8]/20` | `border-[#26A0D8]/40` | Borders, dividers |
| Input fields | `bg-white` | `bg-[#141414]` | Form inputs |
| Primary accent | `#F18523` | Same | Buttons, links, active nav |
| Primary hover | `#D97218` | Same | Button hover states |
| Secondary accent | `#26A0D8` | Same | Borders, dividers, subtle accents |
| Headings | `text-gray-900` | `text-white` | Page titles |
| Body text | `text-gray-700` | `text-gray-300` | Regular text |
| Muted text | `text-gray-500` | `text-gray-400` | Secondary info |
| Green | `#10B981` | Same | Success, free tier, approve |
| Yellow | `#F59E0B` | Same | Warning, generating |
| Red | `#EF4444` | Same | Error, reject, failed |

### Layout Spec
- Sidebar width: 256px (`w-64`)
- Mobile breakpoint: 1024px (`lg:`)
- Mobile: Off-canvas sidebar + hamburger toggle + overlay
- Content area: `lg:ml-64 min-h-screen`
- Max content width: `max-w-7xl mx-auto`
- Dark mode toggle in sidebar footer (sun/moon icon)
- Dark mode saved to `localStorage` key `vb-dark-mode`

### Component Patterns (Light / Dark)
```
Card:       bg-white dark:bg-[#1E1E1E] border border-[#26A0D8]/20 dark:border-[#26A0D8]/40 rounded-xl p-5
Button:     bg-[#F18523] hover:bg-[#D97218] text-white rounded-lg
Input:      bg-white dark:bg-[#141414] border border-[#26A0D8]/20 dark:border-[#26A0D8]/40 rounded-lg
Badge:      bg-gray-100 dark:bg-[#141414] text-gray-600 dark:text-gray-300 rounded text-xs
Active nav: border-l-[3px] border-[#F18523] bg-[#F18523]/8
```

---

## Configuration & Environment

### Flask Config
| Setting | Value |
|---------|-------|
| Database | `videobuds.db` (SQLite, project root) |
| Secret Key | `SECRET_KEY` env var or `dev-secret-change-in-production` |
| Upload Limit | 16 MB |
| Upload Folder | `app/static/uploads/` |
| Generated Folder | `app/static/generated/` |
| Debug Mode | True (development) |
| Port | 8080 |

### Environment Variables (`references/.env`)
| Variable | Provider |
|----------|----------|
| `GOOGLE_API_KEY` | Google AI Studio |
| `KIE_API_KEY` | Kie AI |
| `HIGGSFIELD_API_KEY_ID` | Higgsfield (Key ID) |
| `HIGGSFIELD_API_KEY_SECRET` | Higgsfield (Secret) |
| `WAVESPEED_API_KEY` | WaveSpeed AI |
| `AIRTABLE_API_KEY` | Airtable |
| `AIRTABLE_BASE_ID` | Airtable |
| `POSTHOG_API_KEY` | PostHog Analytics |
| `POSTHOG_HOST` | PostHog Host |

---

## Auto-Seeded Accounts

Created automatically on first startup (when `User.query.count() == 0`):

| Account | Email | Password | Role |
|---------|-------|----------|------|
| Admin | `admin@videobuds.com` | `admin` | `is_admin=True` |
| Test User | `user@videobuds.com` | `user` | `is_admin=False` |

Both accounts are also seeded with:
- **Sample Brand** — "Sample Brand" with tagline, target audience, and content pillars
- **Default Persona** — "Default Persona" with professional tone, conversational voice, and general industry

---

## Master Plan (Future)

From `/Users/a16094/.claude/plans/serialized-knitting-quail.md`:

### Phase 1 — Video Studio Module
Three video creation flows:

1. **UGC Ad Videos**: Product photo + dialogue → 3 scene prompts → reference images → videos via Veo 3.1
2. **Personal Brand / Talking Head**: Avatar + script → Gemini TTS → Higgsfield Speak v2 → talking head
3. **AI Scene Videos**: Concept → 3 scene prompts → 3 clips via Veo 3.1 → composed video

New models: `VideoProject`, `VideoClip`
New routes: `/studio/*`
New blueprint: `video_bp`

### Phase 2 — Content Repurposer + Social Publisher
- Longform → clips (Klap API)
- Horizontal → vertical (Luma Labs)
- Social scheduling via Blotato MCP (TikTok, Instagram, YouTube, LinkedIn)
- Viral Clone Factory (template library)

---

## Bug Fixes & Resolutions

### SQLite Readonly Database Error
- **Problem:** Database at `/tmp/scalebuds.db` had sandbox permission restrictions
- **Fix:** Moved to `BASE_DIR / 'scalebuds.db'` in project directory

### User Had to Sign Up Every Time
- **Problem:** Database kept getting deleted during development
- **Fix:** Auto-seed admin + test user in `app/__init__.py` when `User.query.count() == 0`

### Higgsfield Auth Format Wrong
- **Problem:** Initially used `Bearer` token, but Higgsfield uses `Key KEY_ID:KEY_SECRET`
- **Fix:** Updated `_headers()` in higgsfield.py, split into `HIGGSFIELD_API_KEY_ID` and `HIGGSFIELD_API_KEY_SECRET`

### Old Color Patterns in Templates
- **Problem:** After design overhaul, some brand files still had `hover:bg-[#0055DD]` (old blue hover)
- **Fix:** Global find-and-replace across all 4 affected brand templates

### Video Generation Local Path Issue (R38)
- **Problem:** Image generation returned local file paths, but `generate_ugc_video` only accepted `image_url`
- **Fix:** Updated `tools/create_video.py` to accept `image_path` and auto-detect local paths passed as `image_url`

### Progress Callback App Context Conflict (R38)
- **Problem:** `_make_progress_callback` created a nested `app.app_context()` conflicting with the thread's existing context
- **Fix:** Simplified callback to run directly within `_execute_recipe`'s context (no nested context creation)

### Recipe File Upload Missing Extension Validation
- **Problem:** Recipe file uploads didn't validate file extensions
- **Fix:** Added `ALLOWED_UPLOAD_EXT` validation check in `app/routes/recipes.py` POST handler

### Off-Brand Video Content (Phase 19)
- **Problem:** Ad Video Maker generated videos about skincare when given sunglasses — AI never "saw" the product image
- **Root Cause:** Text-only Gemini call; image was uploaded but only described by filename, not visually analysed
- **Fix:** Implemented multimodal `_call_gemini_with_image()` in `agent_service.py` — AI now sees the actual product photo. Added product-anchored prompts that inject the vision analysis into scene-writing prompts.

### KIE_API_KEY Required for Video Download
- **Problem:** Video generation failed with "KIE_API_KEY is required" when the key wasn't set
- **Fix:** Added local fallback in `tools/providers/google.py` — saves video to `references/outputs/` and returns `/api/outputs/<filename>` URL when KIE_API_KEY is missing

### Veo RAI Filter Blocking Content
- **Problem:** "No generated samples in Veo response" — Veo's safety filters blocked content with people
- **Fix:** Added `personGeneration: "allow_adult"` to Veo API requests. Enhanced error messages with RAI filter detection and debug JSON dumps.

### 404 for Generated Video Downloads
- **Problem:** Generated videos returned absolute file paths, resulting in 404 when accessed in browser
- **Fix:** Created `/api/outputs/<filename>` route in `app/routes/api.py` to serve files from `references/outputs/`. Updated `google.py` to return web-accessible URLs.

### Missing Analysis & Script Display
- **Problem:** Users couldn't see the AI's product analysis or generated scenes in the run output
- **Fix:** Updated `ad_video_maker.py` to include analysis text and scene data in outputs. Enhanced `_run_progress.html` to display text, images, videos, and JSON outputs intelligently.

### Stale URLs in Existing Recipe Runs
- **Problem:** Previous recipe runs stored absolute file paths in `outputs_json`, causing broken links
- **Fix:** Ran data migration to convert paths to web-accessible `/api/outputs/<filename>` format

### Raw Markdown Text in UI (Phase 20)
- **Problem:** AI-generated text displayed raw markdown (`*`, `**`, `-`) in recipe run outputs and brand detail pages
- **Fix:** Applied `| simple_md | safe` Jinja filter to all text output areas; enhanced `simple_md` to handle `*` list markers

### Video Gen Failed on `/api/outputs/` Paths (Phase 20)
- **Problem:** `generate_ugc_video` could not use locally-served images (`/api/outputs/filename.jpg`) as input
- **Fix:** Added path resolution in `tools/create_video.py` to map `/api/outputs/<filename>` → local file path

### Missing CSRF Token on Script Approval Form (Phase 20)
- **Problem:** The "Approve & Generate Videos" form in `_run_progress.html` lacked CSRF protection
- **Fix:** Added hidden `csrf_token` input field to the approval form

### SQLite Readonly Database Error (Phase 20)
- **Problem:** `OperationalError: attempt to write a readonly database` caused by macOS extended attributes (`com.apple.provenance`) on `videobuds.db`
- **Fix:** Deleted old database file; Flask app recreates fresh DB on startup with correct permissions

---

## File Tree (Key Files)

```
r57-template-community/
├── run.py                          # Flask entry point (port 8080)
├── videobuds.db                    # SQLite database (auto-created)
├── .gitignore                      # Protects .env, .db, uploads
├── VIDEOBUDS.md                    # Project documentation
├── CHANGELOG.md                    # This file
├── references/.env                 # API keys (gitignored)
│
├── app/
│   ├── __init__.py                 # App factory + auto-seed + security + brand/persona seed
│   ├── filters.py                  # Jinja2 filters (simple_md, fromjson)
│   ├── config.py                   # DB path, upload limits, PostHog, recipe timeout
│   ├── extensions.py               # SQLAlchemy + Flask-Login
│   ├── security.py                 # Security headers, rate limiter, safe_int
│   │
│   ├── models/
│   │   ├── __init__.py             # Imports all models
│   │   ├── user.py                 # User (auth + admin + relationships)
│   │   ├── brand.py                # Brand identity
│   │   ├── campaign.py             # 30-day campaigns
│   │   ├── post.py                 # Daily posts (+ model/provider)
│   │   ├── generation.py           # Image generation cost tracking
│   │   ├── questionnaire.py        # Brand questionnaire answers
│   │   ├── reference_image.py      # Photo library
│   │   ├── agent_memory.py         # AI long-term memory
│   │   ├── user_persona.py         # Brand voice profiles
│   │   ├── recipe.py               # Recipe catalog entries
│   │   └── recipe_run.py           # Recipe execution tracking
│   │
│   ├── routes/
│   │   ├── __init__.py             # Blueprint registration
│   │   ├── auth.py                 # Login/register (rate-limited)
│   │   ├── dashboard.py            # Admin + user dashboards + pricing
│   │   ├── brands.py               # Brand CRUD + questionnaire
│   │   ├── campaigns.py            # Campaign CRUD + calendar
│   │   ├── posts.py                # Post editor (+ model context)
│   │   ├── generate.py             # Image generation (+ model selection)
│   │   ├── export.py               # ZIP export
│   │   ├── api.py                  # JSON/HTMX endpoints + /api/models
│   │   ├── recipes.py              # Workflow recipes (library/run/history)
│   │   └── personas.py             # AI persona CRUD + wizard
│   │
│   ├── recipes/
│   │   ├── __init__.py             # Recipe registry (auto-discovers)
│   │   ├── base.py                 # BaseRecipe ABC + InputField
│   │   ├── ad_video_maker.py       # R38 — fully wired ✅
│   │   └── (12 more recipe files)  # Defined, execute() placeholder
│   │
│   ├── services/
│   │   ├── agent_service.py        # AI Creative Director (Gemini)
│   │   ├── prompt_service.py       # Style presets + prompt building
│   │   ├── cost_service.py         # Dual pricing calculations
│   │   ├── analytics_service.py    # PostHog tracking
│   │   ├── model_service.py        # Model catalog + pricing
│   │   └── script_service.py       # Script AI agent (research + write)
│   │
│   ├── templates/
│   │   ├── base.html               # Sidebar + dark mode + PostHog
│   │   ├── auth/                   # login.html, register.html
│   │   ├── dashboard/              # index, admin, pricing
│   │   ├── brands/                 # list, new, detail, questionnaire, photo_library
│   │   ├── campaigns/              # list, new, calendar, export
│   │   ├── components/             # post_editor, post_card, model_picker, etc.
│   │   ├── recipes/                # library, detail, run, status, progress, history
│   │   ├── personas/               # index, wizard, edit
│   │   └── errors/                 # 404, 429, 500
│   │
│   └── static/
│       ├── css/custom.css          # Light/dark theme custom styles
│       ├── js/                     # calendar.js, generation.js
│       ├── uploads/                # User uploads (gitignored)
│       └── generated/              # AI-generated images (gitignored)
│
├── tests/
│   ├── test_filters.py            # 23 tests — Jinja2 filter unit tests
│   ├── test_recipe_timeout.py     # 7 tests — Stale run reaper + config
│   ├── test_recipe_active.py      # 12 tests — is_active filtering
│   ├── test_gap_fixes.py          # 13 tests — Phase 29 gap fix tests
│   └── test_owasp.py             # 44 tests — OWASP Top 10 security tests
│
└── tools/
    ├── __init__.py                 # Package init
    ├── config.py                   # API keys, costs, model registry
    ├── create_video.py             # Video generation (local path support)
    ├── create_image.py             # Image generation orchestrator
    ├── analyze_video.py            # Reference video analysis (Gemini)
    ├── upload_to_kie.py            # File upload to Kie hosting
    ├── airtable.py                 # Airtable integration
    ├── youtube_to_linkedin.py      # YouTube→LinkedIn automation (Modal)
    ├── utils.py                    # Shared helpers
    └── providers/
        ├── __init__.py             # Provider routing
        ├── google.py               # Google AI Studio (Veo + Nano Banana)
        ├── kie.py                  # Kie AI (Kling, Sora, Nano Banana)
        ├── higgsfield.py           # Higgsfield (Nano Banana)
        └── wavespeed.py            # WaveSpeed (Kling, Sora, GPT Image)
```

---

### AI News Digest Recipe Wired (Phase 21)
- **Recipe:** `news_digest.py` — fully implemented with Gemini 2.5 Flash
- **Pipeline:** Research trending stories → Rank by relevance → Summarise in chosen tone → Format as email / blog / LinkedIn article
- **Inputs:** Topics (text), story count (3/5/10), output format (email/blog/linkedin), tone (professional/casual/witty)
- **Outputs:** Formatted digest (markdown) + raw research data
- **Cost:** Free (Gemini 2.5 Flash)

---

## Phase 22 — Bug Fixes, Missing Features & Hardening

### What was built

#### Security Hardening
- **Custom CSRF Protection** — Implemented session-based CSRF with `generate_csrf_token()` (Jinja global) and `validate_csrf_token()` (before_request hook). All POST forms now have real CSRF token generation and server-side validation. Replaced all `csrf_token() if csrf_token is defined else ''` with `{{ csrf_token() }}`.
- **`.gitignore` created** — Excludes `videobuds.db`, `.env`, `__pycache__/`, `references/outputs/`, `.venv/`, `.DS_Store`.

#### Missing Features Implemented
- **`requirements.txt`** — Complete dependency list: Flask 3.1, Flask-SQLAlchemy 3.1.1, Flask-Login 0.6.3, python-dotenv, requests, posthog, werkzeug.
- **Account Settings** (`/account`) — Users can change display name, email, and password. Template: `auth/account.html`.
- **Admin User Management** (`/admin/users`) — Admin can list all users, toggle active/deactivate, and delete users. Template: `admin_users.html`. Self-protection prevents admin from deactivating or deleting own account.
- **`User.is_active` column** — Added Boolean field (default=True). Deactivated users see "account has been deactivated" on login attempt. Required SQLite `ALTER TABLE` migration for existing databases.
- **Async Bulk Campaign Generation** — `generate_campaign` route now launches a background thread via `threading.Thread`. Campaign status set to `generating` during processing. Each post generated sequentially within the thread. Campaign status updated to `review` or `draft` upon completion.
- **Pagination** — Brands list (`/brands/`) and Campaigns list (`/campaigns/`) now paginated at 12 items per page. Created reusable `_pagination.html` component in `components/` directory. Shows page numbers, prev/next buttons, and item count.

#### Bug Fixes
- **Stub Recipes** — All 11 unimplemented recipe `execute()` methods now return a user-friendly "Coming Soon" message instead of raising `NotImplementedError`.
- **Campaign Calendar URL** — Verified `url_for('campaigns.calendar', campaign_id=...)` matches route `/campaigns/<id>/calendar` ✓
- **Export Route Prefix** — Verified `url_for('export.preview', campaign_id=...)` uses correct `/export/campaigns/<id>` prefix ✓
- **Post Ownership** — Verified `generate_single` route checks campaign ownership after fetching post ✓
- **ReferenceImage Ownership** — Verified `delete_reference` and `delete_brand_photo` check parent campaign/brand ownership ✓
- **Brands `active_brand` context** — Fixed `list_brands` route to pass `active_brand` to template (was missing, causing template reference to undefined variable).

#### Documentation
- **VIDEOBUDS.md fully updated** — All missing routes (30+ routes across 9 blueprints), `BrandQuestionnaire` model, `prompt_service.py`, `setup_airtable.py`, Services Documentation section, and comprehensive Continuity Notes.
- **CHANGELOG.md** — Phase 22 section added with all changes.

---

## Phase 23 — Photo to Ad Recipe Wiring

### What was built

- **Photo to Ad recipe fully wired** (`app/recipes/photo_to_ad.py`) — No longer a stub. Now a two-phase recipe following the same Compound Engineering pattern as Ad Video Maker:
  - **Phase 1 (Script)**: Multimodal Gemini vision analyses the uploaded product photo, then writes ad concepts (scene descriptions + ad copy) anchored to the actual product. Returns `phase: "script"` → run pauses at `awaiting_approval`.
  - **Phase 2 (Production)**: Generates ad images using Nano Banana Pro (free). Optionally generates short videos with Veo 3.1 based on user's `output_type` selection (images only / videos only / both).
- **Structured asset organisation** — All generated assets saved to `references/outputs/run_<id>/` with metadata.json.
- **Full input support** — Respects all 4 user inputs: `product_photo` (file), `tagline` (optional text overlay), `output_type` (images/videos/both), `variations` (1/3/5).
- **Follows SOLID pattern** — Phase dispatcher in `execute()`, separate `_execute_script()` and `_execute_production()` methods, reusable asset helpers.

### Files changed
- `app/recipes/photo_to_ad.py` — Replaced stub with ~350 lines of working recipe logic.
- `CHANGELOG.md` — Phase 23 added.

---

## Phase 24 — Video Quality & Playback Fixes

### What was fixed

- **Video duration snap** — Veo 3.1 only supports 4, 6, or 8 second durations. Recipes passed `duration="5"` which snapped to 4s (too short for ads). Changed to `duration="8"` in both `ad_video_maker.py` and `photo_to_ad.py`. Updated `video_creator.py` dropdown options from 3/5/8 to 4/6/8 to match valid Veo values.
- **Moov atom at end of file** — Downloaded MP4 files had the `moov` atom (playback metadata) at the end, preventing progressive playback and causing glitches. Added `_faststart()` function in `tools/providers/google.py` that runs `ffmpeg -movflags +faststart` after every video download to move the moov atom to the front. Gracefully falls back if ffmpeg is not installed.
- **Missing `playsinline` attribute** — Added `playsinline` to the `<video>` tag in `app/templates/recipes/_run_progress.html` so videos play inline on iOS Safari instead of going fullscreen.

### Files changed

- `app/recipes/ad_video_maker.py` — `duration="5"` → `"8"`
- `app/recipes/photo_to_ad.py` — `duration="5"` → `"8"`
- `app/recipes/video_creator.py` — Duration dropdown options updated to 4/6/8
- `tools/providers/google.py` — New `_faststart()` function; called after every video download
- `app/templates/recipes/_run_progress.html` — Added `playsinline` to `<video>` tag
- `CHANGELOG.md` — Phase 24 added

---

## Phase 25 — Photo Library Upload Fix

### What was fixed

- **CSRF bypass for AJAX uploads** — Photo library uploads and reference image deletions silently failed because `fetch()` POST requests lacked the `X-Requested-With: XMLHttpRequest` header. The custom CSRF middleware (`app/security.py`) skips CSRF validation for AJAX requests (identified by this header), so its absence caused every upload/delete to be rejected.
- **Added error feedback** — `uploadFiles()` and `deletePhoto()` now show `alert()` messages on failure so users know when something goes wrong instead of silent failure.
- **Post editor fix** — Same `X-Requested-With` header added to the reference image delete `fetch()` call in the post editor component.

### Files changed

- `app/templates/brands/photo_library.html` — Added `headers: { 'X-Requested-With': 'XMLHttpRequest' }` to `uploadFiles()` and `deletePhoto()` fetch calls; added error handling
- `app/templates/components/post_editor.html` — Added `X-Requested-With` header to reference image delete fetch call

---

## Phase 26 — Brand/Persona Gap Analysis & Integration Plan

### What was done

- **Gap analysis** — Identified 5 gaps in how Brands and Personas integrate with the Recipe system:
  1. No Brand/Persona selector in recipe run form (`run.html`)
  2. `BaseRecipe.execute()` never receives Brand or Persona objects
  3. Working recipes (Ad Video Maker, Photo to Ad) ignore brand context in AI prompts
  4. Disconnected UI — Brands and Personas feel separate with no clear link to Recipes
  5. No "knowledge" selection (photo library, brand doc) available during recipe runs
- **Architecture rationale** — Documented why Brand and Persona should remain separate models (distinct entities, many-to-many relationship, modularity, different AI prompt roles)
- **3-phase action plan** with 6 tasks:
  - **Phase A (Wire the Plumbing)**: Add Brand/Persona dropdowns to run form; pass objects to `execute()`; update `BaseRecipe` signature
  - **Phase B (Use the Context)**: Inject brand voice/persona tone into Ad Video Maker and Photo to Ad AI prompts
  - **Phase C (UX Polish)**: Add "Brand Voice" section to brand detail page; auto-inject brand photo library as reference context

### Files changed

- `project-status.md` — New file with full gap analysis, rationale, and action plan

---

## Phase 27 — Brand/Persona Integration Implementation

### Goal

Execute the 3-phase action plan from Phase 26 — wire Brand and Persona objects into the recipe execution pipeline so that AI prompts are informed by the user's brand identity and voice persona.

### What was done

**Phase A — Wire the Plumbing**
- Added Brand and Persona `<select>` dropdowns to `app/templates/recipes/run.html` — both optional, populated from `current_user`'s brands and personas
- Updated `app/routes/recipes.py`:
  - GET handler for `/recipes/<slug>/run/` passes `brands` and `personas` to template
  - POST handler extracts `brand_id` / `persona_id` from form data, stores on `RecipeRun`
  - `_launch_recipe_execution()` and `_execute_recipe()` fetch `Brand` / `UserPersona` from DB and pass them to `recipe.execute()`
  - `approve_script()` handler forwards `brand_id` / `persona_id` from the `RecipeRun` for Phase 2 production
- Updated `app/recipes/base.py` — `execute()` signature now accepts `brand=None, persona=None`

**Phase B — Use the Context**
- `build_brand_context()` static method on `BaseRecipe` — extracts brand name, tagline, target audience, content pillars, never-do, and brand doc into a prompt-injection block
- `build_persona_context()` static method on `BaseRecipe` — extracts persona name, tone, voice style, keywords, avoid words, sample phrases, writing guidelines, and AI summary into a prompt-injection block
- `get_brand_reference_paths()` static method on `BaseRecipe` — queries `ReferenceImage` for a brand's product photos and returns existing local file paths (up to a limit)
- `app/recipes/ad_video_maker.py` — brand/persona context injected into scene-writing prompt; brand product photos auto-added as `reference_paths` in production phase
- `app/recipes/photo_to_ad.py` — brand/persona context injected into concept-writing prompt; brand product photos auto-added as `reference_paths` in production phase

**Phase C — UX Polish**
- Added "Brand Voice" section to `app/templates/brands/detail.html` sidebar — lists all user personas with name, tone, "Default" badge, and link to edit; includes "New Persona" button
- Updated `app/routes/brands.py` `show_brand()` to pass `active_brand` and `personas` to the template

**Phase D — Audit & Gap Fix**
- Audited all 13 recipes and 2 AI services for brand/persona coverage
- Fixed `app/recipes/news_digest.py` — `execute()` now accepts `brand=None, persona=None`; brand voice and persona tone are injected into the formatting prompt so digests read on-brand
- Confirmed `app/services/script_service.py` already fully brand/persona-aware across `write_script()`, `rewrite_script()`, `research_and_write()`, `write_scripts_multi()`
- Noted `app/services/agent_service.py` is brand-aware but does NOT yet accept persona context (future enhancement — currently only used by campaign/brand management routes, not recipe execution)
- 10 placeholder recipes (Coming Soon) have no AI calls — brand/persona integration will be added when they're implemented

### Files changed

- `app/recipes/base.py` — `execute()` signature; `get_brand_reference_paths()`, `build_brand_context()`, `build_persona_context()` helpers
- `app/recipes/ad_video_maker.py` — `execute()`, `_execute_script()`, `_execute_production()` accept and use brand/persona
- `app/recipes/photo_to_ad.py` — `execute()`, `_execute_script()`, `_execute_production()` accept and use brand/persona
- `app/recipes/news_digest.py` — `execute()` updated to accept brand/persona; formatting prompt injects brand voice and persona tone
- `app/routes/recipes.py` — GET/POST handlers, `_execute_recipe`, `_launch_recipe_execution`, `approve_script` updated
- `app/templates/recipes/run.html` — Brand and Persona select dropdowns added
- `app/routes/brands.py` — `show_brand()` passes personas and active_brand
- `app/templates/brands/detail.html` — "Brand Voice" sidebar section added
- `project-status.md` — Updated with implementation status

*Last updated: February 27, 2026 — Phase 27: Brand/Persona Integration Implementation*

---

## Ralph Loop Full Audit

> Performed: 2026-02-27 — Post Phase 27

### Methodology
Compound Engineering with Ralph Loop: **R**esearch → **A**nalyze → **L**earn → **P**lan → **H**ypothesize → Test

### What Was Done

1. **Security Audit** — Reviewed all 9 blueprints, authentication flow, CSRF implementation, rate limiting, security headers, file upload/serving, XSS prevention (via `html.escape()` in `simple_md`), SQL injection (all ORM, no raw SQL), and path traversal protection. **Result: PASS** — one low-risk item (static fallback `SECRET_KEY`).

2. **End-to-End Flow Check** — Verified recipe execution pipeline from GET form → POST with brand/persona → background thread → `execute()` with brand/persona → AI prompt injection → asset generation → DB status update. Two-phase recipes (script approval → production) also verified.

3. **SOLID Principles Review** — Graded B+ overall. Clean model/route/service/recipe separation. Recipe auto-discovery (Open/Closed). Minor concern: `simple_md` filter inline in `__init__.py`.

4. **Gap Analysis** — Identified 2 HIGH, 4 MEDIUM, 3 LOW priority gaps. No CRITICAL issues.

### Gaps Identified

**HIGH:**
- H1: Static `SECRET_KEY` fallback — risky in production
- H2: No input size limits on recipe text fields — potential API cost abuse

**MEDIUM:**
- M1: `agent_service` has no persona support
- M2: `script_to_scenes()` has no persona support
- M3: No error handling on Gemini API failures in recipes
- M4: Background thread crash leaves recipes stuck as "Running…"

**LOW:**
- L1: `simple_md` filter inline in `__init__.py` (should be `app/filters.py`)
- L2: No recipe execution timeout
- L3: 10 placeholder recipes clutter the UI

### Action Plan

| Phase | Items | Effort |
|-------|-------|--------|
| Phase 28A — Security Hardening | H1, H2 | ~45 min |
| Phase 28B — Resilience | M3, M4 | ~1.75 hr |
| Phase 28C — Persona Expansion | M1, M2 | ~1.5 hr |
| Phase 28D — Code Quality | L1, L2, L3 | ~1 hr |

*Full details in `project-status.md` under "Ralph Loop Full Audit".*

---

## Phase 28A — Security Hardening

> Completed: 2026-02-27

### Goal
Fix the two HIGH-priority gaps identified in the Ralph Loop audit.

### What Was Done

**H1: Force SECRET_KEY in Production**
- `ProductionConfig.__init__()` now raises `RuntimeError` if `SECRET_KEY` is the default static value — prevents insecure sessions in production
- `DevelopmentConfig.__init__()` logs a `WARNING` if using the default key — reminds developers during local development
- Added `_DEFAULT_SECRET` constant for clean comparison

**H2: Input Size Limits on Recipe Forms**
- Added `MAX_TEXT_INPUT_LENGTH = 500` and `MAX_TEXTAREA_INPUT_LENGTH = 5000` to `Config` class
- Client-side: `maxlength` attributes on `<input type="text">` and `<textarea>` in `run.html`
- Server-side: Length validation in `app/routes/recipes.py` POST handler — checks each text/textarea field against config limits, returns 400 with user-friendly error
- Bug fix: Error re-renders for file-type validation and required-field validation now also pass `brands` and `personas` to the template (previously missing, which could cause template errors)

### Files Changed
- `app/config.py` — `_DEFAULT_SECRET`, `MAX_TEXT_INPUT_LENGTH`, `MAX_TEXTAREA_INPUT_LENGTH`, `DevelopmentConfig.__init__()`, `ProductionConfig.__init__()`
- `app/routes/recipes.py` — Server-side length validation in POST handler; brands/personas in all error re-renders
- `app/templates/recipes/run.html` — `maxlength` attributes on text and textarea fields

---

## Phase 28B — Resilience Hardening

> Completed: 2026-02-27

### Goal

Fix the two MEDIUM-priority gaps M3 and M4 identified in the Ralph Loop audit: recipe error handling and background thread resilience.

### What Was Done

**M3: Error Handling on Gemini API Failures (News Digest)**
- **Research call** (`_call_gemini` for story research): wrapped in `try/except` that raises a `RuntimeError` with a user-friendly error message including the original exception detail. This propagates up to the thread-level handler which marks the run as `failed`.
- **Format call** (`_call_gemini` for final formatting): wrapped in `try/except` with **graceful degradation** — instead of crashing, returns the raw research data prefixed with a "⚠️ Formatting failed" warning. The run still completes successfully with useful output.
- **JSON parse failure**: `json.JSONDecodeError` handled — falls back to raw text from the research step, so partial results are never lost.

**M4: Background Thread Triple-Fallback**

Refactored `_execute_recipe()` in `app/routes/recipes.py` with three nested error-handling layers:

```
Layer 1 (inner try/except):
  Catches recipe execution errors → sets status="failed",
  saves error_message (truncated to 2000 chars)

Layer 2 (secondary try/except around DB write):
  If DB rollback or error-state write fails → logs exception
  (prevents cascading failures from masking the original error)

Layer 3 (outer try/except — ultimate catch-all):
  Catches anything outside app context (DB unavailable, etc.)
  → logs CRITICAL error. Thread never dies silently.
```

**Stale Run Reaper**
- New `_reap_stale_runs(max_age_minutes=60)` function — queries `RecipeRun` rows stuck in `status='running'` for longer than the configured timeout and marks them as `failed` with a descriptive error message.
- Called **opportunistically** from two places — the recipe library page (`GET /recipes/`) and the history page (`GET /recipes/history/`) — each wrapped in a `try/except` so the reaper never blocks page rendering.
- No background thread or scheduler required — the lightweight query runs on the next page load after a run goes stale.

### Files Changed

- `app/routes/recipes.py` — `_execute_recipe()` triple-fallback refactor; new `_reap_stale_runs()` function; reaper called from `library()` and `history()` routes
- `app/recipes/news_digest.py` — `try/except` on both Gemini API calls (research + format) with user-friendly errors and graceful fallback

---

## Phase 28D — Code Quality

> Completed: 2026-02-27

### L1 — Extract `simple_md` filter

- Moved `simple_md` filter from `app/__init__.py` (inline) to dedicated `app/filters.py`
- Created `register_filters(app)` helper called from `create_app()`
- Removed unused `json` import from `__init__.py`
- Added 23 unit tests (`tests/test_filters.py`): `TestFromjson` (6), `TestSimpleMd` (14), `TestRegisterFilters` (2)
- XSS prevention tested — filter HTML-escapes input before processing Markdown

### L2 — Recipe execution timeout

- Added `RECIPE_TIMEOUT_MINUTES = 30` to `app/config.py` (configurable per environment)
- Updated `_reap_stale_runs()` in `app/routes/recipes.py` to read timeout from `current_app.config`
- Changed type hint from `int | None` to `Optional[int]` for Python 3.9 compatibility
- Added 5 unit tests (`tests/test_recipe_timeout.py`): config default, stale run reaping, fresh run not reaped, custom config, explicit override

### L3 — Hide stub recipes (is_active filter)

- Added `is_active = True` default to `BaseRecipe`
- Set `is_active = False` on 10 stub recipes: clip_factory, image_creator, influencer_content_kit, motion_capture, multi_scene_video, social_scraper, style_cloner, talking_avatar, vertical_reframe, video_creator
- Updated `get_all_recipes()`, `recipe_count()`, `get_recipes_by_category()` to filter inactive by default
- All three accept `include_inactive=True` for admin/debug views
- `get_recipe(slug)` still returns inactive recipes (needed for run history)
- Added 12 unit tests (`tests/test_recipe_active.py`): BaseRecipe defaults, stub detection, active filtering, count, category grouping, slug lookup

### Test suite summary

- **42 total tests** across 3 test files — all passing
- `tests/test_filters.py` — 23 tests
- `tests/test_recipe_timeout.py` — 7 tests (5 stale-run + 2 config)
- `tests/test_recipe_active.py` — 12 tests

---

## Phase 28C — Persona Expansion

> Completed: 2026-02-27

### Goal

Close the two remaining MEDIUM-priority gaps M1 and M2 from the Ralph Loop audit: add persona support to agent_service functions and `script_to_scenes()`.

### What Was Done

**M1: Agent Service — Persona Support**

Added `persona=None` keyword parameter to all four public agent_service functions:

| Function | Persona Injection |
|----------|------------------|
| `plan_campaign(brand, campaign, *, persona=None)` | Persona voice context injected into campaign planning prompt so captions and scene descriptions match the persona's tone/vocabulary |
| `write_captions(brand, post, campaign, *, persona=None)` | Persona voice priming block injected with CRITICAL instruction to match tone, vocabulary, and energy |
| `build_smart_prompt(brand, post, campaign, *, persona=None)` | Persona visual style hint injected so image generation prompts align with the creator's vibe |
| `select_photos(brand, post, campaign, *, persona=None)` | Persona personality summary injected to bias photo selection towards the creator's style |

New helper function: `_persona_context(persona)` — builds a voice-priming block from a `UserPersona` instance. Returns empty string when `persona is None` (backward-compatible). Uses `ai_prompt_summary` if available, else assembles from individual fields (tone, voice_style, bio, target_audience, brand_keywords, avoid_words, sample_phrases, writing_guidelines).

**M2: `script_to_scenes()` — Persona Support**

Added `persona_id=None` and `persona=None` keyword parameters:

```python
def script_to_scenes(
    script, num_scenes=3, aspect_ratio="9:16", *,
    brand_id=None, brand=None,
    persona_id=None, persona=None,  # ← NEW
) -> List[dict]:
```

- Resolves persona from `persona_id` if needed (same pattern as `write_script`)
- Injects persona voice context into the storyboard prompt so visual scene descriptions match the creator's style
- Uses existing `_build_persona_context()` helper from script_service

### Backward Compatibility

All changes are fully backward-compatible:
- `persona=None` is keyword-only, so all existing positional callers continue to work unchanged
- Route-level wiring (campaigns.py, api.py, generate.py) does not yet pass persona — these functions simply receive `None` and skip the persona section in their prompts
- Future enhancement: wire persona through campaign routes when campaigns gain a `persona_id` field

### Files Changed

- `app/services/agent_service.py` — New `_persona_context()` helper; `persona=None` param + prompt injection in `plan_campaign`, `write_captions`, `build_smart_prompt`, `select_photos`
- `app/services/script_service.py` — `persona_id=None` + `persona=None` params and persona context injection in `script_to_scenes()`

---

## Phase 29 — Gap Fixes & E2E Verification

> Completed: 2026-02-27

### Goal

Address user-reported gaps (only 3 recipes visible, video errors hidden, persona/branding not selectable in campaigns, no seed data for new users) through targeted fixes, unit tests, and end-to-end verification.

### Methodology

Compound Engineering with Ralph Loop:
1. **Research** — Reproduced all user-reported issues; audited recipes, templates, routes, and models
2. **Analyze** — Identified 6 discrete gaps (3 P0, 3 P1)
3. **Learn** — Root causes: inactive recipe filtering edge cases, missing UI feedback, incomplete route wiring, no seed data
4. **Plan** — Ordered fixes by priority; each fix paired with unit test
5. **Hypothesize** — Predicted each fix would resolve its gap without regressions
6. **Test** — 13 new unit tests + full E2E verification script

### What Was Done

**FIX 1 (P0): History page recipe_map misses inactive recipes**
- **Problem:** The history page called `get_all_recipes()` (default: `include_inactive=False`), so runs from inactive/stub recipes showed "Unknown" as their recipe name.
- **Fix:** Changed `history()` in `app/routes/recipes.py` to call `get_all_recipes(include_inactive=True)`, ensuring all recipe names — including stubs — display correctly in the run history.

**FIX 2 (P0): Video error not shown in output UI**
- **Problem:** When video generation failed (e.g., Veo RAI filter), the output displayed a media card with a broken `image_url` but no error message — users saw nothing useful.
- **Fix:** Added a yellow warning banner in `app/templates/recipes/_run_progress.html` within the media output block. When `output.value` contains the word "error", it renders a visible `⚠️` banner with the error text above the media element.

**FIX 3 (P0): Inactive recipes accessible via detail URL**
- **Problem:** Users could manually navigate to `/recipes/video-creator/` (an inactive stub) and even attempt to run it.
- **Fix:** Added `if not recipe.is_active: abort(404)` guards to both the `detail(slug)` and `run(slug)` route handlers in `app/routes/recipes.py`. Also added a redundant `is_active` check in `run()` before the existing `db_row.is_enabled` check for defense in depth.

**FIX 4 (P1): Seed sample brand + persona for new users**
- **Problem:** After login, users had no brands or personas available — dropdowns in recipe run forms and campaign forms were empty, breaking the UX.
- **Fix:** Added seed logic to `create_app()` in `app/__init__.py`: if admin or test user has zero brands, creates a "Sample Brand" (with name, tagline, target audience, and content pillars); if they have zero personas, creates a "Default Persona" (with name, tone, voice style, and industry).

**FIX 5 (P1): Wire persona through campaign routes**
- **Problem:** The new campaign form had no persona selector — even though `plan_campaign()` accepted `persona=None`, there was no way for users to select and pass a persona.
- **Fix:**
  - `app/routes/campaigns.py` → `new_campaign()` now fetches `UserPersona.query.filter_by(user_id=current_user.id)` and passes `personas` to the template.
  - `app/routes/campaigns.py` → `create_campaign()` now reads `persona_id` from the form, fetches the `UserPersona` object, and passes it to `plan_campaign()`.
  - `app/templates/campaigns/new.html` → Added a "Persona" dropdown select field (optional) with user personas populated from the route.

**FIX 6 (P1): Sync `is_enabled` DB flag from `is_active` class attr**
- **Problem:** The `Recipe` model has an `is_enabled` column, but it was never synchronized with the `BaseRecipe.is_active` class attribute. A recipe could be `is_active = False` in code but `is_enabled = True` in the database, leading to inconsistent behavior.
- **Fix:** Modified `_ensure_recipe_db_row(recipe_cls)` in `app/routes/recipes.py` to check if `db_row.is_enabled != recipe_cls.is_active` and update + commit if they diverge.

### Unit Tests (13 new)

| Test Class | Tests | What It Verifies |
|------------|:-----:|------------------|
| `TestHistoryRecipeMap` | 1 | `get_all_recipes(include_inactive=True)` returns all recipes including stubs |
| `TestVideoErrorBanner` | 2 | Error banner renders when output.value contains "error"; no banner for clean outputs |
| `TestInactiveRecipeRouteGuard` | 3 | `detail()` and `run()` return 404 for inactive recipes; active recipes return 200 |
| `TestSeedBrandAndPersona` | 2 | Admin and test user both get ≥1 brand and ≥1 persona after app creation |
| `TestCampaignPersonaWiring` | 3 | `UserPersona` imported in campaigns route; `new_campaign` template receives `personas`; template has `persona_id` field |
| `TestEnsureRecipeDbRowSync` | 2 | Sync updates `is_enabled` from `is_active`; idempotent when already synced |

### Full Test Suite — 55 tests, ALL PASS

| File | Tests |
|------|:-----:|
| `tests/test_filters.py` | 23 |
| `tests/test_recipe_timeout.py` | 7 |
| `tests/test_recipe_active.py` | 12 |
| `tests/test_gap_fixes.py` | 13 |
| **Total** | **55** |

### E2E Security & Integrity Verification — ✅ ALL PASS

8-point verification script covering:
1. Recipe count (3 active, 10+ inactive stubs)
2. Active recipes correct (ad-video-maker, photo-to-ad, news-digest)
3. Inactive recipe route guard (`video-creator` is_active=False)
4. Brand + persona seed for admin and test user
5. DB `is_enabled` ↔ `is_active` sync on all recipes
6. CSRF protection enabled, security headers registered
7. All 6 recipe templates present in filesystem
8. Error banner in `_run_progress.html`, persona dropdown in campaign form

### Files Changed

- `app/__init__.py` — Seed "Sample Brand" and "Default Persona" for admin + test user
- `app/routes/recipes.py` — History recipe_map `include_inactive=True`; `detail()` + `run()` inactive guard; `_ensure_recipe_db_row()` sync logic
- `app/routes/campaigns.py` — Fetch + pass personas; read `persona_id` from form; pass persona to `plan_campaign()`
- `app/templates/recipes/_run_progress.html` — Video error warning banner
- `app/templates/campaigns/new.html` — Persona dropdown selector
- `tests/test_gap_fixes.py` — 13 new unit tests

*Last updated: February 27, 2026 — Phase 29: Gap Fixes & E2E Verification*

---

## Phase 30 — OWASP Top 10 Security Hardening

> Completed: 2026-02-27

### Goal

Systematic OWASP Top 10 audit and targeted fixes for the four most applicable vulnerability categories, following compound engineering and Ralph Loop methodology. Every fix paired with unit tests.

### OWASP Categories Addressed

**A01 — Broken Access Control (Open Redirect Prevention)**
- New `is_safe_url(target)` function in `app/security.py` — validates redirect URLs are relative or on the same host; blocks external domains and protocol-relative URLs (`//evil.com`)
- New `safe_redirect(target)` function — wraps `is_safe_url()`, returns the target if safe or falls back to dashboard
- Applied to:
  - `app/routes/auth.py` → `login()` — validates `next_page` from `request.args.get("next")`
  - `app/routes/brands.py` → `activate_brand()` — validates `request.referrer` before redirect
  - `app/routes/api.py` → `switch_brand()` — validates `request.referrer` before redirect

**A05 — Security Misconfiguration (Headers & Session Cookies)**
- Added `Content-Security-Policy` (CSP) header with directive for `default-src`, `script-src`, `style-src`, `img-src`, `font-src`, and `connect-src`
- Added `Strict-Transport-Security` (HSTS) header with `max-age=31536000; includeSubDomains`
- Session cookie hardening:
  - `SESSION_COOKIE_HTTPONLY = True` — prevents JavaScript access to session cookies (XSS mitigation)
  - `SESSION_COOKIE_SAMESITE = "Lax"` — prevents CSRF via cross-origin requests
  - `SESSION_COOKIE_SECURE = True` (production only) — cookies only sent over HTTPS
  - Uses direct assignment instead of `setdefault()` to override Flask's pre-populated `None` defaults

**A07 — Authentication Failures (Input Validation)**
- New `validate_password(password)` function in `app/security.py`:
  - Returns `(is_valid: bool, error_message: str)` tuple
  - Enforces: ≥8 characters, ≥1 uppercase, ≥1 lowercase, ≥1 digit, ≥1 special character
- New `validate_email(email)` function in `app/security.py`:
  - Returns `(is_valid: bool, error_message: str)` tuple
  - Validates format via regex, max length ≤254, domain presence
- Applied to:
  - `app/routes/auth.py` → `register()` — validates email and password before account creation
  - `app/routes/auth.py` → `account()` — validates new password on password change

**A09 — Security Logging & Monitoring Failures**
- Added `logging.getLogger("security")` for dedicated security event logging
- Events logged:
  - `INFO` — Successful login (email + IP address)
  - `WARNING` — Failed login attempt: wrong password (email + IP)
  - `WARNING` — Failed login attempt: unknown user (email + IP)
  - `INFO` — New user registration (email + IP)
  - `WARNING` — Admin toggle user active/inactive (admin email + target user ID)
  - `WARNING` — Admin delete user (admin email + target user ID)
  - `INFO` — User logout (email)

### Unit Tests — 44 Tests, ALL PASS

| Test Class | Tests | OWASP | What It Verifies |
|------------|:-----:|:-----:|------------------|
| `TestIsSafeUrl` | 6 | A01 | Relative URLs safe, external domains blocked, None/empty handled |
| `TestSafeRedirect` | 3 | A01 | Safe URL passthrough, evil URL fallback, None handling |
| `TestValidatePassword` | 7 | A07 | All 5 complexity rules enforced, valid password accepted, empty rejected |
| `TestValidateEmail` | 6 | A07 | Valid format accepted, missing @/domain rejected, length limit, whitespace |
| `TestCSPHeader` | 3 | A05 | CSP header present on responses, script-src and style-src directives |
| `TestHSTSHeader` | 2 | A05 | HSTS header present, contains max-age directive |
| `TestSessionCookieConfig` | 3 | A05 | HttpOnly=True, SameSite=Lax, Secure flag behavior |
| `TestSecurityEventLogging` | 6 | A09 | All 6 security events logged at correct level with correct content |
| `TestLoginOpenRedirect` | 4 | A01 | Login blocks external `?next=` redirect, allows safe paths |
| `TestRegisterValidation` | 5 | A07 | Registration rejects weak passwords and invalid email formats |
| `TestBrandActivateRedirect` | 3 | A01 | Brand activate blocks open redirect via forged referrer |
| `TestBrandSwitchRedirect` | 2 | A01 | API brand switch blocks open redirect via forged referrer |

### Full Test Suite — 99 Tests, ALL PASS

| File | Tests |
|------|:-----:|
| `tests/test_filters.py` | 23 |
| `tests/test_recipe_timeout.py` | 7 |
| `tests/test_recipe_active.py` | 12 |
| `tests/test_gap_fixes.py` | 13 |
| `tests/test_owasp.py` | 44 |
| **Total** | **99** |

### Files Changed

- `app/security.py` — `is_safe_url()`, `safe_redirect()`, `validate_password()`, `validate_email()`; CSP header, HSTS header, session cookie hardening via direct assignment
- `app/routes/auth.py` — Open redirect prevention on login; password/email validation on register; password validation on account; security event logging on login/register/logout
- `app/routes/brands.py` — `is_safe_url()` on `activate_brand()` referrer redirect
- `app/routes/api.py` — `is_safe_url()` on `switch_brand()` referrer redirect
- `app/routes/dashboard.py` — Security event logging on `toggle_user()` and `delete_user()` admin actions
- `tests/test_owasp.py` — 44 new unit tests

---

## Phase 31 — Ad Video Maker Bug Fixes & UX Hardening

**Date**: February 27, 2026
**Methodology**: Ralph Loop — Research → Analyze → Learn → Plan → Hypothesize → Test
**Goal**: Fix three user-reported bugs: infinite page refresh after video generation, video not playing fully, and missing brand/persona selection options.

### User-Reported Bugs

1. **"Page keeps refreshing and the video generated does not play full"** — After the Ad Video Maker recipe completed, the page kept refreshing in an infinite loop, and the generated video would reset each time, preventing full playback.
2. **"I don't see an option to add my branding or brand or persona"** — Brand and persona selectors were hidden behind a collapsible section that users couldn't find.

### Root Cause Analysis

| Bug | Root Cause | OWASP/SOLID Impact |
|-----|-----------|-------------------|
| Infinite refresh | HTMX `hx-trigger="every 2s"` polling returned HTTP 200 for ALL statuses, including terminal ones. HTMX kept polling and replacing the DOM forever. | A05 (misconfiguration) |
| Video won't play | Two compounding causes: (1) DOM replacement by HTMX resets `<video>` element mid-playback; (2) `preload="metadata"` only loads headers, not content | UX defect |
| Hidden selectors | Brand/persona section used `<div hidden>` with a JavaScript toggle button. Users didn't discover the toggle. | UX defect, violates "visibility of system status" heuristic |

### Fixes Applied

**G1 — HTMX Polling Stop (HTTP 286)**
- File: `app/routes/recipes.py` → `run_status()` route
- When `run_row.status` is in `("completed", "failed", "cancelled", "awaiting_approval")`, return `(html, 286)` instead of `(html, 200)`
- HTTP 286 is the HTMX standard for "stop polling" — documented at htmx.org
- Non-terminal statuses (`running`, `pending`) continue returning 200

**G2 — Video Full Playback**
- File: `app/templates/recipes/_run_progress.html`
- Changed `preload="metadata"` to `preload="auto"` on `<video>` elements
- Combined with G1 fix (no more DOM replacement), videos now play uninterrupted

**G3 — Brand/Persona Always Visible**
- File: `app/templates/recipes/run.html`
- Removed `hidden` attribute and toggle button from the brand/persona section
- Section is now always visible with a clear heading: "Brand & Persona — enriches AI output with your brand voice & style"
- Fixed `url_for` for persona creation link: changed from `personas.list_personas` to `personas.index`
- Both dropdowns show all user's brands/personas with "Create" links when lists are empty

### Test Infrastructure Improvements

**`app/config.py` — TestingConfig Enhancement**
- Added `SQLALCHEMY_ENGINE_OPTIONS = {"connect_args": {"check_same_thread": False}, "poolclass": StaticPool}`
- Ensures in-memory SQLite database uses a single shared connection across threads (required for Flask-SQLAlchemy test isolation)

**`tests/test_phase31_fixes.py` — Fixture Design**
- `app` fixture uses `create_app("testing")` for proper DB URI from the start
- `LOGIN_DISABLED = False` explicitly re-enabled for security test accuracy
- `autouse` fixture `clear_flask_login_context` removes `g._login_user` after each test, preventing Flask-Login state leakage between tests in module-scoped app fixtures

### Unit Tests — 19 Tests, ALL PASS

| Test Class | Tests | Description |
|------------|:-----:|-------------|
| `TestHtmxPollingStop` | 7 | HTTP 286 for completed/failed/cancelled/awaiting_approval; HTTP 200 for running/pending; non-HTMX requests always return 200 |
| `TestVideoPlayback` | 3 | `preload="auto"` present, `controls` attribute present, `playsinline` attribute present |
| `TestBrandPersonaVisibility` | 7 | Brand selector visible with data, persona selector visible with data, section not hidden, "Create" links when no brands, "Create" links when no personas, section visible regardless of data, form values posted |
| `TestHtmxAccessControl` | 2 | HTMX poll requires authentication (302 redirect), cross-user poll blocked (404) |

### E2E Verification — 18 Checks, ALL PASS

| Check | Result |
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

### Full Test Suite — 118 Tests, ALL PASS

| File | Tests |
|------|:-----:|
| `tests/test_filters.py` | 23 |
| `tests/test_recipe_timeout.py` | 7 |
| `tests/test_recipe_active.py` | 12 |
| `tests/test_gap_fixes.py` | 13 |
| `tests/test_owasp.py` | 44 |
| `tests/test_phase31_fixes.py` | 19 |
| **Total** | **118** |

### Files Changed

- `app/routes/recipes.py` — `run_status()` returns HTTP 286 for terminal statuses to stop HTMX polling
- `app/templates/recipes/_run_progress.html` — `preload="auto"` on video elements for full playback
- `app/templates/recipes/run.html` — Brand/persona selectors always visible; fixed persona `url_for`
- `app/config.py` — `TestingConfig` adds `StaticPool` engine options for in-memory SQLite test isolation
- `tests/test_phase31_fixes.py` — 19 new unit tests with proper fixture isolation

---

## Phase 32 — News Digest SEO / GEO / AEO Optimization

**Date**: February 27, 2026
**Methodology**: Ralph Loop — Research → Analyze → Learn → Plan → Hypothesize → Test
**Goal**: Add opt-in SEO / GEO / AEO optimization to the News Digest recipe's Blog Post format.

### What Changed

When a user selects **Blog Post** format and checks the **SEO / GEO / AEO Optimization** checkbox, the recipe now:

1. **Replaces** the default blog format instructions with comprehensive SEO/GEO/AEO guidelines
2. **Injects** keyword-rich heading hierarchy, source attribution, FAQ section, and Featured Snippet structure
3. **Parses** a `---SEO_METADATA_JSON---` separator from the Gemini response to extract structured metadata
4. **Renders** a bonus **SEO Metadata Card** output with title tag, meta description, primary/secondary keywords, FAQ schema, and internal link suggestions

### Architecture Decisions

| Decision | Rationale |
|----------|-----------|
| **Single-file change** (`news_digest.py` only) | No route, template, model, or config changes needed — checkbox rendered by existing template logic |
| **Flag gating** (`seo_optimize == "1" AND format == "blog"`) | SEO is irrelevant for email/LinkedIn formats — silently ignored |
| **Static step count (4)** | Adding a 5th step would break progress bar for non-SEO runs; SEO work is folded into existing steps |
| **Graceful metadata parsing** | If Gemini omits separator or returns malformed JSON, blog content is returned unchanged — zero breakage |
| **Three helper methods** | `_build_seo_format_instructions()`, `_extract_seo_metadata()`, `_format_seo_metadata()` — each static, independently testable |

### SEO/GEO/AEO Coverage

| Optimization | Techniques Injected |
|-------------|-------------------|
| **SEO** | H1/H2/H3 keyword hierarchy, primary keyword in first 100 words, 1500–2500 word target, internal linking cues, transition words |
| **GEO** | Declarative factual statements, "According to [Source]" attribution, self-contained parseable sections |
| **AEO** | Dedicated FAQ section (4–5 Q&A pairs), question-answer paragraph structure, Featured Snippet formatting |

### Files Changed

| File | Change |
|------|--------|
| `app/recipes/news_digest.py` | Added `seo_optimize` InputField, `_build_seo_format_instructions()`, `_extract_seo_metadata()`, `_format_seo_metadata()`, enhanced `execute()` flow |
| `tests/test_news_digest_seo.py` | 29 new unit tests across 7 test classes |

### Test Results

- **29 new tests**: ALL PASS
- **Full suite**: 147/147 — ZERO regressions

---

## Phase 33 — Enhanced Image Creator (6 Features)

**Date**: February 27, 2026
**Methodology**: Compound Engineering + Ralph Loop
**Goal**: Transform the Image Creator from a basic prompt-to-image tool into a smart, value-added recipe with 6 key enhancements — AI Prompt Assistant, Reference Image Upload, Style Presets, Platform Selector, Negative Prompt, and Brand Photo Library.

### The 6 Enhancements

| # | Feature | What It Does |
|---|---------|-------------|
| **A** | **AI Prompt Assistant** | User describes in plain English → Gemini writes a detailed image prompt. No prompt-engineering skills needed. Graceful fallback if API fails. |
| **B** | **Reference Image Upload** | User uploads a reference photo → Gemini Vision analyses style, colours, composition → analysis fed into prompt + file passed to `generate_ugc_image(reference_paths=...)`. |
| **C** | **Style Presets** | 8 presets (None, Product Shot, Social Graphic, Lifestyle, Flat Lay, Abstract, Portrait, Infographic) with prompt fragments injected into AI meta-prompt. |
| **D** | **Platform Selector** | 9 platforms (Instagram Feed/Story, LinkedIn, YouTube Thumb, TikTok, Facebook, X, Website Hero) with auto-recommended aspect ratios and composition hints. |
| **E** | **Negative Prompt** | Optional "things to exclude" field — injected into both Assisted and Manual prompt paths. |
| **F** | **Brand Photo Library** | Auto-pulls up to 3 brand reference images via `get_brand_reference_paths()` and passes them alongside any user-uploaded reference. |

### Additional Improvements

- **Brand/Persona injection** — `build_brand_context()` / `build_persona_context()` enrich the AI prompt
- **Multi-image generation** — 1, 2, or 4 images per run
- **Input validation (OWASP)** — whitelist-based model, ratio, count, style, platform, mode validation
- **Error resilience** — per-image try/except; partial failures produce error cards alongside successes
- **Summary card** — comprehensive output showing mode, model, ratio, style, platform, brand, persona, reference status, negative prompt, cost

### Architecture Decisions

| Decision | Rationale |
|----------|-----------|
| **Assisted/Manual dual mode** | Non-technical users get AI prompt writing; power users keep full control |
| **Gemini Vision for references** | Analyses style, colours, composition — much richer than just passing a filename |
| **Platform → auto aspect ratio** | Selects best ratio automatically; user can still override |
| **Style presets as prompt fragments** | Injected into Gemini meta-prompt, not appended — AI weaves them naturally |
| **Lazy imports inside `execute()`** | Avoids import-time dependency on API keys; consistent with other recipes |
| **Whitelist validation** | `_MODEL_MAP`, `_VALID_RATIOS`, `_VALID_COUNTS`, `_STYLE_PRESETS`, `_PLATFORM_MAP` — prevents injection |

### Files Changed

| File | Change |
|------|--------|
| `app/recipes/image_creator.py` | Complete rewrite — 9 input fields, AI Prompt Assistant, Reference Vision, Style Presets, Platform Selector, Negative Prompt, Brand Photo Library, dual mode |
| `tests/test_image_creator.py` | **78 new tests** — 13 test classes covering all 6 features, validation, error handling, progress callbacks, summary card, metadata |
| `tests/test_recipe_active.py` | Updated stub count 10 → 9, active set 3 → 4 |

### Test Results

- **78 new tests**: ALL PASS
- **Full suite**: 225/225 — ZERO regressions

---

## Phase 34 — Video Creator + OWASP A04 + SQLAlchemy Fix + AI Content Machine

**Date**: February 27, 2026
**Methodology**: Compound Engineering + Ralph Loop
**Goal**: Four-pronged phase — activate Video Creator recipe (4 models), harden file uploads (OWASP A04 magic bytes), eliminate SQLAlchemy deprecation warnings, and build the AI Content Machine recipe.

### Phase 34A — Video Creator Recipe

Activated the `video-creator` stub and wired it to `tools.create_video.generate_ugc_video` with full AI-assisted prompt generation.

| # | Feature | Detail |
|---|---------|--------|
| VC1 | **Activate recipe** | `is_active = True` |
| VC2 | **11 input fields** | creation_mode, prompt, reference_image, style_preset (8), platform (9), negative_prompt, model (4), aspect_ratio (3), duration (4s/6s/8s), video_count (1/2/4) |
| VC3 | **4 video models** | Google Veo 3.1, Kie AI Kling 3.0, Kie AI Sora 2 Pro, WaveSpeed Kling 3.0 |
| VC4 | **AI prompt crafting** | Gemini transforms plain English → detailed video prompt with brand/persona/style/platform context |
| VC5 | **Reference image analysis** | Gemini Vision analyses uploaded reference image for style/colour/composition |
| VC6 | **Brand Photo Library** | Auto-pulls brand reference images via `get_brand_reference_paths()` |
| VC7 | **Multi-video generation** | 1, 2, or 4 videos per run with per-video progress and error isolation |

**Files**: `app/recipes/video_creator.py` (rewrite), `tests/test_video_creator.py` (73 tests)

### Phase 34B — OWASP A04 File Upload Hardening

Implemented defence-in-depth for all file upload endpoints.

| # | Feature | Detail |
|---|---------|--------|
| FU1 | **`validate_upload()`** | Centralized utility in `app/security.py` — single call replaces all ad-hoc validation |
| FU2 | **Magic byte verification** | `_check_magic_bytes()` reads first 12 bytes → compares against PNG, JPEG, GIF, WEBP (RIFF+WEBP at offset 8), PDF, WEBM, MP3, WAV (RIFF+WAVE at offset 8) signatures |
| FU3 | **Per-field size limits** | `MAX_UPLOAD_SIZE_BYTES`: image=10MB, video=100MB, audio=25MB, document=20MB, recipe_input=10MB |
| FU4 | **3 endpoints hardened** | Recipe file upload, campaign reference upload, brand photo library upload |

**Files**: `app/security.py`, `app/routes/recipes.py`, `app/routes/api.py`, `tests/test_upload_security.py` (36 tests)

### Phase 34C — SQLAlchemy Deprecation Fix

Eliminated all `Query.get()` / `Query.get_or_404()` calls — replaced with `db.session.get()` / `db.session.get_or_404()`.

| Metric | Value |
|--------|-------|
| Replacements | 22 |
| Files changed | 9 (`api.py`, `dashboard.py`, `campaigns.py`, `generate.py`, `posts.py`, `export.py`, `recipes.py`, `prompt_service.py`, `script_service.py`) |
| Deprecation warnings after | 0 |

### Phase 34D — AI Content Machine Recipe

New recipe for competitive content intelligence — user pastes competitor posts/URLs → Gemini analyses hooks, psychological triggers, content patterns, and generates a ready-to-use content strategy.

| # | Feature | Detail |
|---|---------|--------|
| CM1 | **4 input fields** | competitor_content (textarea), platforms (multiselect), analysis_depth (quick/standard/deep), output_format (full_report/hooks_only/templates_only/psychology_only) |
| CM2 | **4-stage pipeline** | Hook analysis → Psychology mapping → Pattern extraction → Strategy generation |
| CM3 | **Flexible output** | Full report or filtered sections based on user selection |
| CM4 | **Brand/persona context** | All AI prompts enriched with brand voice and persona tone |
| CM5 | **Error resilience** | Per-stage try/except — partial failures produce warning cards, not crashes |

**Files**: `app/recipes/content_machine.py` (new), `tests/test_content_machine.py` (66 tests)

### Test Results

- **175 new tests**: 73 (Video Creator) + 66 (Content Machine) + 36 (Upload Security)
- **Full suite**: 400/400 — ZERO regressions
- **Deprecation warnings**: 0

---

## Phase 35 — E2E Playwright Testing

**Date**: February 27, 2026
**Methodology**: Compound Engineering + Ralph Loop
**Goal**: Full end-to-end browser testing of all active recipes, navigation, security controls, brand/persona management, CSRF protection, stub recipe blocking, and API endpoints using Playwright with Chromium.

### Implementation

| # | Feature | Detail |
|---|---------|--------|
| E1 | **Session-scoped fixtures** | Single browser launch, one login per role (admin + user), shared cookie context — eliminates rate-limiting issues |
| E2 | **Anonymous context** | Separate unauthenticated browser context for access-control tests |
| E3 | **71 tests, 12 classes** | Auth, security headers, navigation, recipe library, all 6 recipe forms, brand/persona CRUD, CSRF, recipe history, admin features, user isolation, API endpoints, recipe documentation |
| E4 | **All 6 active recipes verified** | Ad Video Maker, Photo to Ad, News Digest, Image Creator, Video Creator, Content Machine — detail pages load, run forms render, brand/persona selectors present |
| E5 | **Stub recipe blocking** | Verified `clip-factory` (stub) returns 404 for both detail and run pages |
| E6 | **Security headers verified** | CSP, X-Content-Type-Options, X-Frame-Options, Referrer-Policy present on all responses |
| E7 | **CSRF tokens verified** | Login form, recipe run forms, brand create form all contain CSRF tokens |

### Test Classes

| Test Class | Tests | Description |
|------------|:-----:|-------------|
| `TestAuth` | 4 | Login page, admin session, unauthenticated redirect, recipe auth guard |
| `TestSecurityHeaders` | 4 | CSP, X-Content-Type-Options, X-Frame-Options, Referrer-Policy |
| `TestNavigation` | 5 | Dashboard, recipes, brands, campaigns, pricing |
| `TestRecipeLibrary` | 4 | Active visible, stubs hidden, stub 404 |
| `TestAdVideoMakerRecipe` | 5 | Detail, form, file upload, brand, persona |
| `TestPhotoToAdRecipe` | 4 | Detail, form, file upload, brand/persona |
| `TestNewsDigestRecipe` | 5 | Detail, form, topic, SEO, format |
| `TestImageCreatorRecipe` | 8 | Detail, form, prompt, style, platform, model, reference, brand/persona |
| `TestVideoCreatorRecipe` | 7 | Detail, form, prompt, model, duration, style, brand/persona |
| `TestContentMachineRecipe` | 6 | Detail, form, competitor, analysis mode, platform, brand/persona |
| `TestBrandManagement` | 2 | List, create form |
| `TestPersonaManagement` | 2 | List, create form |
| `TestCSRF` | 3 | Login, recipe run, brand create CSRF tokens |
| `TestRecipeHistory` | 1 | History page loads |
| `TestAdminFeatures` | 1 | Admin dashboard content |
| `TestUserIsolation` | 2 | Non-admin access to home and recipes |
| `TestAPIEndpoints` | 2 | 404 for missing file, auth required |
| `TestRecipeDocumentation` | 6 | How-to-use instructions for all 6 recipes |

### Files Changed

| File | Change |
|------|--------|
| `tests/test_e2e_playwright.py` | **Complete rewrite** — 71 E2E tests, session-scoped Playwright fixtures, 12 test classes |

### Test Results

- **71 E2E tests**: ALL PASS (42.52s runtime)
- **400 unit tests**: ALL PASS (19.02s runtime)
- **Full suite**: 471/471 — ZERO failures, ZERO regressions

---

## Phase 36 — Higgsfield Seedance & Minimax Video Models

**Date**: February 27, 2026

**Methodology**: Compound Engineering + Ralph Loop

### Goal
Integrate Seedance (ByteDance) and Minimax as cost-effective video generation models (~$0.05/video) via the Higgsfield provider, expanding the Video Creator recipe from 4 to 6 models and giving users budget-friendly alternatives to Veo 3.1 ($0.50) and Kling/Sora ($0.30).

### Research
- Scraped Higgsfield API documentation to understand the REST API structure
- Identified the async submit → poll pattern (same as Higgsfield image generation)
- Confirmed model IDs for Seedance (`bytedance/seedance/v1/pro/image-to-video`) and Minimax (`minimax/video/general`)
- Verified the existing provider architecture supports multi-model providers

### Implementation

**7 files modified, 1 new test file created:**

| # | File | Change |
|---|------|--------|
| 1 | `tools/providers/higgsfield.py` | Added `_VIDEO_MODELS` dict mapping model names to API IDs; implemented `submit_video()` for text-to-video and image-to-video; implemented `poll_video()` with timeout/retry; updated `poll_tasks_parallel()` for mixed image/video tasks |
| 2 | `tools/create_video.py` | Added "seedance" and "minimax" to `_resolve_model()` mapping; extended `max_wait` timeout (900s) for both new models in `generate_ugc_video()` and `generate_for_record()` |
| 3 | `tools/providers/__init__.py` | Registered both models in `VIDEO_PROVIDERS` with `higgsfield` as default provider |
| 4 | `tools/config.py` | Added `HIGGSFIELD_API_KEY_ID`, `HIGGSFIELD_API_KEY_SECRET` env vars; added cost entries for `("seedance","higgsfield")` at $0.05 and `("minimax","higgsfield")` at $0.05; defined `HIGGSFIELD_VIDEO_MODELS` config dict |
| 5 | `app/services/model_service.py` | Added "seedance" and "minimax" to `MODEL_CATALOG` with Higgsfield provider details, pricing, free-tier flags, and descriptions |
| 6 | `app/recipes/video_creator.py` | Added both to `_MODEL_MAP` with display labels and cost tags; updated recipe `description`, `how_to_use` table (6-model comparison), and model selector `help_text` |
| 7 | `tests/test_higgsfield_video.py` | **56 new unit tests** across 9 test classes |

### Test Coverage (56 new tests)

| Test Class | Count | Coverage |
|------------|-------|----------|
| `TestProviderRegistry` | 5 | Video provider routing, model resolution |
| `TestSubmitVideo` | 8 | Payload structure (t2v, i2v), model mapping, error handling |
| `TestPollVideo` | 9 | Success, failure, NSFW, timeout, missing URL, retry on HTTP errors |
| `TestPollVideoParallel` | 3 | Concurrent polling, mixed success/failure |
| `TestCostAndCatalog` | 14 | Cost entries, model catalog, free tier flags, default providers |
| `TestVideoCreatorRecipeModels` | 4 | `_MODEL_MAP` entries, input field options, model count |
| `TestVideoModelConstants` | 3 | Higgsfield model ID mapping |
| `TestSecurityEdgeCases` | 5 | Empty/long prompts, invalid aspect ratio/duration, unknown model fallback |
| `TestVideoCreatorRecipeModels` | 5 | Model map and input field integration |

### Video Model Lineup (6 models, 4 providers)

| Model | Provider | Cost | Quality | Use Case |
|-------|----------|------|---------|----------|
| Veo 3.1 | Google AI Studio | $0.50 | Cinematic | Hero content, ads |
| Kling 3.0 | WaveSpeed / Kie | $0.30 | Great | Short UGC, social |
| Sora 2 | WaveSpeed | $0.30 | Good | General purpose |
| Sora 2 Pro | WaveSpeed / Kie | $0.30 | Excellent | High-fidelity |
| **Seedance** | **Higgsfield** | **$0.05** | Good | Budget-friendly, fast |
| **Minimax** | **Higgsfield** | **$0.05** | Excellent | Best value |

### Security (OWASP)
- All inputs validated (model whitelist, aspect ratio whitelist, duration whitelist, prompt length)
- Unknown model values fall back to defaults instead of crashing
- `submit_video` validates model against `HIGGSFIELD_VIDEO_MODELS` registry

### Test Results
- **56 new tests**: ALL PASS
- **527 total tests**: ALL PASS — ZERO regressions

---

## Phase 37 — Brand Guideline System Prompt Enhancement

**Date**: February 27, 2026

**Methodology**: Compound Engineering + Ralph Loop

### Goal
Integrate production-grade brand guideline system prompts (from R38 UGC Ads Factory, Split AI Image Ad Generator, R44 Influencer Toolkit JSON templates) into all visual-output recipes so that every generated image and video is truly on-brand, on-persona, diverse, and viral-quality — without breaking any existing functionality.

### Research
- Analysed 3 JSON template system prompts (R38, Split AI, R44) for reusable quality rules
- Identified 5 categories of creative directives: brand fidelity, diversity, prompt hygiene, UGC authenticity, generation-type-specific quality
- Audited `Brand` model fields (colours, voice, hashtags, caption template, logo) and `UserPersona` model fields (bio) for underutilised data

### Implementation

**5 files modified, 1 new test file created:**

| # | File | Change |
|---|------|--------|
| 1 | `app/recipes/base.py` | **Track A**: Enriched `build_brand_context` — now includes colour palette with labelled roles (Primary/Secondary/Tertiary/Accent), voice/tone JSON, hashtags, caption template, logo reference, and colour enforcement instruction |
| 2 | `app/recipes/base.py` | **Track B**: Enriched `build_persona_context` — now includes `bio` field |
| 3 | `app/recipes/base.py` | **Track C**: New `build_creative_directives()` method — universal quality rules (brand fidelity, diversity, prompt hygiene, UGC authenticity, image/video quality) |
| 4 | `app/recipes/image_creator.py` | Updated `_build_assisted_prompt` — injects `build_creative_directives(generation_type="image")` with UGC detection from style label |
| 5 | `app/recipes/video_creator.py` | Updated `_build_assisted_prompt` — injects `build_creative_directives(generation_type="video")` with UGC detection from style label |
| 6 | `app/recipes/photo_to_ad.py` | Updated `_execute_script` — injects `build_creative_directives(generation_type="image")` into concept prompt |
| 7 | `tests/test_brand_context.py` | **63 new unit tests** across 4 test classes |

### Creative Directives System

The new `build_creative_directives()` method centralises rules from production JSON templates:

| Directive Category | Key Rules |
|---|---|
| **Brand Fidelity** | Never alter product colours; weave brand colours into scene; respect visual style |
| **Diversity & Inclusion** | Ensure gender/ethnicity/hair diversity; default age 21–38; visible imperfections |
| **Prompt Hygiene** | No double quotes; max 7-word ad copy; follow caption template; use brand hashtags |
| **UGC Authenticity** (opt-in) | Amateur iPhone style keywords; candid poses; real-world settings; imperfect framing |
| **Image Quality** | Describe subject/setting/composition/camera angle/lighting/mood/colour palette/textures |
| **Video Quality** | Explicit camera movement; motion/lighting/atmosphere; dialogue rules |

### Enriched Context Fields

| Method | New Fields Added |
|---|---|
| `build_brand_context` | `colours_json` (labelled Primary→Accent 2), `voice_json`, `hashtags`, `caption_template`, `logo_path`, colour enforcement instruction |
| `build_persona_context` | `bio` field |

### Recipes Reviewed

| Recipe | Action | Reason |
|---|---|---|
| Image Creator | ✅ Updated | Visual output — needs brand colours, directives |
| Video Creator | ✅ Updated | Visual output — needs brand colours, directives |
| Photo to Ad | ✅ Updated | Visual output — needs brand colours, directives |
| Content Machine | ⏭ Skipped | Text-only — already uses brand/persona context |
| News Digest | ⏭ Skipped | Text-only — already uses brand/persona context |
| Ad Video Maker | ⏭ Skipped | Already has its own rich prompt system |

### Test Coverage (63 new tests)

| Test Class | Count | Coverage |
|------------|-------|----------|
| `TestBuildBrandContext` | 29 | All brand fields, colours, voice, hashtags, caption template, logo, nulls, malformed JSON, truncation, delimiters, minimal brand |
| `TestBuildPersonaContext` | 17 | All persona fields, bio, nulls, delimiters, minimal persona |
| `TestBuildCreativeDirectives` | 13 | Image/video/text directives, UGC on/off, fidelity rules, diversity, prompt hygiene, delimiters |
| `TestRecipeIntegration` | 4 | Image Creator prompt includes directives, Video Creator prompt includes directives, UGC style triggers UGC directives, non-UGC excludes UGC directives |

### Security (OWASP)
- Malformed JSON in `colors_json`, `voice_json`, `hashtags` handled with try/except — no crashes
- `brand_doc` preview truncated at 800 chars to prevent prompt injection via oversized documents
- All new fields are read-only context injection — no user-controllable code paths added

### Test Results
- **63 new tests**: ALL PASS
- **519 total tests**: ALL PASS — ZERO regressions

---

## Phase 38 — Extended Video Duration Options

**Date**: February 27, 2026

**Methodology**: Compound Engineering + Ralph Loop

### Goal
Give users control over video length — add 15s and 20s options, per-model maximum duration clamping with clear user notifications, and scalable timeout logic for longer generation.

### Research
- Audited all 4 providers' `submit_video` functions for duration support:
  - **Google Veo 3.1**: snaps to 4, 6, or 8 seconds (hard limit)
  - **Kling 3.0** (Kie/WaveSpeed): up to ~10s
  - **Sora 2** (WaveSpeed): maps to 4, 8, 12, 16, 20s
  - **Sora 2 Pro** (Kie/WaveSpeed): n_frames 10/15/20; maps up to 20s
  - **Seedance/Minimax** (Higgsfield): integer seconds, ~10s typical max

### Changes

| File | Change |
|------|--------|
| `app/recipes/video_creator.py` | Extended `_VALID_DURATIONS` to include 15s, 20s; added `_MODEL_MAX_DURATION` map (per-model caps); duration clamping logic in `execute()` with user notification; updated UI labels with model-specific hints |
| `tools/create_video.py` | Scaled timeout logic — adds extra wait for durations >10s |
| `tools/providers/wavespeed.py` | Extended Sora duration mapping to support 16s and 20s |
| `tools/providers/kie.py` | Extended Sora 2 Pro n_frames mapping for 15s and 20s |
| `tests/test_higgsfield_video.py` | 14 new tests: duration constants, per-model max validation, UI field options, clamping behaviour (Veo clamped, Sora not clamped, no-clamp when within limit) |

### Duration Support Matrix

| Model | Max Duration | Supported |
|-------|-------------|-----------|
| Veo 3.1 | 8s | 4, 6, 8 |
| Kling 3.0 | 10s | up to 10 |
| Sora 2 | 20s | 4, 8, 12, 16, 20 |
| Sora 2 Pro | 20s | 4, 8, 12, 16, 20 |
| Seedance | 10s | 5–10 |
| Minimax | 10s | 5–10 |

### Testing
- 14 new duration-specific unit tests — all pass
- Full suite: **531 tests, 0 failures**

### Security
- Duration validated against `_VALID_DURATIONS` whitelist (input validation — OWASP A03)
- Per-model clamping prevents unsupported API calls (defence in depth)
- No user input passed directly to APIs without validation

---

## Phase 39 — Output Rendering Bug Fixes & Gap Analysis

**Date**: February 27, 2026

**Methodology**: Compound Engineering + Ralph Loop (Research → Analyze → Learn → Plan → Hypothesize → Test)

### Goal
Full gap analysis of the codebase — find and fix rendering bugs, key mismatches, and documentation inaccuracies.

### Bugs Found & Fixed

| Bug | Root Cause | Fix |
|-----|-----------|-----|
| **Image Creator images not previewed** | Template only rendered images with `image_url` key; Image Creator outputs `{"type": "image", "url": "..."}` | Added `{% elif output.get('url') and output.get('type') == 'image' %}` branch in `_run_progress.html` |
| **Output titles showing generic text** | Content Machine, Image Creator, Video Creator use `"title"` key; template only read `"label"` | Updated all 8 `output.get('label', ...)` calls to fall back to `output.get('title', ...)` |
| **Stub count wrong in docs** | Rules said "7 stubs" but there are 8 (clip-factory, influencer-content-kit, motion-capture, multi-scene-video, social-scraper, style-cloner, talking-avatar, vertical-reframe) | Updated `ai-services.mdc` and `documentation.mdc` to say 8 |

### Files Changed

| File | Change |
|------|--------|
| `app/templates/recipes/_run_progress.html` | Added standalone image rendering branch; added `title` key fallback in all 8 output label references |
| `.cursor/rules/ai-services.mdc` | Corrected stub count from 7 → 8 |
| `.cursor/rules/documentation.mdc` | Corrected stub count from 7 → 8 |

### Verification
- CSRF: Every POST form has matching `csrf_token()` — 19 templates verified
- Routes: All `url_for()` calls match registered Flask endpoints
- Deprecated patterns: Zero `Query.get()` calls remaining
- Security headers, rate limiting, file upload validation all intact
- Full test suite: **531 tests, 0 failures**

---

## Phase 44 — Talking Avatar B-Roll Pipeline (R52 Port)

> 2026-02-28 · Compound Engineering + Ralph Loop

### Goal
Port the proven B-roll generation pipeline from the R52 longform system (`r52_longform_app.py`) into the Talking Avatar recipe, enabling users to generate both a talking-head video AND matching B-roll footage in a single run — exactly like the original production workflow.

### What Changed

| File | Change |
|------|--------|
| `app/recipes/talking_avatar.py` | **Major enhancement** — Added 3 new input fields (`style_reference`, `generate_broll`, `broll_count`), 5 new helper methods (`_analyse_style_reference`, `_generate_broll_prompts`, `_generate_broll_images`, `_generate_broll_videos`, `_run_broll_pipeline`), updated `get_steps()` to 9 steps, enriched metadata (description, `how_to_use`, `estimated_cost`). B-roll pipeline orchestrates: Gemini Vision style analysis → SEALCaM prompt generation → image generation → video generation. |
| `tests/test_phase44.py` | **NEW** — 50 unit tests covering: input fields, steps, style analysis, prompt generation, image generation, video generation, pipeline orchestration, full execute with B-roll, metadata, and backward compatibility. |

### Architecture — B-Roll Pipeline

```
Style Reference Image (optional)
        │
        ▼
 _analyse_style_reference()  ← Gemini Vision
        │
        ▼
 _generate_broll_prompts()   ← Gemini text (SEALCaM framework)
        │
        ▼
 _generate_broll_images()    ← generate_ugc_image (Nano Banana Pro)
        │
        ▼
 _generate_broll_videos()    ← generate_ugc_video (Kling 3.0, 5s, 16:9)
        │
        ▼
 Outputs: images + video clips appended to run
```

### New Input Fields

| Field | Type | Default | Purpose |
|-------|------|---------|---------|
| `style_reference` | file (image) | — | Visual style guide for B-roll clips |
| `generate_broll` | select | "no" | Toggle B-roll generation on/off |
| `broll_count` | select | "3" | Number of B-roll clips (2, 3, or 4) |

### Key Design Decisions

1. **SEALCaM framework** — Same cinematic prompt structure as R52: Subject, Environment, Action, Lighting, Camera, Metatokens.
2. **Graceful degradation** — Each B-roll stage can fail independently without blocking others. If prompts fail → skip images/videos. If one image fails → still attempt others. If videos fail → images still available.
3. **Style reference is optional** — Without it, a sensible default style is used ("clean, modern, professional").
4. **Brand context flows through** — B-roll prompts incorporate brand/persona context for visual consistency.
5. **Summary card tracks B-roll** — Final summary shows B-roll image and video counts.
6. **Backward compatible** — All Phase 41 talking-head functionality is preserved. Users who select "No" for B-roll get the exact same experience as before.

### Test Results
- **709 unit tests** — all passing (50 new + 659 previous)
- **83 E2E tests** — unaffected
- **Total: 792 tests** (709 unit + 83 E2E)

---

## Phase 43 — Database Persistence Fix (Brand/Persona Data Loss Prevention)

> 2026-02-28 · Compound Engineering + Ralph Loop

### Goal
Fix a **critical data-loss bug** where running unit tests wiped the production `videobuds.db` database — destroying all user-created brands, personas, campaigns, and other data.

### Root Cause Analysis

| Layer | Finding |
|-------|---------|
| `tests/test_recipe_timeout.py` | Called `create_app("default")` which maps to `DevelopmentConfig` → production `videobuds.db` |
| Flask-SQLAlchemy engine caching | Engine is created and **cached** during `create_app()` — overriding `SQLALCHEMY_DATABASE_URI` after the fact has **no effect** |
| `db.drop_all()` in test teardown | Dropped **all tables from the production database** because the engine was still pointing to `videobuds.db` |
| `tests/test_filters.py` | Also used `create_app("default")`, connecting to the production DB during initialization |
| Seed function | After table drop, `create_app()` runs `db.create_all()` + seed → creates generic "Sample Brand" / "Default Persona" instead of user's custom data |

### Fixes Applied (4 files)

| File | Change |
|------|--------|
| `tests/test_recipe_timeout.py` | Changed `create_app("default")` → `create_app("testing")` with explanatory docstring |
| `tests/test_filters.py` | Changed `create_app("default")` → `create_app("testing")` in both test methods |
| `tests/conftest.py` | **NEW** — Two session-scoped autouse safety guards: (1) `db.drop_all()` refuses to operate on file-backed SQLite; (2) warns if `create_app` called with non-testing config |

### Safety Guards

1. **`_guard_production_database`** (conftest.py) — Monkey-patches `db.drop_all()` to check the engine URL before proceeding. If it points to a file-backed SQLite database (not `:memory:`), it raises `RuntimeError` immediately.
2. **`_warn_on_production_db_connect`** (conftest.py) — Wraps `create_app()` with a warning if the config is not `"testing"`, alerting developers before the engine connects.

### Test Results
- **632 unit tests** — all passing, zero regressions
- **83 E2E tests** — unaffected (use production DB correctly via Playwright)
- **Total: 715 tests** (632 unit + 83 E2E)

---

## Phase 42 — Gap Analysis & Hardening

> 2026-02-28 · Compound Engineering + Ralph Loop

### Goal
Systematic gap analysis across the entire codebase — find and fix issues before they become bugs.

### Gap Analysis Results

| Area | Status | Detail |
|------|--------|--------|
| Route security (`@login_required`) | ✅ Pass | All non-auth routes protected |
| CSRF protection | ✅ Pass | All forms have tokens; `csrf_protect` registered |
| Ownership validation | ✅ Pass | All routes verify `user_id == current_user.id` |
| `url_for` correctness | ✅ Pass | All template endpoints match registered routes |
| Deprecated `Query.get()` | ✅ Pass | Zero occurrences — fully migrated to `db.session.get()` |
| Security headers (OWASP A05) | ✅ Pass | X-Content-Type-Options, X-Frame-Options, X-XSS-Protection, CSP, HSTS (production) |
| Model/provider cost registry | ✅ Pass | All 12 model/provider combos have valid cost entries |
| Module imports | ✅ Pass | All 12 service/provider modules import cleanly |
| Recipe input fields & steps | ✅ Pass | All 14 recipes have valid `get_input_fields()` and `get_steps()` |
| Recipe `is_active` counts | ✅ Pass | 8 active, 6 stubs, assertion in `test_recipe_active.py` verified |
| **Stub recipe signatures** | ⚠️ **FIXED** | 6 stubs were missing `brand=None, persona=None` in `execute()` — would crash on activation |
| **E2E coverage** | ⚠️ **FIXED** | `talking-avatar` and `influencer-content-kit` were missing from E2E tests |

### Files Modified (8)

| File | Change |
|------|--------|
| `app/recipes/clip_factory.py` | Added `brand=None, persona=None` to `execute()` |
| `app/recipes/vertical_reframe.py` | Added `brand=None, persona=None` to `execute()` |
| `app/recipes/social_scraper.py` | Added `brand=None, persona=None` to `execute()` |
| `app/recipes/motion_capture.py` | Added `brand=None, persona=None` to `execute()` |
| `app/recipes/multi_scene_video.py` | Added `brand=None, persona=None` to `execute()` |
| `app/recipes/style_cloner.py` | Added `brand=None, persona=None` to `execute()` |
| `tests/test_e2e_playwright.py` | Added `TestTalkingAvatarRecipeE2E` (5 tests) + `TestInfluencerContentKitE2E` (5 tests) + 2 parametrized doc tests |

### Test Results
- **632 unit tests** — all passing, zero regressions
- **83 E2E tests** (up from 71) — talking-avatar and influencer-content-kit added
- **Total: 715 tests** (632 unit + 83 E2E)

---

## Phase 41 — Talking Avatar + Influencer Content Kit + Persona Wiring

> 2026-02-28 · Compound Engineering + Ralph Loop

### Goal
1. **Activate Talking Avatar** recipe — wire existing talking head pipeline (Gemini TTS + Higgsfield Speak v2/talking_photo + WaveSpeed InfiniteTalk).
2. **Build Influencer Content Kit** recipe — multi-post planning with image + video generation from character photo and brief.
3. **Wire persona into remaining routes** — `generate.py` and `api.py` agent endpoints now pass persona context.

### Files Modified/Created (7)

| File | Change |
|------|--------|
| `tools/providers/tts.py` | **NEW** — Gemini 2.5 Flash Preview TTS: text → WAV audio, 8 voices, retry logic, PCM→WAV |
| `app/recipes/talking_avatar.py` | **REWRITTEN** — Full pipeline: headshot → script → TTS → upload → 3-tier talking head fallback |
| `app/recipes/influencer_content_kit.py` | **REWRITTEN** — Character analysis → multi-post planning → parallel image + video per post |
| `app/routes/generate.py` | Persona wired into `_run_generation`, `generate_single`, `generate_for_day`, `_bulk_generate_worker` |
| `app/routes/api.py` | Persona wired into `agent_suggest_captions`, `agent_enhance_prompt` |
| `tests/test_phase41.py` | **NEW** — 59 tests across 6 test classes |
| `tests/test_recipe_active.py` | Updated stub count 8→6, active set expanded to 8 recipes |

### Talking Avatar Pipeline

| Stage | Provider | Detail |
|-------|----------|--------|
| Headshot analysis | Gemini Vision | Face detection/validation |
| Script generation | Gemini | From brief + brand/persona (or user-provided) |
| TTS | Gemini 2.5 Flash Preview | 8 voice presets, WAV output |
| Media upload | WaveSpeed CDN | Audio + image hosted for video pipeline |
| Video (3-tier) | Higgsfield → WaveSpeed | Speak v2 → talking_photo → InfiniteTalk |

### Influencer Content Kit Pipeline

| Stage | Detail |
|-------|--------|
| Character analysis | Gemini Vision analyses character photo for visual details |
| Post planning | AI generates structured post plans (type, concept, caption) |
| Image generation | Parallel image creation per post with character context |
| Video generation | Optional video creation for video-type posts |

### Test Results
- **59 new tests** — all passing
- **632 total unit tests** — all passing, zero regressions
- **71 E2E tests** — unchanged
- **Total: 703 tests** (632 unit + 71 E2E)

---

## Phase 40 — AI Content Editor + News Digest Grounding

**Date**: February 27, 2026

**Methodology**: Compound Engineering + Ralph Loop (Research → Analyze → Learn → Plan → Hypothesize → Test)

### Goal
1. **Differentiate AI News Digest** from ChatGPT/Claude by adding Gemini Google Search grounding so the recipe searches the live web for real, current news instead of relying on stale training data.
2. **Add an AI Content Editor** — after any recipe generates text (scripts, blogs, newsletters, ad copy), users can refine it conversationally with AI while maintaining full brand and persona context.

### Implementation

#### A. Gemini Google Search Grounding

| File | Change |
|------|--------|
| `app/services/agent_service.py` | Added `_call_gemini_grounded()` — sends `google_search_retrieval` tool with Gemini API call; logs search queries and sources; graceful fallback to standard call on error |
| `app/recipes/news_digest.py` | Research step now uses `_call_gemini_grounded()` instead of `_call_gemini()` — fetches real-time news from the web |

**Why this matters**: ChatGPT and Claude use training data that can be weeks or months old. Gemini with Google Search grounding actually runs live web searches, returning up-to-date news articles, stats, and sources. The News Digest recipe is now a real-time research tool, not a rewrite of stale knowledge.

#### B. AI Content Editor

| Component | File | Detail |
|-----------|------|--------|
| **Service** | `app/services/editor_service.py` | `refine_content()` — validates input, builds prompt with brand/persona/history context, calls Gemini, parses response into refined content + explanation |
| **API route** | `app/routes/api.py` | `POST /api/recipes/chat` — JSON endpoint, login required, looks up brand/persona by ID, calls `refine_content()`, returns `{refined_content, explanation}` |
| **Template partial** | `app/templates/recipes/_content_editor.html` | Modal UI — textarea for content, input for instructions, chat history panel, submit with spinner |
| **Integration** | `app/templates/recipes/_run_progress.html` | "Edit with AI" button on every text output; JavaScript handles modal open/close, API calls, history management, content update |
| **Data flow** | `app/routes/recipes.py` | `run_status` now passes `user_brands` and `user_personas` to template so editor can offer brand/persona selection |

**Editor features**:
- Brand-aware: includes colours, voice, hashtags, guidelines in every edit prompt
- Persona-aware: includes tone, bio, voice style, keywords
- Conversational: up to 20 turns of history per session (client-side, no DB writes)
- Input-validated: 50K char content limit, 2K char instruction limit, history sanitisation
- Graceful error handling: user-friendly messages for AI failures, validation errors, unexpected exceptions

### Testing

| Test File | Tests | Coverage |
|-----------|:-----:|----------|
| `tests/test_editor_service.py` | 42 | Input validation (7), history sanitisation (9), prompt building (5), response parsing (4), refine_content (5), Gemini grounding (3), News Digest integration (2), API route (7) |
| `tests/test_news_digest_seo.py` | 5 updated | Fixed to mock `_call_gemini_grounded` instead of `_call_gemini` for research step |

**Results**: 573 total tests, **0 failures**, zero regressions.

### Security
- Login required on `/api/recipes/chat`
- Input length limits prevent abuse (50K content, 2K instruction, 20 history turns)
- History sanitised server-side (role whitelist, text truncation, type checks)
- No PII stored: conversation history lives client-side only
- All existing OWASP protections (CSRF, rate limiting, security headers) remain intact

*Last updated: February 27, 2026 — Phase 40: AI Content Editor + News Digest Grounding*
