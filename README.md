# VideoBuds Video Studio

AI-powered video production platform for agencies and creators. Generate talking-head videos, ad creatives, B-roll footage, and social content — all from one dashboard.

**Live:** [wowly.ai](https://wowly.ai)

---

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Quick Start](#quick-start)
- [Environment Variables](#environment-variables)
- [Recipes](#recipes)
- [Project Structure](#project-structure)
- [Testing](#testing)
- [Deployment](#deployment)
- [Design System](#design-system)
- [License](#license)

---

## Features

- **9 AI Recipes** — ready-to-use content creation workflows
- **Talking Avatar** — upload a photo + script, get a realistic talking-head video with lip-sync
- **Ad Video Maker** — product photos to polished ad videos
- **Image Creator** — AI image generation with multiple models
- **Video Creator** — text/image to video (Kling 3.0, Sora 2, Veo 3.1, Seedance 2.0, Minimax)
- **Style Cloner** — clone viral video formulas in your brand style
- **Content Machine** — bulk content generation pipeline
- **Brand & Persona System** — AI adapts to your brand voice and visual identity
- **B-Roll Pipeline** — cinematic B-roll clips matching your script and style reference
- **Dark Mode** — toggle between light and dark themes
- **Campaign Manager** — 30-day social media campaign generation
- **HTMX-powered UI** — fast, no-framework frontend with Tailwind CSS

---

## Tech Stack

| Layer         | Technology                                                    |
| ------------- | ------------------------------------------------------------- |
| Backend       | Python 3.11+ / Flask 3.1                                     |
| Frontend      | HTMX + Tailwind CSS + Jinja2 (no JS framework, no build step)|
| Database      | SQLAlchemy + SQLite (file-based, auto-created)                |
| Auth          | Flask-Login (session-based)                                   |
| AI Models     | Gemini, Kling 3.0, Sora 2, Veo 3.1, Seedance 2.0, Minimax   |
| TTS           | Gemini TTS (6 voice presets)                                  |
| Talking Head  | Higgsfield, WaveSpeed InfiniteTalk, D-ID (4-engine fallback)  |
| Image Gen     | Nano Banana Pro, GPT Image 1.5                                |
| Analytics     | PostHog (optional)                                            |
| Security      | CSRF tokens, rate limiting, OWASP file-upload validation      |
| Hosting       | Hostinger VPS (Ubuntu 24.04) / Railway                        |

---

## Quick Start

### 1. Clone and install

```bash
git clone https://github.com/nabilakhannn/videobuds.git
cd videobuds
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env and add your API keys (minimum: GOOGLE_API_KEY)
```

### 3. Run

```bash
python run.py
```

Open [localhost:8080](http://localhost:8080).

**Default accounts** (auto-seeded on first run):

| Role  | Email                  | Password |
| ----- | ---------------------- | -------- |
| Admin | `admin@videobuds.com`  | `admin`  |
| User  | `user@videobuds.com`   | `user`   |

---

## Environment Variables

Copy `.env.example` to `.env` and fill in:

| Variable                      | Required | Source                                                         |
| ----------------------------- | -------- | -------------------------------------------------------------- |
| `SECRET_KEY`                  | Yes      | `python -c "import secrets; print(secrets.token_hex(32))"`     |
| `GOOGLE_API_KEY`              | Yes      | [aistudio.google.com/apikey](https://aistudio.google.com/apikey)|
| `WAVESPEED_API_KEY`           | No       | [wavespeed.ai](https://wavespeed.ai)                           |
| `HIGGSFIELD_API_KEY_ID`       | No       | [higgsfield.ai](https://higgsfield.ai)                         |
| `HIGGSFIELD_API_KEY_SECRET`   | No       | [higgsfield.ai](https://higgsfield.ai)                         |
| `DID_API_KEY`                 | No       | [studio.d-id.com](https://studio.d-id.com)                     |
| `KIE_API_KEY`                 | No       | Optional — Kie AI provider                                     |
| `POSTHOG_API_KEY`             | No       | Optional — analytics                                           |

---

## Recipes

### Active (9)

| Recipe                 | What It Does                                              |
| ---------------------- | --------------------------------------------------------- |
| Talking Avatar         | Photo + script → talking-head video with lip-sync         |
| Ad Video Maker         | Product images → ad video with music and captions         |
| Image Creator          | Text prompt → AI-generated images                         |
| Video Creator          | Text/image → AI video (6 models available)                |
| Photo to Ad            | Single photo → multiple ad creatives                      |
| Style Cloner           | Analyze viral videos → recreate in your brand style       |
| Content Machine        | Bulk content generation from briefs                       |
| Influencer Content Kit | Brand brief → influencer-ready content pack               |
| News Digest            | Topics → researched news summary                          |

### Coming Soon (5)

Clip Factory, Vertical Reframe, Multi-Scene Video, Motion Capture, Social Scraper

---

## Project Structure

```
videobuds/
├── app/                        # Flask application
│   ├── __init__.py             # create_app() factory
│   ├── config.py               # Flask config classes
│   ├── extensions.py           # SQLAlchemy, LoginManager
│   ├── security.py             # OWASP security (CSRF, rate limiting, uploads)
│   ├── models/                 # 11 SQLAlchemy models
│   ├── routes/                 # 10 Flask blueprints
│   ├── recipes/                # 14 recipe files (9 active, 5 stub)
│   │   └── base.py             # BaseRecipe with brand/persona context
│   ├── services/               # Business logic (agent, model, prompt, editor)
│   ├── templates/              # 36+ Jinja2 templates
│   └── static/                 # CSS, JS, images
│
├── tools/                      # AI generation tools (standalone)
│   ├── config.py               # API keys, costs, model registry
│   ├── providers/              # Per-provider modules
│   │   ├── google.py           # Gemini
│   │   ├── kie.py              # Kie AI
│   │   ├── wavespeed.py        # WaveSpeed
│   │   ├── higgsfield.py       # Higgsfield
│   │   ├── did.py              # D-ID
│   │   └── tts.py              # Text-to-speech
│   ├── create_image.py         # Multi-provider image generation
│   ├── create_video.py         # Multi-provider video generation
│   ├── video_gen.py            # Video generation utilities
│   └── video_analyze.py        # Gemini-powered video analysis
│
├── tests/                      # Test suite (798 tests)
│   ├── conftest.py             # Safety guards (blocks db.drop_all on prod)
│   ├── test_e2e_playwright.py  # Playwright E2E tests
│   └── ...                     # Unit + integration tests
│
├── deploy/
│   └── setup-vps.sh            # Hostinger VPS deployment script
│
├── examples/                   # Sample images and screenshots
├── references/                 # Runtime data (inputs/outputs)
│
├── .env.example                # Environment variable template
├── requirements.txt            # Python dependencies
├── Procfile                    # Gunicorn process file
├── run.py                      # Dev server entry point (port 8080)
├── CHANGELOG.md                # Full build log (all phases)
├── VIDEOBUDS.md                # Detailed project documentation
└── project-status.md           # Phase completion tracker
```

---

## Testing

```bash
# Run all unit tests
pytest tests/ --ignore=tests/test_e2e_playwright.py -x

# Run Playwright E2E tests (requires server running on :8080)
pytest tests/test_e2e_playwright.py -x
```

**Current count:** 798 tests (709 unit + 89 E2E)

Tests use an in-memory SQLite database. The `conftest.py` safety guard blocks `db.drop_all()` on file-backed databases to prevent accidental data loss.

---

## Deployment

### VPS (Hostinger)

```bash
# First-time setup
scp deploy/setup-vps.sh root@YOUR_VPS_IP:/tmp/
ssh root@YOUR_VPS_IP
bash /tmp/setup-vps.sh

# Updates
ssh root@YOUR_VPS_IP
cd /home/videobuds/app
git pull origin main
sudo systemctl restart videobuds
```

### Railway / Render

The included `Procfile` and `requirements.txt` work out of the box:

```
web: gunicorn app:create_app()
```

Set `DATABASE_URL` to your PostgreSQL connection string if using Postgres.

---

## Design System

| Token            | Light Mode          | Dark Mode                |
| ---------------- | ------------------- | ------------------------ |
| Primary action   | `#F18523` (orange)  | `#F18523`                |
| Accent / borders | `#26A0D8` (azure)   | `#26A0D8/40`             |
| Page background  | `bg-gray-50`        | `bg-[#0F0F0F]`           |
| Card background  | `bg-white`          | `bg-[#1E1E1E]`           |
| Sidebar          | `bg-white`          | `bg-[#1A1A1A]`           |

Dark mode toggles via the sun/moon icon in the sidebar footer. Preference is saved to `localStorage`.

---

## License

Private — All rights reserved.
