---
description: Create a 30-day marketing campaign with daily scheduled posts — from brand discovery to autopilot
---

# 30-Day Marketing Campaign Workflow

This workflow creates a complete 30-day content calendar with unique AI-generated images and brand-voice captions, then schedules them one-per-day on autopilot via Blotato.

---

## Prerequisites

- Blotato account connected with at least one social media platform
- `BLOTATO_API_KEY` set in `.env`
- Airtable configured (API key, base ID, Content table created)
- A `references/[brandname]_BRAND.md` file (created in Phase 1 if it doesn't exist)

---

## Phase 1: Brand Discovery → `brand.md`

**Goal:** Create a `references/[brandname]_BRAND.md` file that captures the brand's voice, values, audience, and visual identity. This file is the foundation for all content.

### Option A: Interview Method (Steven Bartlett Style)

If no brand.md exists yet, conduct a deep-dive interview. Ask the user these questions **one at a time**, building on their answers like a podcast host:

**Round 1 — Identity**
1. "What does your brand actually DO — in one sentence, like you're telling a stranger at a bar?"
2. "Who is the ONE person you're really talking to? Not a demographic — give me a real person. What keeps them up at night?"
3. "If your brand were a person at a dinner party, how would they talk? Formal? Casual? Provocative? Warm?"

**Round 2 — Values & Differentiation**
4. "What do you believe that most people in your industry would disagree with?"
5. "What's the FEELING you want someone to have after consuming your content?"
6. "Name 3 brands or creators whose style you admire — and tell me WHY for each one."

**Round 3 — Visual & Content Identity**
7. "Describe your ideal aesthetic in 3 words. If your brand were a movie set, what would it look like?"
8. "What content pillars do you keep coming back to? The 3-5 topics you could talk about forever?"
9. "What does your brand NEVER do? What's off-limits in tone, content, or style?"

**Round 4 — Goals & Platform**
10. "What platforms are you focusing on, and what does success look like in 30 days?"

After the interview, write `references/[brandname]_BRAND.md` using the template below.

### Option B: Content Analysis Method

If the user provides existing content (posts, videos, images, website):

1. **Analyze the content** — Use `mcp_blotato_blotato_create_source` to extract content from URLs:
   - YouTube videos → extract transcript, analyze speaking style
   - Articles/blog posts → extract voice, recurring themes
   - Social media posts → identify patterns, hashtags, engagement style

2. **Study visual patterns** — If images are provided, use `view_file` to analyze:
   - Color palette
   - Photography style (lifestyle, product, minimalist, etc.)
   - Typography preferences
   - Recurring visual elements

3. **Synthesize into brand.md** using the same template below.

### Brand.md Template

Write the file to `references/[brandname]_BRAND.md` with this structure:

```markdown
# [Brand Name] — Brand Voice & Style Guide

## Who We Are
- One-sentence mission
- Core product/service
- Stage of business (startup, growing, established)

## Target Audience
- **The Person:** [Name a specific archetype]
- **Their Pain:** What keeps them up at night
- **Their Desire:** What transformation they want
- **Where they hang out:** Platforms, communities

## Tone & Voice
| Attribute    | Description |
|------------- |-------------|
| Formality    | [e.g., Professional-casual] |
| Energy       | [e.g., High-energy, calm authority] |
| Humor        | [e.g., Witty one-liners, no humor, sarcastic] |
| Warmth       | [e.g., Direct but encouraging] |

### Signature Phrases
- [Any catchphrases, recurring language patterns]

### What We NEVER Do
- ❌ [Off-limits tones, topics, styles]

## Visual Identity
- **Color Palette:** [Primary, secondary, accent colors]
- **Aesthetic:** [3 words, e.g., "clean, bold, futuristic"]
- **Photography Style:** [e.g., lifestyle, studio, UGC-style]
- **Typography Feel:** [e.g., modern sans-serif, elegant serif]

## Content Pillars
1. [Pillar 1 — topic + why it matters]
2. [Pillar 2]
3. [Pillar 3]
4. [Pillar 4 — optional]
5. [Pillar 5 — optional]

## Platform Strategy
- **Primary:** [Platform] — [posting frequency, content type]
- **Secondary:** [Platform] — [adapted approach]

## Inspirations
- [Brand/Creator 1] — what we take from them
- [Brand/Creator 2]
- [Brand/Creator 3]
```

---

## Phase 2: Create the 30-Day Content Calendar in Airtable

**Goal:** Create 30 records in Airtable — each with a unique Image Prompt, Caption, and Scheduled Date. The user reviews everything in Airtable BEFORE any images are generated.

### Step 2.1: Read the Brand File

```
Read references/[brandname]_BRAND.md to understand the brand's voice, audience, pillars, and visual style.
```

### Step 2.2: Upload Reference Images

Upload the product reference image(s) to Kie.ai so they can be attached to every Airtable record:

```python
python -c "
import sys; sys.path.insert(0, '.')
from dotenv import load_dotenv; load_dotenv('references/.env')
from tools.kie_upload import upload_references
ref_urls = upload_references(['references/inputs/product.jpg'])
f = open('references/outputs/ref_urls.txt', 'w'); f.write('\n'.join(ref_urls)); f.close()
print('Reference URLs saved.')
"
```

### Step 2.3: Plan the 30 Posts

Design 30 unique posts that:

1. **Rotate through content pillars** — don't stack the same topic multiple days in a row
2. **Mix image types** across the 30 days:
   - 🤳 **UGC / Selfie** (~8 posts) — person filming themselves, phone-in-hand, natural lighting
   - 📸 **Studio Hero Shot** (~7 posts) — model on grey/concrete backdrop, moody lighting, power stance
   - 🔍 **Close-up Detail** (~5 posts) — extreme close-up on fabric, stitching, hardware, graphics
   - 🌆 **Urban Lifestyle** (~5 posts) — walking through gritty city streets, rooftops, parking garages
   - 🎨 **CGI/World-Building** (~3 posts) — futuristic rendered scenes matching brand aesthetic
   - 📦 **Flat Lay / Product** (~2 posts) — product laid out with accessories on textured surface

3. **Follow a weekly rhythm** (example):
   - **Monday:** Motivational / Brand statement
   - **Tuesday:** Product detail close-up
   - **Wednesday:** UGC selfie-style
   - **Thursday:** Studio hero shot
   - **Friday:** Urban lifestyle
   - **Saturday:** World-building / CGI
   - **Sunday:** Community engagement

4. **Write brand-voice captions** following the brand file's caption guidelines:
   - Include relevant emojis (from brand guide)
   - Include 2-3 hashtags (from brand guide)
   - Include a CTA (call-to-action)
   - Match the tone exactly

### Step 2.4: Create 30 Airtable Records

Use `create_records_batch` to create all 30 records. Each record gets:

```python
{
    "Index": start_index + i,
    "Ad Name": "Reaper - Day 1 - UGC Selfie",
    "Product": "Reaper Bomber Jacket",
    "Reference Images": [{"url": ref_url}],
    "Image Prompt": "9:16. A young man in a dark bedroom mirror selfie...",
    "Image Model": "Nano Banana Pro",
    "Image Status": "Pending",
    "Caption": "Full tactical. Zero compromises 🖤\n\nReaper drops March 1st, 2026. fabricoftheuniverse.com\n\n#darkwear #techwearfit #fbrc",
    "Scheduled Date": "2026-02-25T10:00:00+11:00",
}
```

**IMPORTANT:** Increment `Scheduled Date` by 1 day for each record (Day 1 = start date, Day 30 = start date + 29 days).

### Step 2.5: Review Checkpoint

**STOP and tell the user to review everything in Airtable.**

Show:
- A summary of the image type distribution (e.g., "UGC: 8, Studio: 7, Detail: 5...")
- 3-5 sample captions with their prompts
- The date range (start → end)

Ask: "I've created all 30 records in Airtable with prompts, captions, and scheduled dates. Head over to Airtable to review them — you can edit any captions or prompts before I generate the images. Let me know when you're happy with everything!"

**Do NOT proceed to image generation until the user approves.**

---

## Phase 3: Generate All 30 Images

**Goal:** Generate unique images for each of the 30 Airtable records using Nano Banana Pro via Google AI Studio.

### Step 3.1: Cost Estimate

Before generating, show the cost:
- **30 images × $0.13 each = ~$3.90 total** (Nano Banana Pro via Google)
- **2 variations per record = 60 images total = ~$7.80** (if doing 2 variations)
- Estimated time: ~60-90 minutes for all 30 records

Ask: "This will generate 30 images using Nano Banana Pro (Google AI Studio) at ~$0.13 each. Total cost: ~$3.90 for 1 variation per record, or ~$7.80 for 2 variations. Which would you prefer?"

### Step 3.2: Generate Images

Use the existing image generation pipeline:

```python
import sys; sys.path.insert(0, '.')
from dotenv import load_dotenv; load_dotenv('references/.env')
from tools.airtable import get_pending_images
from tools.image_gen import generate_batch

records = get_pending_images()
results = generate_batch(
    records,
    reference_paths=["references/inputs/product_image.jpg"],
    model="nano-banana-pro",
    provider="google",
    num_variations=1,  # or 2 if user chose 2
)
```

This will:
1. Read all records with `Image Status = "Pending"` from Airtable
2. Generate an image for each record using its `Image Prompt`
3. Upload the generated image to Kie.ai hosting
4. Attach the image URL back to the Airtable record (`Generated Image 1`)
5. Update `Image Status` to `"Generated"`

### Step 3.3: Review Checkpoint

After all images are generated, tell the user:

"All 30 images are generated and visible in Airtable! Check the 'Generated Image 1' column. Mark any you love as 'Approved' and anything you want redone as 'Rejected'. I can regenerate rejected ones with tweaked prompts."

**Do NOT proceed to scheduling until the user confirms.**

---

## Phase 4: Schedule All 30 Posts via Blotato

**Goal:** Take the approved images and their matching captions from Airtable, upload each image to Blotato, and schedule one post per day.

### Step 4.1: Confirm Schedule Settings

Ask the user:
1. **Platform** — Which connected account to post to?
2. **Post time** — Confirm the daily post time (default from Scheduled Date field)

Show connected accounts from `mcp_blotato_blotato_list_accounts`.

### Step 4.2: Read Approved Records from Airtable

```python
from tools.airtable import get_records
# Get all records that have generated images (or approved)
records = get_records("{Image Status} = 'Generated'")
# or if user approved them:
records = get_records("{Image Status} = 'Approved'")
```

For each record, extract:
- `Caption` — the post text
- `Generated Image 1` — the image URL
- `Scheduled Date` — the ISO 8601 timestamp

### Step 4.3: Upload Images & Schedule Posts

For each record:

1. **Get the image URL** from the Airtable record's `Generated Image 1` attachment
2. **Schedule the post** via Blotato:

```
mcp_blotato_blotato_create_post(
    accountId: "32507",          # Instagram
    platform: "instagram",
    text: record["Caption"],
    mediaUrls: [image_url],
    scheduledTime: record["Scheduled Date"]   # e.g., "2026-02-25T10:00:00+11:00"
)
```

3. **Track the submission ID** and confirm scheduling status

### Step 4.4: Track & Log Scheduling Status

For each scheduled post, record the result. Save to `references/outputs/schedule_log.md`:

```markdown
| Day | Date | Platform | Post Submission ID | Status |
|-----|------|----------|-------------------|--------|
| 1   | Feb 25 | instagram | sub_xxx | ✅ Scheduled |
| 2   | Feb 26 | instagram | sub_yyy | ✅ Scheduled |
| ... | ...  | ...      | ...               | ...    |
```

### Step 4.5: Final Confirmation

Present the final summary:
- ✅ Total posts scheduled: 30
- 📅 Date range: [Start] → [End]
- 🕐 Post time: [Time] daily
- 📱 Platform: Instagram
- 🖼️ Images generated: 30/30

"Your 30-day campaign is now running on autopilot! 🚀"

---

## Key Rules

1. **Brand.md is mandatory** — never generate content without understanding the brand first
2. **Airtable is the review hub** — all prompts, captions, and images live in Airtable so the user can review and edit before generation/scheduling
3. **User approves at every checkpoint** — Airtable review, image review, schedule confirmation
4. **Cost transparency** — show estimated costs before any generation
5. **Use Nano Banana Pro via Google AI Studio** — the default image model for campaigns
6. **Track everything** — schedule log saved to `references/outputs/schedule_log.md`
7. **Platform-specific adjustments:**
   - **Instagram**: images posted as regular posts (not reels/stories unless specified), 30 hashtags max
   - **TikTok**: Use 9:16, set `privacyLevel`, `disabledComments: false`, `isAiGenerated: true`
   - **YouTube**: Use 16:9, requires `title`, `privacyStatus`, `shouldNotifySubscribers`
8. **Use the Blotato posting skill** — when using local images, follow the upload process in `.agent/skills/blotato_best_practices/SKILL.md`
9. **Caption quality** — every caption must match the brand voice from brand.md, include emojis, hashtags, and a CTA
10. **Image variety** — rotate through UGC, studio, detail, lifestyle, CGI, and flat lay styles so the feed doesn't look repetitive
11. **Scheduling timezone** — always use the user's timezone (default: +11:00 AEST). Convert to the offset shown in the metadata timestamp.
12. **Airtable batch limits** — records are created in batches of 10 (handled automatically by `create_records_batch`)
