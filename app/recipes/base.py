"""BaseRecipe — abstract base class for every workflow recipe.

Each recipe subclass defines:
  - metadata (name, description, category, icon, cost label)
  - input_fields — what the user fills in
  - how_to_use — plain-English instructions
  - execute() — the actual step-by-step automation

The generic UI reads *input_fields* to render the form and calls *execute()*
to run the recipe, updating the RecipeRun row with progress along the way.
"""

from __future__ import annotations

import abc
from dataclasses import dataclass, field
from typing import Any, List, Optional


# ---------------------------------------------------------------------------
# Input field descriptor — drives the generic form renderer
# ---------------------------------------------------------------------------

@dataclass
class InputField:
    """One input the user must provide when running a recipe."""

    name: str  # Internal key (snake_case)
    label: str  # Human-readable label shown in the UI
    field_type: str  # text, textarea, number, select, file, checkbox
    required: bool = True
    placeholder: str = ""
    help_text: str = ""
    default: Any = None
    options: List[dict] = field(default_factory=list)
    # options example for select: [{"value": "9:16", "label": "Portrait (9:16)"}]
    accept: str = ""  # For file fields: e.g. "image/*,video/*"
    min_val: Optional[float] = None
    max_val: Optional[float] = None


# ---------------------------------------------------------------------------
# BaseRecipe ABC
# ---------------------------------------------------------------------------

