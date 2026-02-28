# VideoBuds Video Studio — Complete Project Documentation

> Last updated: 2026-02-27 (Sprint: Phase 27 — Brand/Persona Integration Implementation)

---

## What Is VideoBuds?

VideoBuds is an AI-powered video and content creation studio for agency owners and creators. It lets you manage multiple brands, generate AI images and videos, create 30-day social media campaigns, run automated content workflows ("recipes"), and manage brand personas — all from one dashboard.

---

## Login Credentials

| Role | Email | Password | Access |
|------|-------|----------|--------|
| Admin | admin@videobuds.com | admin | Full access + admin dashboard with real costs |
| Test User | user@videobuds.com | user | Standard user view with retail pricing |

---

## How To Run

```bash
# Delete old DB for fresh start (optional)
rm -f videobuds.db

# Start the server
python3 run.py

# Open in browser
http://localhost:8080
```

Server runs on port 8080. Database auto-creates on first run with both accounts seeded.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python Flask |
| Templates | Jinja2 |
| Interactivity | HTMX (no JS framework) |
| Styling | TailwindCSS via CDN (no build step) |
| Database | SQLAlchemy + SQLite (videobuds.db) |
| Auth | Flask-Login |
| Analytics | PostHog (optional, via `POSTHOG_API_KEY`) |
| CSRF | Custom (session-based token + before_request hook) |
| Security | CSRF tokens, rate limiting, HTTP security headers |

---

## Design System

### Colors
| Color | Hex | Used For |
|-------|-----|----------|
| Azure Afternoon | `#26A0D8` | Card borders, dividers, subtle accents |
| Pumpkin Pie | `#F18523` | Primary buttons, links, active nav, sidebar accent |
| Pumpkin Dark | `#D97218` | Button hover states |

### Theme
- **Default**: White/light dashboard
- **Dark mode**: Night black — toggle via sun/moon icon in sidebar footer
- Dark mode saved to localStorage key `vb-dark-mode`
- Anti-flash script in `<head>` prevents white flash on dark mode load

### Light Mode
- Page: `bg-gray-50` | Cards: `bg-white` | Borders: `border-[#26A0D8]/20`
- Headings: `text-gray-900` | Body: `text-gray-700` | Muted: `text-gray-500`

### Dark Mode
- Page: `dark:bg-[#0F0F0F]` | Cards: `dark:bg-[#1E1E1E]` | Borders: `dark:border-[#26A0D8]/40`
- Sidebar: `dark:bg-[#1A1A1A]` | Inputs: `dark:bg-[#141414]`

---

## Features (Completed)

### 1. Authentication
- Login / Register with email + password
- "Remember me" checkbox
- Password confirmation on register
- Auto-seeded admin + test user accounts
- Rate limiting: 15 login attempts / 5 registrations per minute per IP
- PostHog event tracking for login/register

### 2. Brand Management
- Create and manage multiple brands
- Brand questionnaire (AI learns your brand voice, colors, audience)
- Photo library (upload reference images for AI generation)
- Brand switcher in sidebar

### 3. Campaign Builder
- Create 30-day social media campaigns
- Visual calendar grid showing all 30 days
- Click any day to open the post editor (side panel)
- Style presets: Pop Art, Minimalist, Corporate, UGC, Flat Lay, Cinematic
- Mood board with reference image upload
- Custom prompt override option

### 4. AI Image Generation
- Multi-provider architecture (plug and play)
- Providers: Google AI Studio, Kie AI, Higgsfield, WaveSpeed
- Models: Nano Banana, Nano Banana Pro, GPT Image 1.5
- Reference image support for style-guided generation
- Async: submit task → poll for result

### 5. Model Picker & Pricing
- In-editor model picker with per-model retail pricing
- Free tier highlighting (green "FREE" badge)
- Provider sub-selector for models with multiple providers
- Dynamic price badge on Generate button
- Standalone `/pricing` page with all models + providers in a table
- API endpoint: `GET /api/models` (JSON catalog)

### 6. AI Captions & Prompts
- AI-suggested captions (Gemini)
- Prompt enhancement ("Enhance with AI" button)
- Auto-generated image prompts from brand doc + style preset

### 7. Campaign Export
- Download entire campaign as ZIP file
- Includes images + captions

### 8. Admin Dashboard
- Total users, brands, campaigns, generations stats
- Profit summary (retail charged vs actual cost)
- User management table
- "View as User" toggle to preview regular user experience

