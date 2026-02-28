"""Script Agent — research topics and write viral video scripts in the user's voice.

This service is the core creative engine for recipes that need written output:
ad scripts, TikTok hooks, YouTube intros, captions, newsletters, etc.

It combines:
  - Topic research (URL scraping or raw topic text)
  - Brand context (optional, from Brand model)
  - Persona voice (from UserPersona.ai_prompt_summary)
  - Format-specific writing (hooks, scripts, captions, articles)

Usage from a recipe::

    from app.services.script_service import write_script, research_topic

    # Quick single script
    result = write_script(
        topic="Our new protein bar launch",
        persona_id=3,
        script_type="tiktok_hook",
    )

    # Research first, then write
    research = research_topic("https://example.com/article", extra_context="focus on pricing")
    result = write_script(
        topic=research["summary"],
        persona_id=3,
        script_type="ad_script",
        brand_id=1,
    )
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import asdict, dataclass, field
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Script type definitions
# ---------------------------------------------------------------------------

SCRIPT_TYPES: Dict[str, dict] = {
    "tiktok_hook": {
        "label": "TikTok / Reels Hook",
        "max_seconds": 15,
        "structure": (
            "A 5-15 second scroll-stopping hook. "
            "Open with a bold, curiosity-driven statement or question. "
            "Must grab attention in the first 1-2 seconds."
        ),
        "example_format": (
            "[HOOK — 1-2s] Bold opening line\n"
            "[REVEAL — 3-5s] The payoff or proof\n"
            "[CTA — 2-3s] What to do next"
        ),
    },
    "tiktok_full": {
        "label": "TikTok / Reels Full Script",
        "max_seconds": 60,
        "structure": (
            "A 30-60 second short-form video script. "
            "Hook → Problem → Solution → Proof → CTA. "
            "Conversational, punchy, uses pattern interrupts."
        ),
        "example_format": (
            "[HOOK — 0-3s] Attention-grabbing opener\n"
            "[PROBLEM — 3-10s] Relatable pain point\n"
            "[SOLUTION — 10-25s] Your answer / product / tip\n"
            "[PROOF — 25-40s] Social proof, results, or demo\n"
            "[CTA — 40-60s] Tell them exactly what to do"
        ),
    },
    "youtube_intro": {
        "label": "YouTube Intro (First 30s)",
        "max_seconds": 30,
        "structure": (
            "A 15-30 second YouTube intro. "
            "Tease the value, introduce yourself briefly, "
            "promise what the viewer will learn or get."
        ),
        "example_format": (
            "[TEASE — 0-5s] Surprising stat, question, or bold claim\n"
            "[INTRO — 5-15s] Who you are (one sentence)\n"
            "[PROMISE — 15-30s] What the viewer will learn / get / solve"
        ),
    },
    "ad_script": {
        "label": "Ad / UGC Script",
        "max_seconds": 45,
        "structure": (
            "A 15-45 second UGC-style ad script. "
            "Feels authentic, not salesy. "
            "Problem-agitate-solve with a clear CTA."
        ),
        "example_format": (
            "[HOOK — 0-3s] 'POV:' or 'I tried…' or 'Stop scrolling if…'\n"
            "[STORY — 3-15s] Personal experience with the problem\n"
            "[PRODUCT — 15-30s] How the product solved it\n"
            "[PROOF — 30-40s] Results or before/after\n"
            "[CTA — 40-45s] Where to buy / link in bio"
        ),
    },
    "talking_head": {
        "label": "Talking Head / Explainer",
        "max_seconds": 90,
        "structure": (
            "A 30-90 second talking-head script. "
            "Educational, authoritative, but approachable. "
            "One core idea explained clearly."
        ),
        "example_format": (
            "[HOOK — 0-5s] Surprising fact or question\n"
            "[CONTEXT — 5-20s] Why this matters right now\n"
            "[EXPLAIN — 20-60s] The core idea in 3 clear beats\n"
            "[TAKEAWAY — 60-80s] So what? What should the viewer do?\n"
            "[CTA — 80-90s] Follow for more / link / comment"
        ),
    },
    "caption": {
        "label": "Social Caption",
        "max_seconds": 0,  # text-only
        "structure": (
            "A social media caption (2-5 sentences). "
            "Hook line → body → call to action. "
            "Conversational and platform-native."
        ),
        "example_format": (
            "Line 1: Hook / bold statement\n"
            "Lines 2-4: Supporting story or tips\n"
            "Last line: CTA (comment, save, share, link)"
        ),
    },
    "newsletter": {
        "label": "Newsletter / Email",
        "max_seconds": 0,  # text-only
        "structure": (
            "A short email newsletter section (200-400 words). "
            "Subject line → opening hook → 3-5 curated insights or tips "
            "→ closing CTA. Scannable with bullet points."
        ),
        "example_format": (
            "Subject: [compelling subject line]\n\n"
            "Hey [name],\n\n"
            "[Opening hook — 1-2 sentences]\n\n"
            "Here's what caught my eye this week:\n\n"
            "1. **[Insight]** — [2-3 sentence summary]\n"
            "2. **[Insight]** — [2-3 sentence summary]\n"
            "3. **[Insight]** — [2-3 sentence summary]\n\n"
            "[Closing + CTA]"
        ),
    },
}


# ---------------------------------------------------------------------------
# Data classes for structured results
# ---------------------------------------------------------------------------

@dataclass
class ScriptResult:
    """One generated script variant."""
    script_type: str
    label: str
    body: str
    hook: str = ""  # First line / attention grabber
    estimated_seconds: int = 0
    word_count: int = 0
    notes: str = ""  # AI's internal reasoning or tips

    def to_dict(self):
        return asdict(self)


@dataclass
class ScriptBatch:
    """Result of a write_scripts() call — multiple variants."""
    topic: str
    persona_name: str
    scripts: List[ScriptResult] = field(default_factory=list)
    research_summary: str = ""
    cost: float = 0.0

    def to_dict(self):
        return {
            "topic": self.topic,
            "persona_name": self.persona_name,
            "scripts": [s.to_dict() for s in self.scripts],
            "research_summary": self.research_summary,
            "cost": self.cost,
        }


# ---------------------------------------------------------------------------
# Gemini helpers (reuse patterns from agent_service)
# ---------------------------------------------------------------------------

def _get_api_key():
    """Load Google API key from tools config."""
    import sys
    from pathlib import Path
    project_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(project_root))
    from tools.config import GOOGLE_API_KEY
    return GOOGLE_API_KEY


_GEMINI_MODEL = "gemini-2.5-flash"
_GENERATE_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
)


def _call_gemini(prompt: str, model: str | None = None) -> str:
    """Call Gemini generateContent for text reasoning. Returns raw text."""
    import requests as _requests

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

    response = _requests.post(url, headers=headers, json=payload, timeout=120)

    if response.status_code != 200:
        raise RuntimeError(
            f"Gemini API error ({response.status_code}): {response.text[:500]}"
        )

    result = response.json()
    candidates = result.get("candidates", [])
    if not candidates:
        raise RuntimeError("No candidates in Gemini response")

    parts = candidates[0].get("content", {}).get("parts", [])
    text = "".join(p.get("text", "") for p in parts).strip()
    if not text:
        raise RuntimeError("Empty text in Gemini response")

    return text


def _clean_json(raw: str) -> str:
    """Strip markdown fences from Gemini JSON output."""
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        cleaned = "\n".join(lines)
    return cleaned


# ---------------------------------------------------------------------------
# URL research
# ---------------------------------------------------------------------------

def _fetch_url_text(url: str) -> str:
    """Scrape a URL and extract readable text (max ~5 000 chars)."""
    import requests as _requests

    if not url:
        return ""
    try:
        resp = _requests.get(
            url,
            timeout=15,
            headers={"User-Agent": "Mozilla/5.0 (compatible; VideoBuds/1.0)"},
        )
        resp.raise_for_status()
        html = resp.text

        # Strip scripts, styles, and tags
        text = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL)
        text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL)
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text[:5000]
    except Exception as e:
        logger.warning(f"ScriptAgent: Failed to fetch URL {url}: {e}")
        return ""


def research_topic(
    url: str = "",
    topic_text: str = "",
    extra_context: str = "",
) -> dict:
    """Research a topic via URL scraping + AI summarisation.

    Returns::

        {
            "summary": "AI-generated research summary…",
            "key_points": ["point 1", "point 2", …],
            "raw_text": "scraped text (truncated)",
        }
    """
    raw_text = ""
    if url:
        raw_text = _fetch_url_text(url)

    if not raw_text and not topic_text:
        return {
            "summary": "",
            "key_points": [],
            "raw_text": "",
        }

    source_block = ""
    if raw_text:
        source_block = f"\n\n--- Source Material (from {url}) ---\n{raw_text}"

    topic_block = ""
    if topic_text:
        topic_block = f"\n\nTopic Description:\n{topic_text}"

    extra_block = ""
    if extra_context:
        extra_block = f"\n\nAdditional Context:\n{extra_context}"

    prompt = f"""You are a research assistant preparing material for a content creator.
{topic_block}{source_block}{extra_block}

