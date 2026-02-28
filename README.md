# 🚀 Creative Content Engine + Blotato — Community Edition

The full AI agent template for creating visual content at scale. Generate images, create videos, build campaigns, automate pipelines, and schedule social media posts — all from a single AI conversation.

**Powered by:** [Google Antigravity](https://antigravity.dev) + [Blotato](https://blotato.com)

**Community:** [RoboNuggets](https://robonuggets.com)

---

## What's Inside

| Folder | What It Does |
|--------|-------------|
| `.agent/` | Agent brain — the instructions, skills, and workflows that make your AI assistant smart |
| `references/` | Your config, docs, brand files, and media files (product images go in `inputs/`) |
| `tools/` | Python scripts for image gen, video gen, video analysis, Airtable, Modal, and more |

### Skills (`.agent/skills/`)
- **Blotato Best Practices** — How to upload media, generate captions, schedule posts, and handle platform-specific requirements
- **Modal Deployment** — Deploy automated pipelines to the cloud with [Modal.com](https://modal.com) (serverless, pay-per-use)

### Workflows (`.agent/workflows/`)
- **30-Day Campaign** — Full brand discovery → content calendar → AI image generation → auto-scheduling pipeline
- **Generate Content** — Detailed content generation workflow with prompt engineering
- **YouTube → LinkedIn** — Automated pipeline: monitor a YouTube channel → extract transcript → generate infographic → post to LinkedIn

### Tools (`tools/`)
- **Image Generation** — Nano Banana / Nano Banana Pro via Google AI Studio or Kie AI
- **Video Generation** — Veo 3.1 (native audio), Kling 3.0 (cinematic), Sora 2 Pro
- **Video Analysis** — Analyze reference videos to extract style, tone, pacing, and prompt notes
- **Airtable Integration** — Use Airtable as your content review hub
- **Modal Pipeline Example** — Ready-to-deploy YouTube → LinkedIn automation (customize for your brand)
- **Provider System** — Multi-provider architecture: Google AI Studio, Kie AI, WaveSpeed AI

### Example Content Included
- **Brand Files** — `fabric_BRAND.md` and `imma_BRAND.md` — real brand guidelines you can study and use as templates
- **Reference Inputs** — Product images and reference videos to test with
- **Example Outputs** — Sample generated images so you can see what the pipeline produces

---

## Quick Start

### 1. Open this folder in Antigravity

Open this folder as a workspace in [Google Antigravity](https://antigravity.dev).

### 2. Install the Blotato MCP Server

Blotato is how your agent posts to social media (Instagram, TikTok, YouTube, LinkedIn, etc.). You need to connect it as an MCP server in Antigravity.

1. Open your MCP config file. In Antigravity, press `Ctrl+Shift+P` → search for **"MCP: Open User Configuration"**
2. Add the following entry inside the `"servers"` object:

```json
"blotato": {
  "serverUrl": "https://mcp.blotato.com/mcp",
  "headers": {
    "blotato-api-key": "YOUR_BLOTATO_API_KEY_HERE"
  }
}
```

3. Replace `YOUR_BLOTATO_API_KEY_HERE` with your Blotato API key (get one at [my.blotato.com](https://my.blotato.com) → API settings)
4. Save the file — the MCP server will connect automatically

### 3. Set Up API Keys

1. Copy `references/.env.example` to `references/.env`
2. Fill in your API keys:
   - **`GOOGLE_API_KEY`** — Free from [aistudio.google.com/apikey](https://aistudio.google.com/apikey) (for Nano Banana Pro images + Veo 3.1 videos)
   - **`KIE_API_KEY`** — From [kie.ai/api-key](https://kie.ai/api-key) (for Kling/Sora videos + file hosting)
   - **`WAVESPEED_API_KEY`** (optional) — From [wavespeed.ai](https://wavespeed.ai) (backup video provider)
   - **`AIRTABLE_API_KEY`** — From [airtable.com/create/tokens](https://airtable.com/create/tokens) (for content management)
   - **`AIRTABLE_BASE_ID`** — From your Airtable base URL
   - **`BLOTATO_API_KEY`** — Same key you used in the MCP config above

### 4. Install Python Dependencies

```
pip install -r tools/requirements.txt
```

### 5. Create Your Airtable Table

```
python tools/setup_airtable.py
```

Or create the table manually — the full schema is in `.agent/AGENT.md`.

### 6. Connect Your Social Accounts in Blotato

Head to [my.blotato.com](https://my.blotato.com) and connect the social media accounts you want to post to (Instagram, TikTok, YouTube, LinkedIn, etc.).

### 7. Start Creating!

Open the Antigravity chat and try:

- **Quick post:** *"Hey, post this image to Instagram and TikTok"* (drop an image in `references/inputs/`)
- **Analyze a reference video:** *"Analyze the Imma videos in references/inputs and tell me the style"*
- **Generate images:** *"Generate 5 UGC-style images for the Fabric jacket using the reference photos"*
- **Generate videos:** *"Create Veo 3.1 videos from the approved images"*
- **Schedule posts:** *"Schedule these images across the next week — one per day starting Monday"*
- **Full campaign:** *"Let's create a 30-day marketing campaign for my product"* (runs the `/30-day-campaign` workflow)
- **Automate:** *"Set up a YouTube → LinkedIn pipeline for my channel using Modal"*

---

## What You Can Do

| Level | Demo | What It Does |
|-------|------|-------------|
| **1** | Multi-platform post | Post a single piece of media to multiple platforms in one command |
| **1** | Scheduled posting | Stagger posts across days/weeks with automatic scheduling |
| **2** | 30-day campaign | Full brand discovery → image generation → auto-scheduling pipeline |
| **2** | Video generation | Create videos from images with Veo 3.1, Kling 3.0, or Sora 2 Pro |
| **2** | Video analysis | Analyze reference videos to extract style for better prompts |
| **3** | YouTube → LinkedIn | Automated cloud pipeline that runs daily on Modal.com |

---

## AI Models Available

| Model | Provider | Best For | Cost/Unit |
|-------|----------|----------|-----------|
| Nano Banana | Google AI Studio | Fast image generation | ~$0.04 |
| Nano Banana Pro | Google AI Studio / Kie AI | High-quality images | ~$0.13 / $0.09 |
| Veo 3.1 | Google AI Studio | Authentic video with native audio/dialogue | ~$0.50 |
| Kling 3.0 | Kie AI / WaveSpeed | Cinematic video | ~$0.30 |
| Sora 2 Pro | Kie AI / WaveSpeed | High-quality, longer video | ~$0.30 |

---

## Customizing the YouTube → LinkedIn Pipeline

The included `tools/modal_pipeline_example.py` is a working template. To set it up for your channel:

1. **Find your YouTube channel ID** — Go to your channel → View Page Source → search for `channelId`
2. **Write your brand voice** — Replace the `BRAND_VOICE` variable with your creator's voice guidelines
3. **Create Modal secrets:**
   ```
   modal secret create youtube-pipeline-secrets \
     GOOGLE_API_KEY=your_key \
     BLOTATO_API_KEY=your_key \
     LINKEDIN_ACCOUNT_ID=your_id
   ```
4. **Deploy:** `modal deploy tools/modal_pipeline_example.py`
5. **Test:** `modal run tools/modal_pipeline_example.py`

---

## Need Help?

- **Community:** Join [RoboNuggets](https://robonuggets.com) for support, tutorials, and live sessions
- **Blotato Docs:** [blotato.com/docs](https://blotato.com/docs)
- **Antigravity:** [antigravity.dev](https://antigravity.dev)

---

*Built with ❤️ for the RoboNuggets community*