### 9. Dual Pricing
- Admin sees actual costs ($0 for Google/Higgsfield free tier)
- Users see retail pricing ($0.04–$0.13 per image)
- Tracked per generation in database

### 10. Dark Mode
- Toggle in sidebar footer (sun/moon icon)
- Persists across sessions via localStorage
- All templates + CSS support both modes

### 11. Workflow Recipes System ✅
- **13 recipes** defined with metadata, input fields, step definitions, and how-to-use guides
- Generic UI: one template handles all recipe types
- Recipe Library page (card grid, grouped by category, count badge)
- Recipe Detail page with Markdown-rendered how-to-use guide
- Recipe Run page (dynamic form based on `get_input_fields()`)
- Progress tracking (HTMX polling every 3s, progress bar)
- Results display with inline video players, images, and download links
- Run History page with filtering by recipe and status
- Background thread execution (non-blocking)
- **2-phase execution**: Script generation → approval gate → production (for supported recipes)
- **Script approval UI**: Editable scenes with "Approve & Generate Videos" button
- Database models: `Recipe` (catalog), `RecipeRun` (execution tracking, includes `awaiting_approval` status)
- **Ad Video Maker (R38)** — fully wired with multimodal vision + script approval + asset organization

### 12. AI Personas
- Create brand voice profiles (tone, style, audience, keywords)
- Multi-step creation wizard with AI-generated summaries
- Set default persona for consistent AI output
- Edit, delete, and manage multiple personas per user
- Sidebar link under "You" section

### 13. Script AI Agent
- Research topics and write viral scripts

- Multiple script types: UGC, Tutorial, Vlog, Interview, Product Review, etc.
- Rewrite scripts in user's voice
- Scene decomposition for video production
- Batch script generation

### 14. Security
- **Custom CSRF** — session-based token generation (`generate_csrf_token`) + `before_request` validation on all POST forms
- HTTP security headers (X-Content-Type-Options, X-Frame-Options, etc.)
- Rate limiting on auth routes (15 login / 5 register per minute per IP)
- Server-side file upload validation (extension whitelist)
- Authorization checks (users only access own data)
- 429 error page

### 15. Account Settings & Admin User Management *(Phase 22)*
- **Account Settings** (`/account`): Change display name, email, password
- **Admin User Management** (`/admin/users`): List all users, toggle active/deactivate, delete users
- `User.is_active` column — deactivated users cannot log in
- Admin self-protection — cannot deactivate or delete own account

### 16. Pagination *(Phase 22)*
- Brands list (`/brands/`) — paginated, 12 per page
- Campaigns list (`/campaigns/`) — paginated, 12 per page
- Recipe history already had pagination
- Reusable `_pagination.html` component shared across pages

### 17. Background Bulk Generation *(Phase 22)*
- `generate_campaign` runs in a background thread (not synchronous)
- Campaign status set to `generating` during bulk run
- Each post processed sequentially within the thread
- Campaign status updated to `review` or `draft` upon completion

---

## Ad Video Maker (R38) — Compound Engineering Pipeline

### Architecture: 2-Phase Execution with Script Approval Gate

The Ad Video Maker implements **Compound Engineering** with the **Ralph Loop**
(Research → Analyze → Learn → Plan → Hypothesize) and a mandatory **script approval gate**
between the script and production phases.

### Phase 1: SCRIPT (Research → Analyze → Plan)
1. **Multimodal Vision Analysis** — Gemini **sees** the actual product image (not text-only) via `_call_gemini_with_image`. Outputs detailed product identity: type, colors, materials, features, brand cues.
2. **Product-Anchored Scene Writing** — Every scene description references the EXACT product, its specific colors, materials, and features from the visual analysis.
3. **Status → `awaiting_approval`** — Script outputs saved; user reviews/edits scenes before media generation.

### Phase 2: PRODUCTION (after user approves/edits the script)
4. **Generate Scene Images** — Google Nano Banana Pro creates a hero image per approved scene.
5. **Create Videos** — Google Veo 3.1 turns each image into a short video.
6. **Organise Assets** — All files saved to `references/outputs/run_<id>/` with `metadata.json`.