Produce a JSON object with:
- "summary": a concise 3-5 sentence summary of the key information
- "key_points": an array of 5-8 bullet points capturing the most interesting / shareable facts
- "angles": an array of 3 creative angles a content creator could use (e.g. "contrarian take", "how-to tutorial", "myth-busting")

Output ONLY valid JSON, no markdown fences."""

    try:
        raw = _call_gemini(prompt)
        cleaned = _clean_json(raw)
        data = json.loads(cleaned)
        data["raw_text"] = raw_text[:2000]
        return data
    except Exception as e:
        logger.warning(f"ScriptAgent: Research failed: {e}")
        return {
            "summary": topic_text or raw_text[:500],
            "key_points": [],
            "raw_text": raw_text[:2000],
        }


# ---------------------------------------------------------------------------
# Persona / Brand context builders
# ---------------------------------------------------------------------------

def _build_persona_context(persona) -> str:
    """Build a voice-priming block from a UserPersona instance."""
    if persona and persona.ai_prompt_summary:
        return persona.ai_prompt_summary

    if not persona:
        return ""

    # Fallback: build from individual fields
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


def _build_brand_block(brand) -> str:
    """Build a brand context block from a Brand model instance."""
    if not brand:
        return ""
    parts = [f"Brand: {brand.name}"]
    if brand.tagline:
        parts.append(f"Tagline: {brand.tagline}")
    if brand.target_audience:
        parts.append(f"Target audience: {brand.target_audience}")
    if brand.visual_style:
        parts.append(f"Visual style: {brand.visual_style}")
    if brand.pillars:
        parts.append(f"Content pillars: {', '.join(brand.pillars)}")
    if brand.never_do:
        parts.append(f"Never do: {brand.never_do}")
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Core: write_script (single) and write_scripts (batch)
# ---------------------------------------------------------------------------

def write_script(
    topic: str,
    script_type: str = "tiktok_hook",
    *,
    persona_id: Optional[int] = None,
    persona: object = None,
    brand_id: Optional[int] = None,
    brand: object = None,
    num_variants: int = 3,
    extra_instructions: str = "",
    research_summary: str = "",
) -> ScriptBatch:
    """Generate viral script variants for a given topic in the user's voice.

    Args:
        topic: The subject / idea / brief for the script.
        script_type: Key from SCRIPT_TYPES (e.g. "tiktok_hook", "ad_script").
        persona_id: Load UserPersona by ID (or pass persona object directly).
        persona: UserPersona instance (takes priority over persona_id).
        brand_id: Load Brand by ID (or pass brand object directly).
        brand: Brand instance (takes priority over brand_id).
        num_variants: How many script variants to generate (1-5).
        extra_instructions: Freeform user instructions appended to the prompt.
        research_summary: Pre-researched context to feed the AI.

    Returns:
        ScriptBatch with the generated scripts.
    """
    # Clamp variants
    num_variants = max(1, min(5, num_variants))

    # Resolve persona
    if persona is None and persona_id:
        from ..models.user_persona import UserPersona
        from ..extensions import db as _db
        persona = _db.session.get(UserPersona, persona_id)

    # Resolve brand
    if brand is None and brand_id:
        from ..models import Brand
        from ..extensions import db as _db
        brand = _db.session.get(Brand, brand_id)

    # Look up script type config
    type_config = SCRIPT_TYPES.get(script_type, SCRIPT_TYPES["tiktok_hook"])

    # Build context blocks
    persona_block = _build_persona_context(persona)
    brand_block = _build_brand_block(brand)

    persona_section = ""
    if persona_block:
        persona_section = f"""
