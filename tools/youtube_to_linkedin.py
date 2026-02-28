"""
Modal.com Serverless Pipeline: YouTube → LinkedIn Automation

Runs daily on a cron schedule. Checks for new videos on a YouTube channel,
extracts the transcript, generates an infographic (Nano Banana Pro),
writes a LinkedIn post in the creator's voice, and publishes via Blotato.

SETUP:
  1. Replace YOUR_CHANNEL_ID with your YouTube channel ID
  2. Replace YOUR_BRAND_VOICE with your brand voice guidelines
  3. Create Modal secrets (see below)
  4. Deploy: modal deploy modal_pipeline_example.py
  5. Test:   modal run modal_pipeline_example.py
  6. Logs:   modal app logs youtube-linkedin-pipeline

SECRETS:
  modal secret create youtube-pipeline-secrets \
    GOOGLE_API_KEY=your_key \
    BLOTATO_API_KEY=your_key \
    LINKEDIN_ACCOUNT_ID=your_linkedin_id
"""

import modal
import json
import time
import base64
import re
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Modal App + Image
# ---------------------------------------------------------------------------
app = modal.App("youtube-linkedin-pipeline")

image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install("requests", "feedparser")
)

# Store all API keys in a Modal Secret
# See SETUP instructions above for how to create this
secret = modal.Secret.from_name("youtube-pipeline-secrets")

# Persistent volume to track which videos we've already processed
volume = modal.Volume.from_name("youtube-pipeline-state", create_if_missing=True)


# ---------------------------------------------------------------------------
# Brand Voice — CUSTOMIZE THIS FOR YOUR CREATOR
# ---------------------------------------------------------------------------
BRAND_VOICE = """
You are writing a LinkedIn post as [YOUR CREATOR NAME] — [brief creator description].

VOICE RULES:
- [Describe the tone: professional-casual? Academic? Motivational?]
- [How do they express opinions? Bold convictions? Careful analysis?]
- [Do they create urgency? Use humor? Tell stories?]
- [Do they address the reader directly with "you"?]

STRUCTURE RULES:
- Open with a bold hook — a surprising fact or provocative question
- Use double line breaks between every paragraph (LinkedIn formatting)
- Include a numbered framework or list if applicable
- Back claims with evidence — studies, companies, real examples
- End with a reflective question that invites comments
- Add 3-5 relevant hashtags on the final line
- Length: 150-300 words. Dense but not long. Every sentence earns its place.

WHAT THEY NEVER DO:
- [List things that are off-brand]
- Generic hype without substance
- Clickbait without follow-through
- Vague advice without frameworks
"""

# ---------------------------------------------------------------------------
# YouTube Channel Config — REPLACE WITH YOUR CHANNEL
# ---------------------------------------------------------------------------
# Find your channel ID: Go to your YouTube channel → View Page Source → search for "channelId"
CHANNEL_ID = "YOUR_CHANNEL_ID_HERE"
RSS_URL = f"https://www.youtube.com/feeds/videos.xml?channel_id={CHANNEL_ID}"

# State file path on the Modal Volume
STATE_FILE = "/state/processed_videos.json"


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------
def load_processed_videos():
    """Load the list of already-processed video IDs from persistent storage."""
    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_processed_video(video_id):
    """Add a video ID to the processed list."""
    processed = load_processed_videos()
    processed.append(video_id)
    # Keep only last 100 entries
    processed = processed[-100:]
    with open(STATE_FILE, "w") as f:
        json.dump(processed, f)


def get_latest_video():
    """Fetch the latest video from the YouTube RSS feed."""
    import feedparser
    feed = feedparser.parse(RSS_URL)

    if not feed.entries:
        return None

    entry = feed.entries[0]
    video_id = entry.get("yt_videoid", "")
    return {
        "video_id": video_id,
        "title": entry.get("title", ""),
        "url": f"https://www.youtube.com/watch?v={video_id}",
        "published": entry.get("published", ""),
    }


