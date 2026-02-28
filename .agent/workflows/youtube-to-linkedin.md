---
description: Automated pipeline that monitors a YouTube channel, extracts transcripts, generates infographics, and posts to LinkedIn on autopilot via Modal.com
---

# YouTube → LinkedIn Automated Content Pipeline

This workflow monitors a YouTube creator's channel, extracts the transcript of their latest video, generates a branded infographic, writes a caption in the creator's voice, and publishes it to LinkedIn — all running daily on autopilot in the cloud.

## What It Produces

For each new video detected:
- ✅ A transcript summary (via Blotato Source API)
- ✅ A branded infographic image (via Nano Banana Pro / Google AI Studio)
- ✅ A LinkedIn post written in the creator's voice (via Gemini + brand.md)
- ✅ Published to LinkedIn with the infographic attached (via Blotato Post API)

---

## Prerequisites

Before starting, you need:

| Requirement | How to Get It |
|------------|--------------|
| **Google API Key** | [aistudio.google.com/apikey](https://aistudio.google.com/apikey) |
| **Blotato API Key** | [my.blotato.com](https://my.blotato.com) → API settings |
| **Blotato LinkedIn Account** | Connect LinkedIn in Blotato, note the `accountId` |
| **YouTube Channel ID** | Find via channel page source (starts with `UC`) |
| **Modal.com account** | [modal.com](https://modal.com) — free tier is enough |

---

## Phase 1: Build the Brand Voice File

The brand voice file is what prevents your posts from sounding like generic AI slop. It captures HOW the creator speaks, not just WHAT they talk about.

### Step 1: Extract Voice Samples

Use Blotato's Source API to pull transcripts from 2-3 of the creator's videos with voice analysis instructions:

```
Tool: blotato_create_source
sourceType: youtube
url: [video URL]
customInstructions: "Analyze the speaker's communication style, tone, vocabulary, 
sentence structure, rhetorical techniques, and personality. Focus on HOW they speak, 
not WHAT they talk about."
```

### Step 2: Create the Brand .md File

From the voice analysis, create a `references/[creator]_brand.md` file containing:

- **Persona description** (e.g., "The Sharp Strategist")
- **Tone characteristics** (formality, confidence, warmth, urgency)
- **Vocabulary patterns** (technical level, signature phrases)
- **Rhetorical techniques** (analogies, frameworks, evidence style)
- **Content pillars** (what topics they cover)
- **What they DON'T do** (anti-patterns to avoid)
- **Platform-specific guidelines** (LinkedIn formatting rules, hashtag strategy)

> **Example:** See `references/nate_jones_brand.md` for a complete reference.

---

## Phase 2: Test the Pipeline Manually

Before automating, run each step manually to verify it works.

### Step 1: Source the Latest Video

// turbo
Browse the creator's YouTube channel or their RSS feed to find the latest video URL:

```
RSS Feed: https://www.youtube.com/feeds/videos.xml?channel_id=[CHANNEL_ID]
```

### Step 2: Extract Transcript

```
Tool: blotato_create_source
sourceType: youtube
url: [video URL]
customInstructions: "Summarize the key points and main takeaways in a concise, 
well-structured format. Focus on core arguments, frameworks, and actionable insights."
```

### Step 3: Generate Infographic

Use Google AI Studio (Nano Banana Pro) to generate an infographic from the summary:

```python
# Key settings:
# Model: gemini-3-pro-image-preview
# Prompt prefix: "4:5." (for LinkedIn aspect ratio)
# Style: Professional, dark background, clean typography
```

The prompt should reference the brand's visual identity — colors, footer with creator name, etc.

### Step 4: Upload Image to Blotato Hosting

Local images need a public URL for social media. Upload via Blotato's media endpoint:

```powershell
$base64 = [Convert]::ToBase64String([IO.File]::ReadAllBytes($imagePath))
$body = @{ url = "data:image/png;base64,$base64" } | ConvertTo-Json
Invoke-RestMethod -Uri "https://backend.blotato.com/v2/media" `
  -Method Post -Headers @{ "blotato-api-key" = $apiKey } `
  -Body $body -ContentType "application/json"
```

### Step 5: Write Caption

Use Gemini with the brand voice embedded in the system prompt. Key formatting rules for LinkedIn:
- Double line breaks (`\n\n`) between every paragraph
- No markdown bold — use emojis (1️⃣) and ALL CAPS for emphasis
- Numbered frameworks for scannability
- End with a reflective question, not a CTA
- Hashtags on their own line at the bottom

### Step 6: Post to LinkedIn

```
Tool: blotato_create_post
accountId: [your LinkedIn account ID]
platform: linkedin
text: [formatted caption]
mediaUrls: [hosted image URL]
```

---

## Phase 3: Deploy to Modal (Autopilot)

Once the manual pipeline works, package it into a Modal app for daily automation.

### Step 1: Install & Authenticate Modal

```powershell
pip install modal
python -m modal setup
```

> On Windows, always use `python -m modal` — the bare `modal` command may not be on PATH.

### Step 2: Create Modal Secret

Store all API keys securely (never hardcode them):

```powershell
python -m modal secret create pipeline-secrets `
  GOOGLE_API_KEY=your_key `
  BLOTATO_API_KEY=your_key `
  LINKEDIN_ACCOUNT_ID=your_id
```

### Step 3: Write the Modal App

The app structure follows this pattern:

```python
import modal

app = modal.App("my-pipeline")
image = modal.Image.debian_slim(python_version="3.11").pip_install("requests", "feedparser")
secret = modal.Secret.from_name("pipeline-secrets")
volume = modal.Volume.from_name("pipeline-state", create_if_missing=True)

@app.function(image=image, secrets=[secret], volumes={"/state": volume}, timeout=600)
def run_pipeline():
    # 1. Check RSS feed for new videos
    # 2. Skip if already processed (check Volume state)
    # 3. Extract transcript (Blotato Source API)
    # 4. Generate infographic (Google AI Studio)
    # 5. Upload to Blotato hosting
    # 6. Write caption (Gemini + brand voice)
    # 7. Post to LinkedIn (Blotato Post API)
    # 8. Save video ID to state + volume.commit()
    pass

@app.function(image=image, secrets=[secret], volumes={"/state": volume},
              schedule=modal.Cron("0 10 * * *"), timeout=600)
def scheduled_run():
    return run_pipeline.local()

@app.local_entrypoint()
def main():
    result = run_pipeline.remote()
    print(result)
```

> **Reference implementation:** See `modal_nate_pipeline.py` for the complete working code.

### Step 4: Deploy

```powershell
python -m modal deploy modal_nate_pipeline.py
```

### Step 5: Verify

```powershell
# Test manually
python -m modal run modal_nate_pipeline.py

# Check logs
python -m modal app logs nate-jones-pipeline

# View in dashboard
# https://modal.com/apps/robonuggets100
```

---

## Adapting This Workflow

This pattern works for any "monitor source → generate content → publish" pipeline:

| Source | Adaptation |
|--------|-----------|
| **TikTok creator** | Change `sourceType` to `tiktok`, adjust brand.md |
| **Blog/Newsletter** | Use `sourceType: article` with the blog's RSS feed |
| **Podcast** | Use `sourceType: audio` with the podcast MP3 URL |
| **Twitter/X thought leader** | Use `sourceType: twitter` with tweet URLs |

| Destination | Adaptation |
|-------------|-----------|
| **Instagram** | Change platform, add `mediaType: "reel"` or carousel images |
| **TikTok** | Change platform, add required TikTok fields (privacyLevel, etc.) |
| **Twitter/X** | Change platform, respect 280-char limit in caption |
| **Multiple platforms** | Call `blotato_create_post` once per platform |

---

## Cost Breakdown

| Component | Cost per Run |
|-----------|-------------|
| Modal compute (~2 min) | ~$0.01 |
| Blotato Source extraction | Free (included in plan) |
| Google AI Studio (Gemini caption) | ~$0.001 |
| Google AI Studio (Nano Banana Pro image) | ~$0.04-0.07 |
| Blotato Post | Free (included in plan) |
| **Total per day** | **~$0.05-0.08** |
| **Total per month (daily)** | **~$1.50-2.40** |
