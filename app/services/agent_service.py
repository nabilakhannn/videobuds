"""AI Creative Director agent — uses Gemini text API for brand analysis,
campaign planning, caption writing, prompt engineering, and feedback learning."""

import json
import logging
import os
import re
import requests
from datetime import datetime, timezone

from ..extensions import db
from ..models.agent_memory import AgentMemory
from .prompt_service import STYLE_PRESETS

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Gemini text API config (same free key used for image gen)
# ---------------------------------------------------------------------------
_GEMINI_MODEL = "gemini-2.5-flash"
_GENERATE_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


def _get_api_key():
    """Load Google API key from tools config (same key as image gen)."""
    import sys
    from pathlib import Path
    project_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(project_root))
    from tools.config import GOOGLE_API_KEY
    return GOOGLE_API_KEY


def _call_gemini(prompt, model=None):
    """Call Gemini generateContent for text reasoning. Returns raw text.

    Mirrors the proven pattern in tools/video_analyze.py:214-250.
    """
    model = model or _GEMINI_MODEL
    api_key = _get_api_key()
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY not configured")

    url = _GENERATE_URL.format(model=model)
    headers = {
        "x-goog-api-key": api_key,
        "Content-Type": "application/json",
    }
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
    }

    response = requests.post(url, headers=headers, json=payload, timeout=120)

    if response.status_code != 200:
        raise RuntimeError(
            f"Gemini text API error ({response.status_code}): {response.text[:500]}"
        )

    result = response.json()
    candidates = result.get("candidates", [])
    if not candidates:
        raise RuntimeError(f"No candidates in Gemini response")

    parts = candidates[0].get("content", {}).get("parts", [])
    text = "".join(p.get("text", "") for p in parts).strip()
    if not text:
        raise RuntimeError("Empty text in Gemini response")

    return text


def _call_gemini_grounded(prompt, model=None):
    """Call Gemini with Google Search grounding enabled.

    This makes Gemini actually search the web before responding, returning
    content based on real, current information — not just training data.
    Uses the same API as ``_call_gemini`` but adds the
    ``google_search_retrieval`` tool so the model can fetch live results.

    Returns the generated text (grounding metadata is logged but not returned).
    """
    model = model or _GEMINI_MODEL
    api_key = _get_api_key()
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY not configured")

    url = _GENERATE_URL.format(model=model)
    headers = {
        "x-goog-api-key": api_key,
        "Content-Type": "application/json",
    }
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "tools": [{"google_search_retrieval": {}}],
    }

    response = requests.post(url, headers=headers, json=payload, timeout=180)

    if response.status_code != 200:
        logger.warning(
            "Grounded Gemini call failed (%s), falling back to standard call",
            response.status_code,
        )
        # Graceful fallback — try without grounding
        return _call_gemini(prompt, model=model)

    result = response.json()
    candidates = result.get("candidates", [])
    if not candidates:
        raise RuntimeError("No candidates in grounded Gemini response")

    # Log grounding metadata if present (sources, search queries)
    grounding = candidates[0].get("groundingMetadata")
    if grounding:
        queries = grounding.get("webSearchQueries", [])
        sources = grounding.get("groundingChunks", [])
        logger.info(
            "Gemini grounding: %d search queries, %d sources",
            len(queries), len(sources),
        )

    parts = candidates[0].get("content", {}).get("parts", [])
    text = "".join(p.get("text", "") for p in parts).strip()
    if not text:
        raise RuntimeError("Empty text in grounded Gemini response")

    return text