### Key Technical Details
- **Multimodal Gemini**: `_call_gemini_with_image()` in `agent_service.py` sends image + text to Gemini vision
- **Product anchoring**: Scene prompts injected with full visual analysis, forcing AI to use the EXACT product
- **Approval UI**: `_run_progress.html` displays editable scene fields with "Approve & Generate Videos" button
- **2-phase dispatch**: `execute()` dispatches to `_execute_script()` or `_execute_production()` based on `inputs['_phase']`
- **Asset organization**: Files saved to `references/outputs/run_<id>/` with structured names
- `generate_ugc_video` auto-detects local file paths (swaps `image_url` → `image_path`)
- Google Veo `submit_video` accepts `image_path` for local files (base64 encoded)
- `personGeneration: "allow_adult"` added to Veo requests to prevent RAI filter blocking
- Background thread execution prevents blocking the UI
- Progress callback updates `RecipeRun` status in real-time
- Local video fallback when `KIE_API_KEY` is not set — serves via `/api/outputs/<filename>`
- Graceful error handling — recipe status set to "failed" with clear error message

---

## Video Engine

Located in `tools/` directory. Fully functional via CLI and used by recipes.

### Video Generation (`tools/create_video.py`)
- Single video: `generate_ugc_video(prompt, image_url, image_path, model)`
- Per-record: `generate_for_record(record)` — processes Airtable records
- Batch: `generate_batch(records)` — parallel mixed-provider batches
- Auto-detects local file paths and passes as `image_path` to providers

### Supported Video Models

| Model | Provider | Cost (Retail) | Cost (Actual) |
|-------|----------|--------------|---------------|
| Veo 3.1 | Google AI Studio | $0.50 | $0.00 (free tier) |
| Kling 3.0 | Kie AI / WaveSpeed | $0.30 | $0.30 |
| Sora 2 | WaveSpeed | $0.30 | $0.30 |
| Sora 2 Pro | Kie AI / WaveSpeed | $0.30 | $0.30 |

### Video Analysis (`tools/analyze_video.py`)
- Upload reference UGC video to Gemini Files API
- AI analyzes: hook, person, setting, camera, product interaction, pacing, tone, dialogue, audio, authenticity score
- Returns structured analysis + prompt notes for style replication
- Supports single and multiple video analysis

### Image Models

| Model | Provider | Cost (Retail) | Cost (Actual) |
|-------|----------|--------------|---------------|
| Nano Banana | Google | $0.04 | $0.00 |
| Nano Banana Pro | Google | $0.13 | $0.00 |
| Nano Banana | Kie AI | $0.09 | $0.09 |
| Nano Banana Pro | Higgsfield | $0.13 | $0.00 |
| GPT Image 1.5 | WaveSpeed | $0.07 | $0.07 |

### Provider Architecture (`tools/providers/`)
Each provider module exposes:
- `submit_image()` / `submit_video()` → returns task_id
- `poll_image()` / `poll_video()` → returns `{status, result_url, task_id}`
- `poll_tasks_parallel()` → batch polling with ThreadPoolExecutor
- `image_IS_SYNC` / `video_IS_SYNC` → sync vs async flags

### YouTube-to-LinkedIn Pipeline (`tools/youtube_to_linkedin.py`)
Modal.com serverless automation:
1. Check YouTube RSS for new videos
2. Extract transcript (Blotato)
3. Generate infographic (Nano Banana Pro)
4. Write LinkedIn post in brand voice (Gemini)
5. Auto-publish to LinkedIn (Blotato)
6. Runs daily on cron schedule

---

## Workflow Recipes — All 13 Definitions

### Content Creation
| Recipe | Status | Description |
|--------|--------|-------------|
| 🎬 Ad Video Maker | ✅ Wired | Product photo → UGC-style ad videos |
| 🤳 Influencer Content Kit | Defined | Character + setting → AI influencer posts |
| 🖼️ Image Creator | Defined | Text prompt → AI images with style control |
| 📹 Video Creator | Defined | Text/image → AI videos |
| 📸 Photo-to-Ad | ✅ Wired | Product photo → ad-ready image variations |

### Video Studio
| Recipe | Status | Description |
|--------|--------|-------------|
| 🎭 Talking Avatar | Defined | Blog/script → talking head video |
| 🕺 Motion Capture | Defined | Still image + driving video → animated video |
| 🎞️ Multi-Scene Video | Defined | Script → multi-scene video with transitions |
| 🎨 Style Cloner | Defined | Reference video → style-replicated new video |

