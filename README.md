# VideoBuds Video Studio

AI-powered video production platform. Generate talking-head videos, ad creatives, B-roll footage, and social content — all from one dashboard.

**Live at:** [wowly.ai](https://wowly.ai)

---

## Features

- **9 AI Recipes** — ready-to-use content creation workflows
- **Talking Avatar** — upload a photo + script, get a realistic talking-head video with lip-sync
- **Ad Video Maker** — product photos to polished ad videos
- **Image Creator** — AI image generation with multiple models
- **Video Creator** — text/image to video (Kling, Sora, Veo, Seedance, Minimax)
- **Style Cloner** — clone viral video formulas in your brand style
- **Content Machine** — bulk content generation pipeline
- **Brand & Persona System** — AI adapts to your brand voice and visual identity
- **B-Roll Pipeline** — cinematic B-roll clips matching your script and style reference
- **Dark Mode** — toggle between light and dark themes

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python / Flask |
| Frontend | HTMX + Tailwind CSS + Jinja2 |
| Database | SQLite |
| AI Models | Gemini, Kling 3.0, Sora 2, Veo 3.1, Seedance 2.0, Minimax |
| TTS | Gemini TTS (6 voice presets) |
| Talking Head | Higgsfield, WaveSpeed InfiniteTalk, D-ID (4-engine fallback) |
| Image Gen | Nano Banana Pro, GPT Image 1.5 |
| Hosting | Hostinger VPS (Ubuntu 24.04) |

## Recipes

### Active (9)
| Recipe | What It Does |
|--------|-------------|
| Talking Avatar | Photo + script → talking-head video with lip-sync |
| Ad Video Maker | Product images → ad video with music and captions |
| Image Creator | Text prompt → AI-generated images |
| Video Creator | Text/image → AI video (6 models available) |
| Photo to Ad | Single photo → multiple ad creatives |
| Style Cloner | Analyze viral videos → recreate in your brand style |
| Content Machine | Bulk content generation from briefs |
| Influencer Content Kit | Brand brief → influencer-ready content pack |
| News Digest | Topics → researched news summary |

### Coming Soon (5)
Clip Factory, Vertical Reframe, Multi-Scene Video, Motion Capture, Social Scraper

## Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/nabilakhannn/videobuds.git
cd videobuds
pip install -r requirements.txt
```

### 2. Set Up Environment

```bash
cp .env.example .env
```

Fill in your API keys:
- `GOOGLE_API_KEY` — [aistudio.google.com/apikey](https://aistudio.google.com/apikey)
- `WAVESPEED_API_KEY` — [wavespeed.ai](https://wavespeed.ai)
- `HIGGSFIELD_API_KEY_ID` + `HIGGSFIELD_API_KEY_SECRET` — [higgsfield.ai](https://higgsfield.ai)
- `DID_API_KEY` — [studio.d-id.com](https://studio.d-id.com)

### 3. Run

```bash
python run.py
```

Open [localhost:8080](http://localhost:8080)

**Default accounts:**
- Admin: `admin@videobuds.com` / `admin`
- User: `user@videobuds.com` / `user`

## Deployment (VPS)

```bash
ssh root@YOUR_VPS_IP
cd /home/videobuds/app
git pull origin main
sudo systemctl restart videobuds
```

## Tests

```bash
# Unit tests
pytest tests/ -x

# Playwright E2E (requires local server on :8080)
pytest tests/test_e2e_playwright.py -x
```

798 tests passing (709 unit + 89 E2E).

## Project Structure

```
app/
  recipes/        — 14 recipe files (9 active, 5 inactive)
  routes/         — Flask blueprints (auth, dashboard, recipes, API, etc.)
  services/       — model_service, prompt_service, agent_service, editor_service
  templates/      — Jinja2 templates (20+ pages)
  static/         — CSS, JS, images
tools/
  providers/      — wavespeed.py, higgsfield.py, google.py, kie.py, tts.py, did.py
  config.py       — API keys, costs, model registry
  create_image.py — multi-provider image generation
  create_video.py — multi-provider video generation
  video_gen.py    — video generation utilities
  video_analyze.py — Gemini-powered video analysis
tests/            — 798 tests (unit + Playwright E2E)
```

## License

Private — All rights reserved.