class BaseRecipe(abc.ABC):
    """Every recipe must implement this interface."""

    # --- Class-level metadata (override in subclass) ---

    slug: str = ""  # unique key, e.g. "ad_video_maker"
    name: str = ""  # human-readable, e.g. "Ad Video Maker"
    short_description: str = ""  # one liner for the card
    description: str = ""  # longer paragraph for detail page
    category: str = "content_creation"
    # categories: content_creation, video_studio, repurpose, research, distribution
    icon: str = "🧪"
    estimated_cost: str = "Free"  # shown on the card
    how_to_use: str = ""  # Markdown-formatted instructions
    is_active: bool = True  # Set to False for stub/placeholder recipes

    # --- Input fields ---

    @abc.abstractmethod
    def get_input_fields(self) -> List[InputField]:
        """Return the list of InputField objects that the run form will render."""
        ...

    # --- Steps ---

    @abc.abstractmethod
    def get_steps(self) -> List[str]:
        """Return short labels for each step (drives the progress bar)."""
        ...

    # --- Execution ---

    @abc.abstractmethod
    def execute(self, inputs: dict, run_id: int, user_id: int,
                on_progress=None, brand=None, persona=None) -> dict:
        """Run the recipe end-to-end.

        Args:
            inputs: validated user inputs (keys match InputField.name)
            run_id: RecipeRun.id for saving intermediate state
            user_id: current user's id
            on_progress: callback(step_index: int, label: str) to report progress

        Returns:
            dict with at least {"outputs": [...], "cost": float}
        """
        ...

    # --- Pre-flight input validation ---

    def validate_inputs(self, inputs: dict) -> Optional[str]:
        """Validate inputs *before* the run is created.

        Override in subclasses to enforce cross-field rules (e.g. "at least
        one of script/brief is required").

        Returns
        -------
        None
            Inputs are valid — proceed with run creation.
        str
            Human-readable error message shown on the form.
        """
        return None  # Default: no extra validation

    # --- Helpers available to all recipes ---

    def report_progress(self, on_progress, step: int, label: str):
        """Convenience wrapper that safely calls the progress callback."""
        if on_progress:
            on_progress(step, label)

    @staticmethod
    def build_brand_context(brand) -> str:
        """Build a prompt-injection block from a Brand object.

        Returns an empty string if brand is None, so callers can simply
        concatenate: ``prompt + self.build_brand_context(brand)``.

        Includes ALL available brand data so the AI can produce truly
        on-brand output: colours, voice/tone, hashtags, caption template,
        logo reference, content pillars, visual style, and guidelines.
        """
        if brand is None:
            return ""

        import json
        parts = ["═══ BRAND CONTEXT ═══"]
        parts.append(f"Brand: {brand.name}")
        if brand.tagline:
            parts.append(f"Tagline: {brand.tagline}")

        # ── Colour palette (primary / secondary / tertiary) ──
        if brand.colors_json:
            try:
                colors = json.loads(brand.colors_json)
                if colors and isinstance(colors, list):
                    labels = ["Primary", "Secondary", "Tertiary",
                              "Accent 1", "Accent 2"]
                    color_lines = []
                    for i, c in enumerate(colors[:5]):
                        lbl = labels[i] if i < len(labels) else f"Color {i+1}"
                        color_lines.append(f"  {lbl}: {c}")
                    parts.append("Colour Palette:\n" + "\n".join(color_lines))
                    parts.append(
                        "IMPORTANT: Use these brand colours in backgrounds, "
                        "accents, clothing, props, or lighting. Never replace "
                        "them with random colours."
                    )
            except (json.JSONDecodeError, TypeError):
                pass

        # ── Brand voice / tone ──
        if brand.voice_json:
            try:
                voice = json.loads(brand.voice_json)
                if voice and isinstance(voice, dict):
                    voice_parts = []
                    for k, v in voice.items():
                        if v:
                            voice_parts.append(f"  {k.replace('_', ' ').title()}: {v}")
                    if voice_parts:
                        parts.append("Brand Voice:\n" + "\n".join(voice_parts))
            except (json.JSONDecodeError, TypeError):
                pass

        if brand.target_audience:
            parts.append(f"Target Audience: {brand.target_audience}")
        if brand.visual_style:
            parts.append(f"Visual Style: {brand.visual_style}")
        if brand.content_pillars:
            try:
                pillars = json.loads(brand.content_pillars)
                if pillars:
                    parts.append(f"Content Pillars: {', '.join(pillars)}")
            except (json.JSONDecodeError, TypeError):
                pass

        # ── Hashtags ──
        if brand.hashtags:
            try:
                tags = json.loads(brand.hashtags)
                if tags and isinstance(tags, list):
                    parts.append(f"Brand Hashtags: {' '.join(tags)}")
            except (json.JSONDecodeError, TypeError):
                pass

        # ── Caption template ──
        if brand.caption_template:
            parts.append(
                f"Caption Template (follow this structure):\n"
                f"  {brand.caption_template}"
            )

        # ── Logo reference ──
        if brand.logo_path:
            parts.append(
                "Logo: Brand logo is available — reference it in scenes "
                "where logo placement is appropriate."
            )

        if brand.never_do:
            parts.append(f"NEVER DO: {brand.never_do}")
        if brand.brand_doc:
            # Include first ~800 chars of brand doc for richer context
            doc_preview = brand.brand_doc[:800]
            if len(brand.brand_doc) > 800:
                doc_preview += "…"
            parts.append(f"Brand Guidelines:\n{doc_preview}")
        parts.append("═══ END BRAND CONTEXT ═══\n")
        return "\n".join(parts)

    @staticmethod
    def get_brand_reference_paths(brand, purpose: str = None, limit: int = 5) -> list:
        """Return local file paths for a brand's reference images.

        Args:
            brand: Brand model instance (or None).
            purpose: Filter by purpose ('product', 'mood', 'style_reference').
                     None = all purposes.
            limit: Maximum number of paths to return.

        Returns:
            List of file paths that exist on disk, up to *limit* entries.
        """
        if brand is None:
            return []
        import os
        from app.models.reference_image import ReferenceImage
        query = ReferenceImage.query.filter_by(brand_id=brand.id)
        if purpose:
            query = query.filter_by(purpose=purpose)
        refs = query.order_by(ReferenceImage.created_at.desc()).limit(limit).all()
        return [r.file_path for r in refs if r.file_path and os.path.exists(r.file_path)]

    @staticmethod
    def build_persona_context(persona) -> str:
        """Build a prompt-injection block from a UserPersona object.

        Returns an empty string if persona is None.

        Includes ALL available persona data so the AI can faithfully
        adopt the character's voice, tone, and personality.
        """
        if persona is None:
            return ""

        parts = ["═══ PERSONA / VOICE CONTEXT ═══"]
        parts.append(f"Persona: {persona.name}")
        if persona.bio:
            parts.append(f"Bio / Background: {persona.bio}")
        if persona.tone:
            parts.append(f"Tone: {persona.tone}")
        if persona.voice_style:
            parts.append(f"Voice Style: {persona.voice_style}")
        if persona.target_audience:
            parts.append(f"Speaking To: {persona.target_audience}")
        if persona.industry:
            parts.append(f"Industry: {persona.industry}")
        if persona.writing_guidelines:
            parts.append(f"Writing Rules: {persona.writing_guidelines}")
        if persona.sample_phrases:
            parts.append(f"Example Phrases: {', '.join(persona.sample_phrases[:5])}")
        if persona.brand_keywords:
            parts.append(f"Always Use Words: {', '.join(persona.brand_keywords[:10])}")
        if persona.avoid_words:
            parts.append(f"Never Use Words: {', '.join(persona.avoid_words[:10])}")
        if persona.ai_prompt_summary:
            parts.append(f"Voice Summary: {persona.ai_prompt_summary}")
        parts.append(
            "IMPORTANT: All captions, ad copy, and text must match this "
            "persona's tone and style. Never deviate from their voice."
        )
        parts.append("═══ END PERSONA CONTEXT ═══\n")
        return "\n".join(parts)

    @staticmethod
    def build_creative_directives(*, generation_type: str = "image",
                                   style_hint: str = "") -> str:
        """Return universal creative quality directives for AI prompts.

        These rules are distilled from production-grade system prompts
        (R38 UGC Ads Factory, Split AI Image Ad Generator, R44 Influencer
        Toolkit) and ensure every generated asset is on-brand, diverse,
        and high-quality.

        Args:
            generation_type: "image", "video", or "text"
            style_hint: "ugc" for UGC-style output, "" for default

        Returns:
            A directive block that should be appended to any AI prompt.
        """
        parts = ["\n═══ CREATIVE QUALITY DIRECTIVES ═══"]

        # ── Brand fidelity ──
        parts.append(
            "BRAND FIDELITY:\n"
            "- NEVER alter the colour or any part of the product.\n"
            "- If brand colours are provided, weave them into the scene "
            "(backgrounds, accents, clothing, props, lighting).\n"
            "- If a design peg or reference image is provided, adjust "
            "colours in the scene to fit the brand's colour palette.\n"
            "- Respect the brand's visual style, target audience, and "
            "content pillars at all times."
        )

        # ── Diversity & inclusion ──
        parts.append(
            "DIVERSITY & INCLUSION:\n"
            "- Ensure diversity in gender, ethnicity, and hair colour.\n"
            "- Default age range: 21–38 unless the brand specifies otherwise.\n"
            "- Show visible imperfections for realism (blemishes, uneven "
            "skin, natural features)."
        )

        # ── Prompt hygiene ──
        parts.append(
            "PROMPT RULES:\n"
            "- Do NOT use double quotes inside image or video prompts.\n"
            "- Keep ad copy short, punchy, and action-oriented (max 7 words).\n"
            "- If a caption template is provided, follow that structure.\n"
            "- If brand hashtags are provided, incorporate them naturally."
        )

        # ── UGC-specific directives ──
        if style_hint == "ugc":
            parts.append(
                "UGC AUTHENTICITY:\n"
                "- All outputs must feel natural, candid, and unpolished.\n"
                "- Use amateur iPhone photo/video style keywords: "
                "'unremarkable amateur iPhone photos', 'reddit image', "
                "'snapchat video', 'casual iPhone selfie', 'slightly uneven "
                "framing', 'authentic share, slightly blurry', 'amateur "
                "quality phone photo'.\n"
                "- Everyday realism with authentic, relatable settings.\n"
                "- Slightly imperfect framing and lighting.\n"
                "- Candid poses and genuine expressions.\n"
                "- Real-world environments left as-is (clutter, busy backgrounds)."
            )

        # ── Generation-type-specific ──
        if generation_type == "image":
            parts.append(
                "IMAGE QUALITY:\n"
                "- Be specific: describe subject, setting, composition, "
                "camera angle, lighting, mood, colour palette, textures.\n"
                "- Avoid vague adjectives — every descriptor should be visual."
            )
        elif generation_type == "video":
            parts.append(
                "VIDEO QUALITY:\n"
                "- Describe camera movement explicitly: 'slow dolly push-in', "
                "'orbit left 90°', 'crane up revealing the scene'.\n"
                "- Specify motion, lighting transitions, atmosphere changes, "
                "and pacing.\n"
                "- For dialogue: use '...' for pauses, avoid special "
                "characters like em dashes."
            )

        parts.append("═══ END CREATIVE DIRECTIVES ═══\n")
        return "\n".join(parts)