def _call_gemini_with_image(prompt, image_path, model=None):
    """Call Gemini generateContent with text + image (multimodal).

    Sends the image as base64 inline data alongside the text prompt so the
    AI actually **sees** the product/photo instead of hallucinating.

    Uses the same API endpoint as ``_call_gemini`` but adds an
    ``inline_data`` part containing the base64-encoded image.
    """
    import base64

    model = model or _GEMINI_MODEL
    api_key = _get_api_key()
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY not configured")

    # Read and encode the image
    with open(image_path, "rb") as f:
        image_bytes = f.read()
    image_b64 = base64.b64encode(image_bytes).decode("utf-8")

    # Detect MIME type from file extension
    ext = os.path.splitext(image_path)[1].lower()
    mime_map = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
        ".gif": "image/gif",
    }
    mime_type = mime_map.get(ext, "image/jpeg")

    url = _GENERATE_URL.format(model=model)
    headers = {
        "x-goog-api-key": api_key,
        "Content-Type": "application/json",
    }
    payload = {
        "contents": [{
            "parts": [
                {"text": prompt},
                {"inline_data": {"mime_type": mime_type, "data": image_b64}},
            ]
        }],
    }

    response = requests.post(url, headers=headers, json=payload, timeout=120)

    if response.status_code != 200:
        raise RuntimeError(
            f"Gemini multimodal API error ({response.status_code}): "
            f"{response.text[:500]}"
        )

    result = response.json()
    candidates = result.get("candidates", [])
    if not candidates:
        raise RuntimeError("No candidates in Gemini multimodal response")

    parts = candidates[0].get("content", {}).get("parts", [])
    text = "".join(p.get("text", "") for p in parts).strip()
    if not text:
        raise RuntimeError("Empty text in Gemini multimodal response")

    logger.info("Gemini multimodal call succeeded (%d chars)", len(text))
    return text


# ---------------------------------------------------------------------------
# Helper: fetch and extract text from a URL for AI analysis
# ---------------------------------------------------------------------------

