"""Style preset definitions and prompt builder for image generation."""

STYLE_PRESETS = {
    "pop_art": {
        "name": "Pop Art",
        "description": "Bold colors, high contrast, comic-inspired",
        "icon": "palette",
        "prompt_fragment": "Pop art style, bold primary colors, high contrast, thick black outlines, comic book inspired, halftone dot patterns",
        "camera": "clean studio shot, flat lighting, bold shadows",
    },
    "minimalist": {
        "name": "Minimalist",
        "description": "Clean, simple, lots of white space",
        "icon": "circle",
        "prompt_fragment": "Minimalist composition, clean white background, single subject centered, ample negative space, soft natural lighting",
        "camera": "centered composition, soft diffused lighting, clean background",
    },
    "corporate": {
        "name": "Corporate",
        "description": "Professional, polished, business-ready",
        "icon": "briefcase",
        "prompt_fragment": "Professional corporate photography, clean composition, subtle gradient background, polished and business-ready",
        "camera": "professional DSLR, f/2.8, clean studio lighting, business context",
    },
    "ugc": {
        "name": "UGC (User Generated)",
        "description": "Authentic, iPhone-shot, casual feel",
        "icon": "phone",
        "prompt_fragment": "Amateur iPhone photo, candid UGC style, authentic and unpolished, natural skin texture, slightly uneven framing",
        "camera": "amateur iPhone selfie, uneven framing, natural daylight",
    },
    "flat_lay": {
        "name": "Flat Lay",
        "description": "Overhead product arrangement",
        "icon": "camera",
        "prompt_fragment": "Overhead flat lay composition, products neatly arranged on textured surface, top-down perspective, styled with props",
        "camera": "top-down overhead, soft even lighting, no harsh shadows",
    },
    "cinematic": {
        "name": "Cinematic",
        "description": "Movie-quality, dramatic lighting",
        "icon": "film",
        "prompt_fragment": "Cinematic photography, dramatic lighting with deep shadows, anamorphic lens look, film grain, color graded, moody",
        "camera": "ARRI Alexa look, 35mm anamorphic, shallow DOF, cinematic color grade",
    },
}


def build_prompt(style_preset, brand, post, custom_prompt=None):
    """
    Build an image-generation prompt. Uses AI agent when available,
    falls back to template-based prompt.
    """
    if custom_prompt:
        return custom_prompt

    # Try AI agent for smart prompt generation
    try:
        from .agent_service import build_smart_prompt
        from ..models.campaign import Campaign
        from ..extensions import db
        campaign = db.session.get(Campaign, post.campaign_id) if post.campaign_id else None
        if brand and campaign:
            return build_smart_prompt(brand, post, campaign)
    except Exception:
        pass  # Fall back to template

    return build_prompt_template(style_preset, brand, post)


def build_prompt_template(style_preset, brand, post):
    """Template-based prompt builder (fallback when AI agent is unavailable)."""
    preset = STYLE_PRESETS.get(style_preset, STYLE_PRESETS["minimalist"])

    parts = []

    aspect_ratio = getattr(post, "aspect_ratio", None) or "9:16"
    parts.append(f"Aspect ratio {aspect_ratio}.")
    parts.append(preset["prompt_fragment"] + ".")

    brand_colors = brand.colors if brand else []
    if brand_colors:
        parts.append(f"Brand color palette: {', '.join(brand_colors)}.")

    visual_style = getattr(brand, "visual_style", None)
    if visual_style:
        parts.append(f"Visual style: {visual_style}.")

    parts.append(f"Camera: {preset['camera']}.")

    content_pillar = getattr(post, "content_pillar", None)
    if content_pillar:
        parts.append(f"Content pillar: {content_pillar}.")

    image_type = getattr(post, "image_type", None)
    if image_type:
        parts.append(f"Image type: {image_type}.")

    return " ".join(parts)