--- VOICE & PERSONALITY (write exactly like this person) ---
{persona_block}
---
CRITICAL: You MUST write in this person's authentic voice. Match their tone,
vocabulary, sentence patterns, and energy level. If they're casual, be casual.
If they use slang, use slang. If they're formal, be formal. Mirror their
sample phrases for rhythm and style."""

    brand_section = ""
    if brand_block:
        brand_section = f"\n\n--- BRAND CONTEXT ---\n{brand_block}"

    research_section = ""
    if research_summary:
        research_section = f"\n\n--- RESEARCH MATERIAL ---\n{research_summary}"

    extra_section = ""
    if extra_instructions:
        extra_section = f"\n\n--- ADDITIONAL INSTRUCTIONS ---\n{extra_instructions}"

    prompt = f"""You are a world-class viral content scriptwriter who specialises in
short-form video content. You study what makes TikTok, YouTube Shorts, and
Instagram Reels go viral — hooks, pacing, pattern interrupts, emotional beats.
{persona_section}{brand_section}{research_section}{extra_section}

TOPIC: {topic}

SCRIPT FORMAT: {type_config['label']}
FORMAT DESCRIPTION: {type_config['structure']}
STRUCTURE:
{type_config['example_format']}

Write {num_variants} different script variant(s) for this topic.
Each variant should take a DIFFERENT creative angle:
- Variant 1: Direct / authoritative approach
{"- Variant 2: Story-driven / personal approach" if num_variants >= 2 else ""}
{"- Variant 3: Contrarian / surprising approach" if num_variants >= 3 else ""}
{"- Variant 4: Humorous / entertaining approach" if num_variants >= 4 else ""}
{"- Variant 5: Emotional / inspirational approach" if num_variants >= 5 else ""}