### Repurpose / Edit
| Recipe | Status | Description |
|--------|--------|-------------|
| ✂️ Clip Factory | Defined | Long video → short clips with captions |
| 📐 Vertical Reframe | Defined | Horizontal → vertical video reframing |

### Research / Intelligence
| Recipe | Status | Description |
|--------|--------|-------------|
| 🔍 Social Scraper | Defined | Multi-platform social media data extraction |
| 📰 News Digest | ✅ Wired | AI-curated news newsletter (Gemini) |

---

## File Structure

```
r57-template-community/
├── run.py                          # Entry point (port 8080)
├── requirements.txt                # Python dependencies (pip install -r requirements.txt)
├── .gitignore                      # Excludes DB, .env, __pycache__, outputs
├── videobuds.db                    # SQLite database (auto-created, gitignored)
├── VIDEOBUDS.md                    # This file
├── CHANGELOG.md                    # Build log
│
├── app/
│   ├── __init__.py                 # App factory + auto-seed + security + simple_md filter
│   ├── config.py                   # DB path, upload limits, PostHog
│   ├── extensions.py               # SQLAlchemy + LoginManager
│   ├── security.py                 # Security headers, rate limiter, safe_int
│   ├── models/
│   │   ├── __init__.py             # Imports all models
│   │   ├── user.py                 # User model (email, is_admin)
│   │   ├── brand.py                # Brand model (questionnaire, photos)
│   │   ├── campaign.py             # Campaign model
│   │   ├── post.py                 # Post model (day, caption, image, model, provider)
│   │   ├── generation.py           # Generation cost tracking
│   │   ├── reference_image.py      # Reference images for campaigns
│   │   ├── agent_memory.py         # AI agent memory/learning
│   │   ├── user_persona.py         # Brand voice / personality profiles
│   │   ├── recipe.py               # Recipe catalog entries
│   │   └── recipe_run.py           # Recipe execution tracking
│   ├── routes/
│   │   ├── __init__.py             # Blueprint registration
│   │   ├── auth.py                 # Login/register (rate-limited)
│   │   ├── dashboard.py            # Admin + user dashboards + pricing page
│   │   ├── brands.py               # Brand CRUD (/brands/)
│   │   ├── campaigns.py            # Campaign CRUD (/campaigns/)
│   │   ├── posts.py                # Post editor endpoints
│   │   ├── api.py                  # HTMX/AJAX API endpoints + /api/models
│   │   ├── generate.py             # Image generation triggers
│   │   ├── export.py               # Campaign ZIP export
│   │   ├── recipes.py              # Workflow recipes (library/detail/run/history)
│   │   └── personas.py             # AI persona management (CRUD + wizard)
│   ├── recipes/
│   │   ├── __init__.py             # Recipe registry (auto-discovers all recipes)
│   │   ├── base.py                 # BaseRecipe ABC + InputField dataclass
│   │   ├── ad_video_maker.py       # R38 — fully wired ✅
│   │   ├── clip_factory.py         # Clip Factory
│   │   ├── vertical_reframe.py     # Vertical Reframe
│   │   ├── multi_scene_video.py    # Multi-Scene Video
│   │   ├── influencer_content_kit.py # Influencer Content Kit
│   │   ├── image_creator.py        # Image Creator
│   │   ├── video_creator.py        # Video Creator
│   │   ├── social_scraper.py       # Social Scraper
│   │   ├── motion_capture.py       # Motion Capture
│   │   ├── talking_avatar.py       # Talking Avatar
│   │   ├── style_cloner.py         # Style Cloner
│   │   ├── news_digest.py          # News Digest
│   │   └── photo_to_ad.py          # Photo to Ad
│   ├── services/
│   │   ├── agent_service.py        # Gemini AI Creative Director agent + multimodal vision
│   │   ├── cost_service.py         # Cost tracking (actual vs retail)
│   │   ├── analytics_service.py    # PostHog analytics
│   │   ├── model_service.py        # Model catalog + pricing
│   │   ├── prompt_service.py       # Style presets + prompt building logic
│   │   └── script_service.py       # Script AI agent (research + write)
│   ├── templates/
│   │   ├── base.html               # Main layout + sidebar + dark mode
│   │   ├── auth/                   # login.html, register.html, account.html
│   │   ├── dashboard/              # index.html, admin.html, admin_users.html, pricing.html
│   │   ├── brands/                 # list, detail, new, photo_library, questionnaire
│   │   ├── campaigns/              # list, new, calendar, export
│   │   ├── components/             # post_card, post_editor, style_picker, model_picker, _pagination
│   │   ├── recipes/                # library, detail, run, run_status, _run_progress, history
│   │   ├── personas/               # index, wizard, edit
│   │   └── errors/                 # 404, 429, 500
│   └── static/
│       ├── css/custom.css          # Custom styles (post cards, side panel)
│       └── js/                     # calendar.js, generation.js
│
├── tools/                          # Backend AI engines
│   ├── __init__.py                 # Package init
│   ├── config.py                   # API keys, costs, model registry
│   ├── create_video.py             # Video generation (single, batch, local path support)
│   ├── create_image.py             # Image generation orchestrator
│   ├── analyze_video.py            # Reference video analysis (Gemini)
│   ├── upload_to_kie.py            # File upload to Kie hosting
│   ├── airtable.py                 # Airtable integration
│   ├── youtube_to_linkedin.py      # YouTube→LinkedIn automation (Modal)
│   ├── setup_airtable.py           # Airtable schema setup utility
│   ├── utils.py                    # Shared helpers
│   └── providers/
│       ├── __init__.py             # Provider registry + routing
│       ├── google.py               # Google AI Studio (Veo + Nano Banana)
│       ├── kie.py                  # Kie AI (Kling, Sora, Nano Banana)
│       ├── wavespeed.py            # WaveSpeed (Kling, Sora, GPT Image)
│       └── higgsfield.py           # Higgsfield (Nano Banana)
│
├── Json templates/                 # 11 n8n workflow JSONs (reference)
└── references/
    ├── .env                        # API keys (gitignored)
    └── docs/                       # Brand docs, guides
```