def extract_transcript(video_url, blotato_key):
    """Use Blotato Create Source to extract and summarize the YouTube transcript."""
    import requests

    # Step 1: Submit extraction
    resp = requests.post(
        "https://backend.blotato.com/v2/sources",
        headers={
            "blotato-api-key": blotato_key,
            "Content-Type": "application/json",
        },
        json={
            "sourceType": "youtube",
            "url": video_url,
            "customInstructions": (
                "Summarize the key points and main takeaways in a concise, "
                "well-structured format. Focus on core arguments, frameworks, "
                "and actionable insights. Use bullet points."
            ),
        },
        timeout=30,
    )
    data = resp.json()
    source_id = data.get("id")

    if data.get("status") == "completed":
        return data.get("content", ""), data.get("title", "")

    # Step 2: Poll for completion (up to 2 minutes)
    for _ in range(24):
        time.sleep(5)
        poll_resp = requests.get(
            f"https://backend.blotato.com/v2/sources/{source_id}",
            headers={"blotato-api-key": blotato_key},
            timeout=15,
        )
        poll_data = poll_resp.json()
        if poll_data.get("status") == "completed":
            return poll_data.get("content", ""), poll_data.get("title", "")
        if poll_data.get("status") == "failed":
            raise Exception(f"Transcript extraction failed: {poll_data}")

    raise Exception(f"Transcript extraction timed out for {video_url}")


def generate_caption(summary, video_title, google_api_key):
    """Use Gemini to write a LinkedIn post in the creator's voice."""
    import requests

    prompt = f"""{BRAND_VOICE}

Based on the following video summary, write a LinkedIn post in the creator's voice.
The video title is: "{video_title}"

VIDEO SUMMARY:
{summary}

Write the LinkedIn post now. Output ONLY the post text, no markdown formatting,
no explanations. Use plain text with line breaks.
"""

    resp = requests.post(
        "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent",
        headers={
            "x-goog-api-key": google_api_key,
            "Content-Type": "application/json",
        },
        json={
            "contents": [{"parts": [{"text": prompt}]}],
        },
        timeout=60,
    )

    result = resp.json()
    candidates = result.get("candidates", [])
    if candidates:
        parts = candidates[0].get("content", {}).get("parts", [])
        if parts:
            return parts[0].get("text", "").strip()

    raise Exception(f"Caption generation failed: {result}")


def generate_infographic(summary, video_title, google_api_key):
    """Generate an infographic using Nano Banana Pro via Google AI Studio."""
    import requests

    prompt = f"""4:5. Create a premium, visually striking LinkedIn infographic with a clean dark navy blue background (#0A1628) and white/cyan accent text.

Based on this video: "{video_title}"

Content summary to visualize:
{summary[:1500]}

Requirements:
- Bold title at top summarizing the key insight
- Subtitle in cyan (#00D4FF)
- Clean vertical sections with thin cyan divider lines
- Use icons or visual elements for each key point
- Include a numbered framework or tiered model if applicable
- Bold call to action at the bottom
- Footer: "YOUR CREATOR NAME | @YourHandle | Your Tagline"
- Style: Modern, corporate-clean, data-visualization aesthetic
- Typography-focused, professional LinkedIn infographic
"""

    resp = requests.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3-pro-image-preview:generateContent",
        headers={
            "x-goog-api-key": google_api_key,
            "Content-Type": "application/json",
        },
        json={
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"responseModalities": ["TEXT", "IMAGE"]},
        },
        timeout=120,
    )

    result = resp.json()
    candidates = result.get("candidates", [])
    if not candidates:
        raise Exception(f"Infographic generation failed: {result}")

    parts = candidates[0].get("content", {}).get("parts", [])
    for part in parts:
        if "inlineData" in part:
            return part["inlineData"]["data"]  # base64 image data

    raise Exception("No image data in response")


def upload_to_blotato(base64_image, blotato_key):
    """Upload base64 image to Blotato hosting, return public URL."""
    import requests

    data_uri = f"data:image/png;base64,{base64_image}"
    resp = requests.post(
        "https://backend.blotato.com/v2/media",
        headers={
            "blotato-api-key": blotato_key,
            "Content-Type": "application/json",
        },
        json={"url": data_uri},
        timeout=60,
    )

    if resp.status_code == 200:
        return resp.json().get("url", "")
    raise Exception(f"Blotato upload failed: {resp.status_code} {resp.text[:200]}")