RULES:
1. Every script MUST start with a killer hook (the first 1-2 seconds).
2. Use short, punchy sentences. No filler. Every word earns its place.
3. Write for SPOKEN delivery — use contractions, natural pauses, emphasis cues.
4. Include [VISUAL CUE] directions in brackets where relevant.
5. End with a clear, specific call-to-action.
6. Match the persona's voice EXACTLY if one is provided.
7. Keep each script within ~{type_config['max_seconds'] or 60} seconds of spoken time.

Output ONLY a JSON array. Each item:
{{
    "hook": "the first line / attention grabber",
    "body": "the full script text (including the hook)",
    "estimated_seconds": <integer>,
    "notes": "1-sentence tip on delivery"
}}

No markdown fences. No explanation. Just the JSON array."""

    try:
        raw = _call_gemini(prompt)
        cleaned = _clean_json(raw)
        scripts_data = json.loads(cleaned)
    except json.JSONDecodeError:
        logger.warning("ScriptAgent: Failed to parse script JSON, attempting line split")
        # Attempt to recover by finding the JSON array in the response
        match = re.search(r"\[.*\]", raw, re.DOTALL)
        if match:
            try:
                scripts_data = json.loads(match.group(0))
            except json.JSONDecodeError:
                scripts_data = []
        else:
            scripts_data = []
    except Exception as e:
        logger.error(f"ScriptAgent: Script generation failed: {e}")
        scripts_data = []

    # Build result objects
    results = []
    for item in scripts_data[:num_variants]:
        body = item.get("body", "")
        results.append(ScriptResult(
            script_type=script_type,
            label=type_config["label"],
            body=body,
            hook=item.get("hook", body.split("\n")[0] if body else ""),
            estimated_seconds=item.get("estimated_seconds", 0),
            word_count=len(body.split()),
            notes=item.get("notes", ""),
        ))

    # If nothing was generated, return a fallback
    if not results:
        results.append(ScriptResult(
            script_type=script_type,
            label=type_config["label"],
            body="Script generation failed. Please try again with a different topic or check your API key.",
            hook="",
            notes="Error: could not parse AI response.",
        ))

    batch = ScriptBatch(
        topic=topic,
        persona_name=persona.name if persona else "Default",
        scripts=results,
        research_summary=research_summary,
        cost=0.0,  # Gemini Flash is effectively free
    )

    logger.info(
        f"ScriptAgent: Generated {len(results)} {script_type} scripts "
        f"for topic '{topic[:60]}…'"
    )
    return batch


def write_scripts_multi(
    topic: str,
    script_types: List[str],
    *,
    persona_id: Optional[int] = None,
    persona: object = None,
    brand_id: Optional[int] = None,
    brand: object = None,
    variants_per_type: int = 2,
    extra_instructions: str = "",
    research_summary: str = "",
) -> Dict[str, ScriptBatch]:
    """Generate scripts across multiple formats for the same topic.

    Useful when a recipe needs e.g. both a TikTok hook and a full ad script
    for the same product/topic.

    Returns:
        dict mapping script_type -> ScriptBatch
    """
    # Resolve persona once
    if persona is None and persona_id:
        from ..models.user_persona import UserPersona
        from ..extensions import db as _db
        persona = _db.session.get(UserPersona, persona_id)

    if brand is None and brand_id:
        from ..models import Brand
        from ..extensions import db as _db
        brand = _db.session.get(Brand, brand_id)

    results = {}
    for stype in script_types:
        if stype not in SCRIPT_TYPES:
            logger.warning(f"ScriptAgent: Unknown script type '{stype}', skipping")
            continue
        batch = write_script(
            topic=topic,
            script_type=stype,
            persona=persona,
            brand=brand,
            num_variants=variants_per_type,
            extra_instructions=extra_instructions,
            research_summary=research_summary,
        )
        results[stype] = batch

    return results


# ---------------------------------------------------------------------------
# Convenience: research then write (single call)
# ---------------------------------------------------------------------------

def research_and_write(
    url: str = "",
    topic_text: str = "",
    script_type: str = "tiktok_hook",
    *,
    persona_id: Optional[int] = None,
    persona: object = None,
    brand_id: Optional[int] = None,
    brand: object = None,
    num_variants: int = 3,
    extra_instructions: str = "",
) -> ScriptBatch:
    """Two-step convenience: research a topic, then write scripts.

    Combines research_topic() + write_script() into one call.
    """
    research = research_topic(
        url=url,
        topic_text=topic_text,
        extra_context=extra_instructions,
    )

    summary = research.get("summary", topic_text)
    key_points = research.get("key_points", [])
    if key_points:
        summary += "\n\nKey points:\n" + "\n".join(f"• {p}" for p in key_points)

    batch = write_script(
        topic=topic_text or summary,
        script_type=script_type,
        persona_id=persona_id,
        persona=persona,
        brand_id=brand_id,
        brand=brand,
        num_variants=num_variants,
        extra_instructions=extra_instructions,
        research_summary=summary,
    )
    batch.research_summary = summary
    return batch


# ---------------------------------------------------------------------------
# Rewrite / improve an existing script
# ---------------------------------------------------------------------------

def rewrite_script(
    original_script: str,
    feedback: str = "",
    script_type: str = "tiktok_hook",
    *,
    persona_id: Optional[int] = None,
    persona: object = None,
    brand_id: Optional[int] = None,
    brand: object = None,
) -> ScriptResult:
    """Rewrite / improve an existing script based on user feedback.

    Returns a single improved ScriptResult.
    """
    # Resolve persona
    if persona is None and persona_id:
        from ..models.user_persona import UserPersona
        from ..extensions import db as _db
        persona = _db.session.get(UserPersona, persona_id)

    if brand is None and brand_id:
        from ..models import Brand
        from ..extensions import db as _db
        brand = _db.session.get(Brand, brand_id)

    type_config = SCRIPT_TYPES.get(script_type, SCRIPT_TYPES["tiktok_hook"])
    persona_block = _build_persona_context(persona)
    brand_block = _build_brand_block(brand)

    persona_section = ""
    if persona_block:
        persona_section = f"\n\n--- VOICE (match this exactly) ---\n{persona_block}"

    brand_section = ""
    if brand_block:
        brand_section = f"\n\n--- BRAND ---\n{brand_block}"

    feedback_section = ""
    if feedback:
        feedback_section = f"\n\nUSER FEEDBACK: {feedback}"

    prompt = f"""You are an expert script editor. Rewrite and improve this script.
{persona_section}{brand_section}