---

## API Keys Required (in references/.env)

```env
# Image/Video Generation
GOOGLE_API_KEY=           # Google AI Studio (Veo, Nano Banana) — FREE TIER
KIE_API_KEY=              # Kie AI (Kling, Sora, Nano Banana)
WAVESPEED_API_KEY=        # WaveSpeed (Kling, Sora, GPT Image, Avatars)
HIGGSFIELD_API_KEY_ID=    # Higgsfield Key ID
HIGGSFIELD_API_KEY_SECRET= # Higgsfield Key Secret

# Content Management
AIRTABLE_API_KEY=         # Airtable (batch video workflows)
AIRTABLE_BASE_ID=         # Airtable base ID

# Analytics (optional)
POSTHOG_API_KEY=          # PostHog analytics
POSTHOG_HOST=             # PostHog host
```

---

## Important Routing Notes

### Auth (no url_prefix)
| Route | Method | Notes |
|-------|--------|-------|
| `/login` | GET/POST | Login page with rate limiting |
| `/register` | GET/POST | Registration with rate limiting |
| `/logout` | GET | Logout + redirect |
| `/account` | GET/POST | Account settings (change name, email, password) |

### Dashboard
| Route | Method | Notes |
|-------|--------|-------|
| `/` | GET | Dashboard (requires login) |
| `/admin` | GET | Admin dashboard (is_admin only) |
| `/admin/users` | GET | Admin user management list |
| `/admin/users/<id>/toggle` | POST | Toggle user active/deactivate |
| `/admin/users/<id>/delete` | POST | Delete user |
| `/pricing` | GET | Standalone pricing page |

### Brands (`/brands/`)
| Route | Method | Notes |
|-------|--------|-------|
| `/brands/` | GET | List brands (paginated) — trailing slash required |
| `/brands/` | POST | Create brand |
| `/brands/new` | GET | New brand form |
| `/brands/<id>` | GET | Brand detail/edit page |
| `/brands/<id>` | POST | Update brand |
| `/brands/<id>` | DELETE | Delete brand (returns JSON) |
| `/brands/<id>/activate` | POST | Set brand as active |
| `/brands/<id>/photos` | GET | Photo library for brand |
| `/brands/<id>/generate-doc` | POST | Auto-generate brand document |
| `/brands/questionnaire` | GET/POST | AI-guided brand questionnaire |