def _research_url(url):
    """Fetch a URL and extract text content for Gemini to analyze.

    Returns extracted text or empty string on failure.
    """
    if not url:
        return ""
    try:
        resp = requests.get(url, timeout=15, headers={
            "User-Agent": "Mozilla/5.0 (compatible; VideoBuds/1.0)"
        })
        resp.raise_for_status()
        html = resp.text

        # Strip HTML tags to get readable text
        text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
        text = re.sub(r'<[^>]+>', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()

        # Limit to ~5000 chars to stay within Gemini context
        return text[:5000]
    except Exception as e:
        logger.warning(f"Agent: Failed to fetch URL {url}: {e}")
        return ""


# ---------------------------------------------------------------------------
# Helper: build rich brand / persona context strings for Gemini prompts
# ---------------------------------------------------------------------------

def _persona_context(persona):
    """Assemble persona voice/tone data into a context block for Gemini prompts.

    Compatible with the UserPersona model.  Returns empty string when *persona*
    is ``None`` so callers can simply concatenate without branching.
    """
    if not persona:
        return ""

    # Prefer the pre-built AI summary (set by the persona wizard)
    if persona.ai_prompt_summary:
        return persona.ai_prompt_summary

    # Fallback: assemble from individual fields
    parts = []
    if persona.tone:
        parts.append(f"Tone: {persona.tone}")
    if persona.voice_style:
        parts.append(f"Voice: {persona.voice_style}")
    if persona.bio:
        parts.append(f"About: {persona.bio}")
    if persona.target_audience:
        parts.append(f"Audience: {persona.target_audience}")
    if persona.brand_keywords:
        parts.append(f"Key words to use: {', '.join(persona.brand_keywords)}")
    if persona.avoid_words:
        parts.append(f"Words to avoid: {', '.join(persona.avoid_words)}")
    if persona.sample_phrases:
        parts.append(f"Example phrases: {' | '.join(persona.sample_phrases[:5])}")
    if persona.writing_guidelines:
        parts.append(f"Guidelines: {persona.writing_guidelines}")
    return "\n".join(parts)


def _brand_context(brand):
    """Assemble all known brand data into a context block."""
    parts = [f"Brand Name: {brand.name}"]
    if brand.tagline:
        parts.append(f"Tagline: {brand.tagline}")
    if brand.target_audience:
        parts.append(f"Target Audience: {brand.target_audience}")
    if brand.visual_style:
        parts.append(f"Visual Style: {brand.visual_style}")
    if brand.colors:
        parts.append(f"Brand Colors: {', '.join(brand.colors)}")
    if brand.pillars:
        parts.append(f"Content Pillars: {', '.join(brand.pillars)}")
    if brand.never_do:
        parts.append(f"Things to NEVER Do: {brand.never_do}")
    if brand.brand_doc:
        parts.append(f"\n--- Full Brand Guidelines ---\n{brand.brand_doc}")
    return "\n".join(parts)


def _load_brand_brief(brand_id):
    """Load the most recent brand brief from agent memory."""
    mem = AgentMemory.query.filter_by(
        brand_id=brand_id, memory_type="brand_brief"
    ).order_by(AgentMemory.created_at.desc()).first()
    return mem.content if mem else None


def _load_preferences(brand_id, limit=20):
    """Load recent approval/rejection preferences for a brand."""
    mems = AgentMemory.query.filter_by(
        brand_id=brand_id, memory_type="preference"
    ).order_by(AgentMemory.created_at.desc()).limit(limit).all()
    return [m.content for m in mems]


def _clean_json(raw):
    """Strip markdown fences from Gemini JSON output."""
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        cleaned = "\n".join(lines)
    return cleaned


# ---------------------------------------------------------------------------
# 1. analyze_brand — run after questionnaire or brand creation
# ---------------------------------------------------------------------------

def analyze_brand(brand, questionnaire_answers=None, *, description="",
                  industry="", visual_vibe="", target_audience_segments="",
                  website_url="", social_url=""):
    """Analyze brand data and produce an enhanced creative brief.

    Accepts either old-style questionnaire_answers dict OR new-style keyword args.
    Stores the brief in AgentMemory and updates brand.brand_doc.
    Also populates brand model fields from AI analysis.
    """
    context = _brand_context(brand)

    # Build input section from new simplified questionnaire
    input_section = ""
    input_parts = []
    if description:
        input_parts.append(f"What the brand does: {description}")
    if industry:
        input_parts.append(f"Industry/niche: {industry}")
    if visual_vibe:
        input_parts.append(f"Visual vibe preferences: {visual_vibe}")
    if target_audience_segments:
        input_parts.append(f"Target audience segments: {target_audience_segments}")
    if input_parts:
        input_section = "\n\nUser-provided input:\n" + "\n".join(f"- {p}" for p in input_parts)

    # Legacy questionnaire support
    qa_section = ""
    if questionnaire_answers:
        qa_lines = []
        for key, answer in questionnaire_answers.items():
            if answer:
                label = key.replace("q_", "").replace("_", " ").title()
                qa_lines.append(f"- {label}: {answer}")
        if qa_lines:
            qa_section = "\n\nQuestionnaire Responses:\n" + "\n".join(qa_lines)

    # Research website if provided
    website_section = ""
    if website_url:
        website_text = _research_url(website_url)
        if website_text:
            website_section = f"\n\n--- Website Content ({website_url}) ---\n{website_text}"

    # Research social profile if provided
    social_section = ""
    if social_url:
        social_text = _research_url(social_url)
        if social_text:
            social_section = f"\n\n--- Social Profile Content ({social_url}) ---\n{social_text}"

    prompt = f"""You are an expert creative director at a top advertising agency. A new client has given you MINIMAL information about their brand. Your job is to research thoroughly and build a COMPLETE brand identity.

{context}{input_section}{qa_section}{website_section}{social_section}

Based on this information, produce TWO outputs:

## OUTPUT 1: Brand Data (JSON)
Output a JSON object with these fields (fill in everything, even if you have to infer from context):
{{
    "tagline": "a catchy brand tagline (max 10 words)",
    "target_audience": "detailed audience description (2-3 sentences)",
    "visual_style": "visual style description (2-3 sentences)",
    "content_pillars": ["pillar1", "pillar2", "pillar3", "pillar4", "pillar5"],
    "never_do": "things to avoid in content and visuals (2-3 sentences)",
    "colors": ["#hex1", "#hex2", "#hex3"],
    "voice": "brand voice and tone description (2-3 sentences)"
}}

## OUTPUT 2: Creative Brief (Markdown)
Write a comprehensive Creative Brief with these sections:
1. **Brand Essence** — One sentence capturing who they are
2. **Voice & Tone** — How the brand speaks. Give 3 example phrases.
3. **Target Audience Profile** — Demographics, psychographics, pain points, desires
4. **Visual Direction** — Color usage, photography style, composition, lighting, textures
5. **Content Strategy** — For each content pillar, describe 3 specific content angles
6. **Image Scenes** — Describe 5 specific scenes that would make great ad images
7. **Guardrails** — What to always avoid in visuals and copy

Format your response as:
```json
<the JSON object>
```

---BRIEF---
<the markdown creative brief>"""

    raw = _call_gemini(prompt)

    # Parse the structured data from response
    brand_data = None
    brief = raw

    # Try to extract JSON block
    json_match = re.search(r'```json\s*\n(.*?)\n```', raw, re.DOTALL)
    if json_match:
        try:
            brand_data = json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass

    # Extract brief section
    brief_marker = "---BRIEF---"
    if brief_marker in raw:
        brief = raw.split(brief_marker, 1)[1].strip()
    elif json_match:
        # Use everything after the JSON block
        brief = raw[json_match.end():].strip()

    # Update brand model fields from AI analysis
    if brand_data:
        if brand_data.get("tagline"):
            brand.tagline = brand_data["tagline"]
        if brand_data.get("target_audience"):
            brand.target_audience = brand_data["target_audience"]
        if brand_data.get("visual_style"):
            brand.visual_style = brand_data["visual_style"]
        if brand_data.get("content_pillars"):
            brand.content_pillars = json.dumps(brand_data["content_pillars"])
        if brand_data.get("never_do"):
            brand.never_do = brand_data["never_do"]
        if brand_data.get("colors"):
            brand.colors_json = json.dumps(brand_data["colors"])

    # Store in agent memory
    existing = AgentMemory.query.filter_by(
        brand_id=brand.id, memory_type="brand_brief"
    ).first()
    if existing:
        existing.content = brief
        existing.created_at = datetime.now(timezone.utc)
    else:
        db.session.add(AgentMemory(
            brand_id=brand.id,
            memory_type="brand_brief",
            content=brief,
        ))

    # Update brand_doc with the enhanced version
    brand.brand_doc = brief
    db.session.commit()

    logger.info(f"Agent: Brand brief generated for brand {brand.id} ({brand.name})")
    return brief


# ---------------------------------------------------------------------------
# 2. plan_campaign — run after campaign creation to fill posts
# ---------------------------------------------------------------------------

def plan_campaign(brand, campaign, *, persona=None):
    """Plan content for every post in a campaign. Updates captions and stores plan.

    Args:
        brand: Brand model instance.
        campaign: Campaign model instance.
        persona: Optional UserPersona instance — when provided, the AI writes
                 captions and scene descriptions in the persona's voice.
    """
    from ..models.post import Post

    brief = _load_brand_brief(brand.id) or _brand_context(brand)
    preferences = _load_preferences(brand.id)

    pref_section = ""
    if preferences:
        pref_section = "\n\nLearned Preferences (from past approvals/rejections):\n" + "\n".join(
            f"- {p}" for p in preferences[:10]
        )

    persona_section = ""
    persona_block = _persona_context(persona)
    if persona_block:
        persona_section = (
            f"\n\n--- VOICE & PERSONALITY (write captions in this person's voice) ---\n"
            f"{persona_block}\n---\nMatch their tone, vocabulary, and energy level in every caption."
        )

    posts = Post.query.filter_by(campaign_id=campaign.id).order_by(Post.day_number).all()
    if not posts:
        return []

    style_name = "minimalist"
    if campaign.style_preset and campaign.style_preset in STYLE_PRESETS:
        style_name = STYLE_PRESETS[campaign.style_preset]["name"]

    # Campaign intention context
    intention_section = ""
    if campaign.intention:
        intention_labels = {
            "brand_awareness": "Brand Awareness — introduce the brand to new audiences",
            "product_launch": "Product Launch — showcase a new product or service",
            "engagement": "Engagement & Community — build relationships, start conversations",
            "education": "Education & Value — share tips, tutorials, how-tos",
            "seasonal": "Seasonal/Holiday — capitalize on seasonal moments",
            "behind_scenes": "Behind the Scenes — show the human side of the brand",
            "sales": "Sales & Promotion — drive conversions and sales",
        }
        intention_desc = intention_labels.get(campaign.intention, campaign.intention)
        intention_section = f"\nCampaign Intention: {intention_desc}"

    post_list = "\n".join(
        f"- Day {p.day_number}: Pillar={p.content_pillar or 'general'}, Type={p.image_type or 'lifestyle'}"
        for p in posts
    )

    prompt = f"""You are a creative director planning a {len(posts)}-day social media campaign.

Brand Brief:
{brief}
{pref_section}{persona_section}

Campaign: "{campaign.name}"
Visual Style: {style_name}{intention_section}
Start Date: {campaign.start_date}

Posts to plan:
{post_list}

IMPORTANT: Every post MUST align with the campaign intention. The content, captions, and scenes should all serve the campaign's goal.

For EACH day, output a JSON array. Each item must have:
- "day": day number (integer)
- "caption": a ready-to-post social media caption in the brand's voice (2-4 sentences, include a call-to-action, no hashtags in caption)
- "scene": a specific image scene description — describe WHAT to show (subject, setting, composition, mood, key visual elements). Be specific: "woman in her 30s holding product at a sunlit kitchen counter" NOT "lifestyle image"
- "angle": the specific content angle for this day's pillar

Output ONLY the JSON array, no markdown fences, no explanation.
Example format: [{{"day":1,"caption":"...","scene":"...","angle":"..."}}]"""

    raw = _call_gemini(prompt)
    cleaned = _clean_json(raw)

    try:
        plan = json.loads(cleaned)
    except json.JSONDecodeError:
        logger.warning(f"Agent: Failed to parse campaign plan JSON for campaign {campaign.id}")
        return []

    # Update posts with AI-generated content
    post_map = {p.day_number: p for p in posts}
    for item in plan:
        day = item.get("day")
        post = post_map.get(day)
        if not post:
            continue

        caption = item.get("caption", "")
        scene = item.get("scene", "")

        if caption:
            post.caption = caption
        if scene:
            post.image_prompt = scene

    # Store the full plan in agent memory
    db.session.add(AgentMemory(
        brand_id=brand.id,
        campaign_id=campaign.id,
        memory_type="campaign_plan",
        content=json.dumps(plan, ensure_ascii=False),
    ))

    db.session.commit()
    logger.info(f"Agent: Campaign plan generated for campaign {campaign.id} ({len(plan)} days)")
    return plan


# ---------------------------------------------------------------------------
# 3. write_captions — on-demand caption suggestions
# ---------------------------------------------------------------------------

def write_captions(brand, post, campaign, *, persona=None):
    """Generate 3 caption variants for a post. Returns list of strings.

    Args:
        brand: Brand model instance.
        post: Post model instance.
        campaign: Campaign model instance.
        persona: Optional UserPersona — captions will be written in the
                 persona's voice when provided.
    """
    brief = _load_brand_brief(brand.id) or _brand_context(brand)
    preferences = _load_preferences(brand.id)

    pref_section = ""
    if preferences:
        pref_section = "\nLearned style preferences:\n" + "\n".join(f"- {p}" for p in preferences[:5])

    persona_section = ""
    persona_block = _persona_context(persona)
    if persona_block:
        persona_section = (
            f"\n\n--- VOICE & PERSONALITY (write exactly like this person) ---\n"
            f"{persona_block}\n---\nCRITICAL: Match their tone, vocabulary, and energy level."
        )

    prompt = f"""You are a social media copywriter for {brand.name}.

Brand Brief (excerpt):
{brief[:2000]}
{pref_section}{persona_section}

Write 3 different caption variants for this post:
- Day {post.day_number} of campaign "{campaign.name}"
- Content Pillar: {post.content_pillar or 'general'}
- Image Type: {post.image_type or 'lifestyle'}
- Current scene/prompt: {post.image_prompt or 'not set'}

Requirements:
- Write in the brand's voice and tone
- 2-4 sentences each
- Include a clear call-to-action
- Each variant should take a different angle (emotional, educational, provocative)
- Target audience: {brand.target_audience or 'general'}
- Do NOT include hashtags in the caption

Output ONLY a JSON array of 3 strings. No markdown fences, no explanation.
Example: ["Caption one...", "Caption two...", "Caption three..."]"""

    raw = _call_gemini(prompt)
    cleaned = _clean_json(raw)

    try:
        captions = json.loads(cleaned)
        if isinstance(captions, list) and len(captions) >= 1:
            return captions[:3]
    except json.JSONDecodeError:
        pass

    # Fallback: split by newlines if JSON parsing fails
    lines = [l.strip().lstrip("0123456789.-) ") for l in raw.strip().split("\n") if l.strip()]
    return lines[:3] if lines else ["Could not generate captions. Please try again."]


# ---------------------------------------------------------------------------
# 4. build_smart_prompt — replace template-based prompt building
# ---------------------------------------------------------------------------

def build_smart_prompt(brand, post, campaign, *, persona=None):
    """Generate a detailed, specific image prompt using AI reasoning.

    Args:
        brand: Brand model instance.
        post: Post model instance.
        campaign: Campaign model instance (or None).
        persona: Optional UserPersona — when provided, the visual direction
                 will align with the persona's brand style.
    """
    brief = _load_brand_brief(brand.id) or _brand_context(brand)
    preferences = _load_preferences(brand.id)

    style_key = post.style_preset or (campaign.style_preset if campaign else None) or "minimalist"
    preset = STYLE_PRESETS.get(style_key, STYLE_PRESETS["minimalist"])

    pref_section = ""
    if preferences:
        pref_section = "\nPast feedback (what the user liked/disliked):\n" + "\n".join(
            f"- {p}" for p in preferences[:8]
        )

    # Use existing scene description if available (from campaign planning)
    scene_hint = ""
    if post.image_prompt:
        scene_hint = f"\nScene direction (from campaign plan): {post.image_prompt}"

    caption_hint = ""
    if post.caption:
        caption_hint = f"\nCaption context (image should match this message): {post.caption}"

    # Campaign intention context
    intention_hint = ""
    if campaign and campaign.intention:
        intention_hint = f"\nCampaign goal: {campaign.intention.replace('_', ' ').title()}"

    # Persona visual direction
    persona_hint = ""
    persona_block = _persona_context(persona)
    if persona_block:
        persona_hint = f"\nCreator persona (visual style should match their vibe): {persona_block[:500]}"

    prompt = f"""You are an expert art director writing an image generation prompt for an AI model (Google Gemini image generation).

Brand: {brand.name}
Brand Brief (excerpt):
{brief[:1500]}

Visual Style Preset: {preset['name']} — {preset['prompt_fragment']}
Camera Direction: {preset['camera']}
Content Pillar: {post.content_pillar or 'general'}
Image Type: {post.image_type or 'lifestyle'}
Brand Colors: {', '.join(brand.colors) if brand.colors else 'not specified'}
Target Audience: {brand.target_audience or 'general'}
Things to NEVER show: {brand.never_do or 'none specified'}
{scene_hint}{caption_hint}{intention_hint}{persona_hint}{pref_section}

Write a single, detailed image generation prompt (3-5 sentences) that:
1. Describes a SPECIFIC scene with a clear subject (person, product, setting)
2. Includes composition and camera angle
3. Specifies lighting and mood
4. References brand colors naturally
5. Matches the visual style preset
6. Would work as an Instagram/TikTok ad creative

Output ONLY the prompt text — no quotes, no labels, no explanation. Just the image generation prompt itself."""

    return _call_gemini(prompt)


# ---------------------------------------------------------------------------
# 5. learn_from_feedback — store approval/rejection preferences
# ---------------------------------------------------------------------------

def learn_from_feedback(brand, post, action):
    """Store a preference memory when a post is approved or rejected.

    Args:
        brand: Brand model instance
        post: Post model instance
        action: "approved" or "rejected"
    """
    label = "LIKED" if action == "approved" else "DISLIKED"

    summary_parts = [f"{label}:"]
    if post.style_preset:
        summary_parts.append(f"style={post.style_preset}")
    if post.content_pillar:
        summary_parts.append(f"pillar={post.content_pillar}")
    if post.image_type:
        summary_parts.append(f"type={post.image_type}")
    if post.image_prompt:
        summary_parts.append(f"prompt={post.image_prompt[:200]}")
    if post.caption:
        summary_parts.append(f"caption={post.caption[:100]}")

    content = " | ".join(summary_parts)

    db.session.add(AgentMemory(
        brand_id=brand.id,
        memory_type="preference",
        content=content,
    ))
    db.session.commit()

    logger.info(f"Agent: Stored {action} preference for brand {brand.id}, post {post.id}")


# ---------------------------------------------------------------------------
# 6. select_photos — AI picks relevant photos from brand library
# ---------------------------------------------------------------------------

def select_photos(brand, post, campaign, *, persona=None):
    """Pick the most relevant photos from the brand's photo library for this post.

    Args:
        brand: Brand model instance.
        post: Post model instance.
        campaign: Campaign model instance.
        persona: Optional UserPersona — used to bias photo selection towards
                 the persona's style (e.g. prefer UGC for casual voices).

    Returns a list of file paths for the most relevant photos.
    """
    from ..models.reference_image import ReferenceImage

    # Load all brand photos (brand-level + campaign-level)
    all_refs = ReferenceImage.query.filter(
        db.or_(
            db.and_(ReferenceImage.brand_id == brand.id, ReferenceImage.campaign_id.is_(None)),
            ReferenceImage.campaign_id == campaign.id,
        )
    ).all()

    if not all_refs:
        return []

    # If 3 or fewer photos, just use all of them
    valid_refs = [r for r in all_refs if r.file_path and os.path.exists(r.file_path)]
    if len(valid_refs) <= 3:
        return [r.file_path for r in valid_refs]

    # Build photo inventory for AI to choose from
    photo_list = "\n".join(
        f"- ID:{r.id} | Purpose:{r.purpose} | File:{os.path.basename(r.file_path)}"
        for r in valid_refs
    )

    intention_hint = ""
    if campaign and campaign.intention:
        intention_hint = f"\nCampaign goal: {campaign.intention.replace('_', ' ').title()}"

    persona_hint = ""
    persona_block = _persona_context(persona)
    if persona_block:
        persona_hint = f"\nCreator personality: {persona_block[:300]}"

    prompt = f"""You are an art director selecting reference photos for an ad creative.

Post Context:
- Content Pillar: {post.content_pillar or 'general'}
- Image Type: {post.image_type or 'lifestyle'}
- Scene/Prompt: {post.image_prompt or 'not set'}
- Caption: {post.caption or 'not set'}{intention_hint}{persona_hint}

Available Photos:
{photo_list}

Select 1-3 photos that would be MOST relevant as reference images for this post.
Consider: product photos for product-focused posts, personal photos for UGC/behind-scenes, inspiration for mood/style.

Output ONLY a JSON array of photo IDs. Example: [1, 5, 12]"""

    try:
        raw = _call_gemini(prompt)
        cleaned = _clean_json(raw)
        selected_ids = json.loads(cleaned)

        if isinstance(selected_ids, list):
            ref_map = {r.id: r.file_path for r in valid_refs}
            paths = [ref_map[rid] for rid in selected_ids if rid in ref_map]
            if paths:
                return paths
    except Exception as e:
        logger.warning(f"Agent: Photo selection failed, using all photos: {e}")

    # Fallback: return all valid photo paths
    return [r.file_path for r in valid_refs]