def post_to_linkedin(text, image_url, blotato_key, account_id):
    """Publish a post to LinkedIn via Blotato."""
    import requests

    payload = {
        "accountId": account_id,
        "platform": "linkedin",
        "text": text,
    }
    if image_url:
        payload["mediaUrls"] = [image_url]

    resp = requests.post(
        "https://backend.blotato.com/v2/posts",
        headers={
            "blotato-api-key": blotato_key,
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=30,
    )

    data = resp.json()
    status = data.get("status")

    # If still processing, poll
    if status == "in-progress":
        submission_id = data.get("postSubmissionId")
        for _ in range(6):
            time.sleep(10)
            poll = requests.get(
                f"https://backend.blotato.com/v2/posts/{submission_id}",
                headers={"blotato-api-key": blotato_key},
                timeout=15,
            )
            poll_data = poll.json()
            if poll_data.get("status") in ("published", "scheduled"):
                return poll_data
            if poll_data.get("status") == "failed":
                raise Exception(f"Post failed: {poll_data}")

    return data


# ---------------------------------------------------------------------------
# Main Pipeline Function
# ---------------------------------------------------------------------------
@app.function(
    image=image,
    secrets=[secret],
    volumes={"/state": volume},
    timeout=600,
)
def run_pipeline():
    """
    Full pipeline: Check for new video → Extract transcript → Generate
    infographic → Write caption → Post to LinkedIn.
    """
    import os

    google_key = os.environ["GOOGLE_API_KEY"]
    blotato_key = os.environ["BLOTATO_API_KEY"]
    linkedin_id = os.environ["LINKEDIN_ACCOUNT_ID"]

    print("=" * 60)
    print(f"  YouTube → LinkedIn Pipeline — {datetime.now(timezone.utc).isoformat()}")
    print("=" * 60)

    # Step 1: Check for new videos
    print("\n📺 Step 1: Checking YouTube RSS feed...")
    latest = get_latest_video()
    if not latest:
        print("   No videos found in feed. Exiting.")
        return {"status": "no_videos"}

    print(f"   Latest: {latest['title']}")
    print(f"   URL: {latest['url']}")
    print(f"   Published: {latest['published']}")

    # Check if already processed
    processed = load_processed_videos()
    if latest["video_id"] in processed:
        print(f"   ⏭️ Already processed. Skipping.")
        return {"status": "already_processed", "video_id": latest["video_id"]}

    # Step 2: Extract transcript
    print("\n📝 Step 2: Extracting transcript via Blotato...")
    summary, title = extract_transcript(latest["url"], blotato_key)
    print(f"   Title: {title}")
    print(f"   Summary length: {len(summary)} chars")

    # Step 3: Generate infographic
    print("\n🎨 Step 3: Generating infographic via Nano Banana Pro...")
    image_b64 = generate_infographic(summary, title, google_key)
    print(f"   Image generated: {len(image_b64)} chars (base64)")

    # Step 4: Upload to Blotato hosting
    print("\n📤 Step 4: Uploading to Blotato hosting...")
    image_url = upload_to_blotato(image_b64, blotato_key)
    print(f"   Hosted URL: {image_url}")

    # Step 5: Generate caption in creator's voice
    print("\n✍️ Step 5: Generating LinkedIn caption...")
    caption = generate_caption(summary, title, google_key)
    print(f"   Caption length: {len(caption)} chars")
    print(f"   Preview: {caption[:150]}...")

    # Step 6: Post to LinkedIn
    print("\n📬 Step 6: Posting to LinkedIn...")
    result = post_to_linkedin(caption, image_url, blotato_key, linkedin_id)
    print(f"   Status: {result.get('status')}")
    print(f"   URL: {result.get('publicUrl', 'N/A')}")

    # Step 7: Mark as processed
    save_processed_video(latest["video_id"])
    volume.commit()
    print("\n✅ Pipeline complete!")

    return {
        "status": "posted",
        "video_id": latest["video_id"],
        "video_title": title,
        "linkedin_url": result.get("publicUrl"),
        "image_url": image_url,
    }


# ---------------------------------------------------------------------------
# Cron Schedule — Runs daily at 10:00 AM UTC
# Adjust to your timezone. Examples:
#   "0 10 * * *"  = 10:00 AM UTC (9:00 PM AEDT / 5:00 AM EST)
#   "0 14 * * *"  = 2:00 PM UTC (1:00 AM AEDT / 9:00 AM EST)
# ---------------------------------------------------------------------------
@app.function(
    image=image,
    secrets=[secret],
    volumes={"/state": volume},
    schedule=modal.Cron("0 10 * * *"),
    timeout=600,
)
def scheduled_run():
    """Daily cron trigger — calls the main pipeline."""
    print("⏰ Cron trigger fired!")
    return run_pipeline.local()


# ---------------------------------------------------------------------------
# CLI Entry Point — for manual testing
# ---------------------------------------------------------------------------
@app.local_entrypoint()
def main():
    """Run the pipeline manually: modal run modal_pipeline_example.py"""
    result = run_pipeline.remote()
    print(f"\n🎯 Result: {json.dumps(result, indent=2)}")