### Campaigns (`/campaigns/`)
| Route | Method | Notes |
|-------|--------|-------|
| `/campaigns/` | GET | List campaigns (paginated) — trailing slash required |
| `/campaigns/` | POST | Create campaign |
| `/campaigns/new` | GET | New campaign form |
| `/campaigns/<id>/calendar` | GET | Calendar grid view |
| `/campaigns/<id>/delete` | POST | Delete campaign |
| `/campaigns/<id>/posts/<day>` | GET | HTMX post editor (side panel) |
| `/campaigns/<id>/posts/<day>` | POST | Update post |

### Export (`/export/`)
| Route | Method | Notes |
|-------|--------|-------|
| `/export/campaigns/<id>` | GET | Export preview page |
| `/export/campaigns/<id>` | POST | Download campaign ZIP |

### Recipes (`/recipes/`)
| Route | Method | Notes |
|-------|--------|-------|
| `/recipes/` | GET | Workflow Library |
| `/recipes/<slug>/` | GET | Recipe detail page |
| `/recipes/<slug>/run/` | GET/POST | Run a recipe |
| `/recipes/run/<id>/status` | GET | Poll run progress (HTMX) |
| `/recipes/run/<id>/approve` | POST | Approve script → launch Phase 2 |
| `/recipes/run/<id>/status.json` | GET | Run progress JSON |
| `/recipes/history/` | GET | Past runs (paginated) |

### Personas (`/personas/`)
| Route | Method | Notes |
|-------|--------|-------|
| `/personas/` | GET | List personas |
| `/personas/new` | GET/POST | Multi-step wizard |
| `/personas/<id>/edit` | GET/POST | Edit persona |
| `/personas/<id>/delete` | POST | Delete persona |
| `/personas/<id>/set-default` | POST | Set as default |

### API (`/api/`)
| Route | Method | Notes |
|-------|--------|-------|
| `/api/models` | GET | Model catalog JSON endpoint |
| `/api/outputs/<filename>` | GET | Serve generated output files (images, videos) |
| `/api/brands/switch` | POST | Switch active brand (HTMX) |
| `/api/prompt/preview` | POST | AI prompt preview (HTMX) |
| `/api/references/upload` | POST | Upload reference image to campaign |
| `/api/references/<id>/delete` | POST | Delete reference image |
| `/api/brands/<id>/photos/upload` | POST | Upload photo to brand library |
| `/api/brands/<id>/photos` | DELETE | Delete brand photo |
| `/api/campaigns/<id>/stats` | GET | Campaign stats JSON |

### Generate (`/generate/`)
| Route | Method | Notes |
|-------|--------|-------|
| `/generate/<post_id>` | POST | Generate image for single post |
| `/generate/campaign/<id>` | POST | Bulk generate (async background thread) |
| `/generate/day/<campaign_id>/<day>` | POST | Generate for specific day |

---

## Database Models

### User (`app/models/user.py`)
- email, password_hash, display_name, is_admin, **is_active** (Boolean, default=True)
- last_login_at, created_at
- Relationships: brands, campaigns, personas, recipe_runs
- Methods: `set_password()`, `check_password()` (werkzeug pbkdf2:sha256)

### Brand (`app/models/brand.py`)
- name, user_id, is_active, tagline, visual_style, target_audience, never_do
- content_pillars (JSON string), colors_json (JSON string), hashtags (JSON string)
- brand_doc (text — AI-generated brand guidelines), caption_template
- Property: `colors` (parsed from colors_json), `pillars` (parsed from content_pillars)

### BrandQuestionnaire (`app/models/questionnaire.py`)
- brand_id (FK), question_key, answer
- Stores individual answers from the brand questionnaire wizard

### Campaign (`app/models/campaign.py`)
- name, brand_id, user_id, start_date, end_date
- style_preset, intention, post_count, status
- generated_count, total_cost, created_at

### Post (`app/models/post.py`)
- campaign_id, day_number, scheduled_date, caption, image_url, status
- style_preset, custom_prompt, image_prompt, content_pillar, image_type
- model, provider (selected AI model for generation)

### Generation (`app/models/generation.py`)
- user_id, model, provider, cost (actual), retail_cost, created_at

### ReferenceImage (`app/models/reference_image.py`)
- campaign_id, brand_id, user_id, file_path, file_name, purpose
- Supports both campaign-level and brand-level reference images

### AgentMemory (`app/models/agent_memory.py`)
- user_id, brand_id, memory_type, content_json

### UserPersona (`app/models/user_persona.py`)
- user_id, name, is_default, tone, voice_style, bio, industry
- target_audience, brand_keywords (JSON), avoid_words (JSON)
- sample_phrases (JSON), writing_guidelines, ai_prompt_summary