ORIGINAL SCRIPT:
{original_script}
{feedback_section}

FORMAT: {type_config['label']}

Improve the script by:
1. Sharpening the hook (must grab attention in <2 seconds)
2. Tightening the pacing (cut filler, every word earns its place)
3. Strengthening the CTA
4. Matching the persona's voice more closely (if provided)
5. Applying the user's feedback (if provided)

Output ONLY a JSON object:
{{
    "hook": "the improved first line",
    "body": "the full improved script",
    "estimated_seconds": <integer>,
    "notes": "what you changed and why (1-2 sentences)"
}}

No markdown fences. No explanation. Just the JSON object."""

    try:
        raw = _call_gemini(prompt)
        cleaned = _clean_json(raw)
        data = json.loads(cleaned)
    except Exception as e:
        logger.error(f"ScriptAgent: Rewrite failed: {e}")
        return ScriptResult(
            script_type=script_type,
            label=type_config["label"],
            body=original_script,
            notes=f"Rewrite failed: {e}",
        )

    body = data.get("body", original_script)
    return ScriptResult(
        script_type=script_type,
        label=type_config["label"],
        body=body,
        hook=data.get("hook", body.split("\n")[0] if body else ""),
        estimated_seconds=data.get("estimated_seconds", 0),
        word_count=len(body.split()),
        notes=data.get("notes", ""),
    )


# ---------------------------------------------------------------------------
# Generate scene descriptions from a script (for image/video gen)
# ---------------------------------------------------------------------------

def script_to_scenes(
    script: str,
    num_scenes: int = 3,
    aspect_ratio: str = "9:16",
    *,
    brand_id: Optional[int] = None,
    brand: object = None,
    persona_id: Optional[int] = None,
    persona: object = None,
) -> List[dict]:
    """Break a script into visual scene descriptions for image/video generation.

    Args:
        script: The full script text to decompose into scenes.
        num_scenes: Number of scenes to produce (default 3).
        aspect_ratio: Target aspect ratio, e.g. ``"9:16"`` or ``"16:9"``.
        brand_id: Load Brand by ID (or pass *brand* directly).
        brand: Brand model instance (takes priority over *brand_id*).
        persona_id: Load UserPersona by ID (or pass *persona* directly).
        persona: UserPersona instance (takes priority over *persona_id*).

    Returns a list of dicts::

        [
            {
                "scene_number": 1,
                "timestamp": "0-5s",
                "script_line": "the text spoken in this scene",
                "visual_prompt": "detailed image/video generation prompt",
            },
            …
        ]
    """
    if brand is None and brand_id:
        from ..models import Brand
        from ..extensions import db as _db
        brand = _db.session.get(Brand, brand_id)

    if persona is None and persona_id:
        from ..models.user_persona import UserPersona
        from ..extensions import db as _db
        persona = _db.session.get(UserPersona, persona_id)

    brand_block = _build_brand_block(brand)
    brand_section = ""
    if brand_block:
        brand_section = f"\n\nBrand context:\n{brand_block}"

    persona_block = _build_persona_context(persona)
    persona_section = ""
    if persona_block:
        persona_section = (
            f"\n\nCreator persona (visual style should match their vibe):\n"
            f"{persona_block[:500]}"
        )

    prompt = f"""You are a storyboard artist breaking a video script into visual scenes.
{brand_section}{persona_section}