### Recipe (`app/models/recipe.py`)
- slug, name, description, category, icon, is_enabled
- usage_count, estimated_cost_label

### RecipeRun (`app/models/recipe_run.py`)
- recipe_id, user_id, brand_id, persona_id
- status (pending/running/awaiting_approval/completed/failed/cancelled)
- steps_completed, total_steps, current_step_label
- inputs (JSON), outputs (JSON), error_message
- cost, retail_cost, model_used
- started_at, completed_at, created_at

---

## Services Documentation

### `agent_service.py` — Gemini AI Creative Director
Key functions:
- `analyze_brand(brand, ...)` — Deep brand analysis using Gemini (text or multimodal)
- `plan_campaign(brand, campaign)` — Fill captions + scene descriptions for all posts
- `write_captions(brand, posts)` — Generate social media captions
- `build_smart_prompt(brand, post)` — AI-enhanced image prompts
- `learn_from_feedback(brand, feedback)` — Store user feedback in AgentMemory
- `select_photos(brand, campaign)` — Select best reference photos for generation
- `_call_gemini(prompt, model)` — Direct Gemini text call (used internally + by recipes)
- `_call_gemini_with_image(prompt, image_path, model)` — **Multimodal** Gemini call (image + text)

### `prompt_service.py` — Style Presets & Prompt Building
- `build_prompt(style_preset, brand, post)` — Constructs image prompts from style + brand doc + post context
- Style presets: Pop Art, Minimalist, Corporate, UGC, Flat Lay, Cinematic
- Each preset defines base prompt template, negative prompt, recommended aspect ratio

### `model_service.py` — Model Catalog & Pricing
- `get_image_models()` / `get_video_models()` — Return model lists with pricing
- `get_all_models()` — Combined catalog for pricing page
- Free tier models sorted to top

### `cost_service.py` — Cost Tracking
- `record_generation(user_id, model, provider)` — Tracks actual vs retail cost per generation

### `analytics_service.py` — PostHog Events
- `track(user_id, event, properties)` — Send events to PostHog (if API key set)

### `script_service.py` — Script AI Agent
- `research_topic(topic)` — Research using Gemini
- `write_script(topic, script_type, voice)` — Write scripts in multiple formats
- Script types: UGC, Tutorial, Vlog, Interview, Product Review, etc.

---

## Continuity Notes (for resuming in a new CLI)

### Current State (2026-02-27)
- **Server**: Runs on port 8080 (`python3 run.py`)
- **Database**: `videobuds.db` — auto-creates with seeded accounts on first run
- **Dependencies**: `pip install -r requirements.txt`
- **Real user account**: `bestify4u@gmail.com` (user_id=4) has recipe runs in history
- **Seeded accounts**: `admin@videobuds.com` / `admin`, `user@videobuds.com` / `user`
  - ⚠️ If DB was created before rebrand, admin email may still be `admin@scalebuds.com`
- **Generated assets**: Stored in `references/outputs/` — served via `/api/outputs/<filename>`
- **Organized run assets**: Each recipe run saves to `references/outputs/run_<id>/`

### What Was Completed (Phases 19–26)
**Phase 19 — Compound Engineering & Ralph Loop**
1. ✅ Multimodal Gemini — AI now SEES product images (not text-only analysis)
2. ✅ 2-Phase Execution — Script → approval gate → production
3. ✅ Product-Anchored Prompts — Scenes reference exact product from vision analysis
4. ✅ Script Approval UI — Editable scenes, approve button, re-run support
5. ✅ Asset Organization — Structured `run_<id>/` directories with metadata.json

**Phase 20 — Polish, Security Hardening & Gap Analysis**
6. ✅ Security Audit — Auth, authz, CSRF, rate limiting, headers, safe filter ✓
7. ✅ E2E Compile Check — All routes + recipes verified
8. ✅ SOLID Refactor — Single responsibility per phase, clean interfaces
9. ✅ Bug Fixes — KIE_API_KEY fallback, Veo RAI filters, 404 downloads, history URLs
10. ✅ Clean Text Outputs — `simple_md` Jinja filter renders markdown in all AI output areas
11. ✅ Video Gen Path Fix — `/api/outputs/` paths resolved to local files for video gen input
12. ✅ SQLite DB Fix — Resolved macOS quarantine-related readonly database error

**Phase 21 — News Digest Recipe**
13. ✅ News Digest wired — Gemini researches + summarises + formats digest

**Phase 22 — Bug Fixes, Missing Features & Hardening**
14. ✅ Custom CSRF — Session-based token generation + `before_request` validation on all POST forms
15. ✅ `.gitignore` — Excludes DB, .env, __pycache__, outputs
16. ✅ `requirements.txt` — All Python dependencies listed
17. ✅ Account Settings page — Change name, email, password
18. ✅ Admin User Management — List, toggle active/deactivate, delete users
19. ✅ `User.is_active` column — Deactivated users cannot log in
20. ✅ Async Bulk Generation — `generate_campaign` runs in background thread
21. ✅ Pagination — Brands + Campaigns lists paginated (12 per page)
22. ✅ Stub Recipes — 11 stubs now return "Coming Soon" (not NotImplementedError)
23. ✅ Full routing documentation — All routes documented in VIDEOBUDS.md

**Phase 23 — Photo to Ad Recipe Wiring**
24. ✅ Photo to Ad fully wired — 2-phase Compound Engineering (vision analysis → approval → image/video gen)
25. ✅ Multimodal product analysis — Same pattern as Ad Video Maker
26. ✅ Full input support — product_photo, tagline, output_type (images/videos/both), variations (1/3/5)

**Phase 24 — Video Quality & Playback Fixes**
27. ✅ Video duration fix — Changed from 5s (snapped to 4s) to 8s for proper ad-length videos
28. ✅ Moov atom faststart — `_faststart()` runs `ffmpeg -movflags +faststart` after every download
29. ✅ Playsinline attribute — Added to `<video>` tag for iOS Safari inline playback

**Phase 25 — Photo Library Upload Fix**
30. ✅ CSRF bypass for AJAX — Added `X-Requested-With: XMLHttpRequest` to all `fetch()` POST calls
31. ✅ Error feedback — Upload and delete failures now show user-facing alert messages

**Phase 26 — Brand/Persona Gap Analysis & Integration Plan**
32. ✅ Gap analysis documented — 5 gaps identified in brand/persona/recipe integration
33. ✅ Action plan created — 3-phase (A/B/C), 6-task plan in `project-status.md`

**Phase 27 — Brand/Persona Integration Implementation**
34. ✅ Brand/Persona dropdowns added to recipe run form (`run.html`) — both optional selects populated from `current_user`'s brands/personas
35. ✅ `BaseRecipe.execute()` signature updated — now accepts `brand=None, persona=None`
36. ✅ Recipe routes updated — `_execute_recipe` and `_launch_recipe_execution` fetch Brand/Persona from DB and pass to `execute()`; `approve_script` also forwards brand/persona for Phase 2
37. ✅ `build_brand_context()` and `build_persona_context()` static helpers on `BaseRecipe` — generate prompt-injection blocks from Brand/Persona objects
38. ✅ `get_brand_reference_paths()` static helper on `BaseRecipe` — returns local file paths from brand's photo library filtered by purpose
39. ✅ Ad Video Maker prompt injection — brand voice, target audience, guidelines + persona tone, keywords, voice style injected into scene-writing prompt; brand product photos auto-added as reference images in production phase
40. ✅ Photo to Ad prompt injection — same brand/persona context injected into concept-writing prompt; brand product photos auto-added as reference images
41. ✅ Brand Voice section added to brand detail page — sidebar card listing user's personas with links, "Default" badge, and "New Persona" button

### What's Next
- Wire remaining 10 recipe `execute()` methods (Ad Video Maker, Photo to Ad, News Digest are done)
- Vercel deployment: custom domain, web analytics, speed insights
- Ralph Loop learning: store user feedback on approved/rejected scripts
- Content Repurposer pipeline (Clip Factory, Vertical Reframe)
- Social Publisher integration

### Known Issues
- Seeded admin email may be `admin@scalebuds.com` if DB was created before rebrand — delete `videobuds.db` and restart for fresh seed
- macOS quarantine attributes on `videobuds.db` can cause readonly errors — delete and let app recreate
- `KIE_API_KEY` not set: videos saved locally and served via `/api/outputs/` (no external hosting)
- 10 stub recipes return "Coming Soon" — Ad Video Maker, Photo to Ad, and News Digest are fully wired