SCRIPT:
{script}

Break this into exactly {num_scenes} visual scenes.
Aspect ratio: {aspect_ratio}

For each scene, write a DETAILED image/video generation prompt that:
1. Describes the exact visual composition (subject, setting, framing)
2. Specifies lighting, mood, and color palette
3. Matches the script's emotional beat at that moment
4. Works as a standalone prompt for an AI image generator
5. Incorporates brand colors/style if provided

Output ONLY a JSON array:
[
    {{
        "scene_number": 1,
        "timestamp": "0-5s",
        "script_line": "the text spoken during this scene",
        "visual_prompt": "detailed scene description for image generation"
    }}
]

No markdown fences. No explanation."""

    try:
        raw = _call_gemini(prompt)
        cleaned = _clean_json(raw)
        scenes = json.loads(cleaned)
        if isinstance(scenes, list):
            return scenes[:num_scenes]
    except Exception as e:
        logger.error(f"ScriptAgent: Scene breakdown failed: {e}")

    # Fallback: split script evenly
    lines = [l.strip() for l in script.strip().split("\n") if l.strip()]
    chunk_size = max(1, len(lines) // num_scenes)
    fallback_scenes = []
    for i in range(num_scenes):
        start = i * chunk_size
        chunk = " ".join(lines[start:start + chunk_size])
        fallback_scenes.append({
            "scene_number": i + 1,
            "timestamp": f"{i * 5}-{(i + 1) * 5}s",
            "script_line": chunk,
            "visual_prompt": f"Scene depicting: {chunk[:200]}",
        })
    return fallback_scenes


# ---------------------------------------------------------------------------
# Public helpers for template use
# ---------------------------------------------------------------------------

def get_script_types() -> Dict[str, dict]:
    """Return the SCRIPT_TYPES dictionary (for dropdowns / UI)."""
    return SCRIPT_TYPES


def get_script_type_choices() -> List[dict]:
    """Return script types as a list of {value, label} for select dropdowns."""
    return [
        {"value": key, "label": cfg["label"]}
        for key, cfg in SCRIPT_TYPES.items()
    ]
