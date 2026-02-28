"""Image Creator — AI-powered image generation with smart assistance.

Six enhancements over a basic prompt-to-image tool:
  A. AI Prompt Assistant — describe in plain English, AI writes the detailed prompt
  B. Reference Image Upload — upload a style/composition reference for AI vision
  C. Style Presets — Product Shot, Social Graphic, Lifestyle, Flat Lay, etc.
  D. Platform Selector — auto-sets aspect ratio + composition hints
  E. Negative Prompt — specify what to exclude
  F. Brand Photo Library — auto-pulls brand reference images

Security: All inputs are validated (prompt length, aspect ratio whitelist,
model whitelist, count whitelist, file upload extension whitelist).
Brand/persona context is injected into the prompt so the AI stays on-brand.
"""

import logging
import os

from .base import BaseRecipe, InputField

logger = logging.getLogger(__name__)

# ── Constants ──────────────────────────────────────────────────────────────

# Map UI model values → (internal model name, display label, provider hint)
_MODEL_MAP = {
    "nanobanana": ("nano-banana-pro", "Nano Banana Pro", "google"),
    "gpt-image-1.5": ("gpt-image-1.5", "GPT Image 1.5", "wavespeed"),
}

_VALID_RATIOS = {"1:1", "9:16", "16:9", "4:5", "3:4"}
_VALID_COUNTS = {"1", "2", "4"}

# Style presets — each provides a prompt fragment the AI uses
_STYLE_PRESETS = {
    "none": {
        "label": "None — I'll describe everything",
        "prompt_fragment": "",
    },
    "product_shot": {
        "label": "Product Shot",
        "prompt_fragment": (
            "Professional product photography on a clean, neutral background. "
            "Studio lighting with soft shadows. Sharp focus on the product, "
            "slightly elevated camera angle. Commercial-quality, ready for "
            "e-commerce or catalogue use."
        ),
    },
    "social_graphic": {
        "label": "Social Media Graphic",
        "prompt_fragment": (
            "Eye-catching social media visual with bold composition, vibrant "
            "colors, and clear focal point. Designed for high engagement — "
            "scroll-stopping aesthetic with modern, trendy styling."
        ),
    },
    "lifestyle": {
        "label": "Lifestyle Scene",
        "prompt_fragment": (
            "Lifestyle photography showing the subject in a natural, real-world "
            "setting. Warm, authentic feel. Candid composition with natural "
            "lighting. Think 'Instagram influencer' aesthetic."
        ),
    },
    "flat_lay": {
        "label": "Flat Lay",
        "prompt_fragment": (
            "Top-down flat lay composition on a styled surface. Carefully arranged "
            "with complementary props. Clean, organized aesthetic popular for "
            "Instagram product reveals and mood boards."
        ),
    },
    "abstract": {
        "label": "Abstract / Artistic",
        "prompt_fragment": (
            "Abstract, artistic visual with creative use of color, texture, and "
            "form. Experimental composition suitable for brand storytelling, "
            "backgrounds, or creative campaigns."
        ),
    },
    "portrait": {
        "label": "Portrait / Headshot",
        "prompt_fragment": (
            "Professional portrait or headshot with soft, flattering lighting. "
            "Shallow depth of field, clean background. Suitable for LinkedIn, "
            "team pages, or personal branding."
        ),
    },
    "infographic": {
        "label": "Infographic / Data Visual",
        "prompt_fragment": (
            "Clean infographic or data visualization with modern typography, "
            "icon-based layout, and clear visual hierarchy. Dark or white "
            "background with accent colors. Professional and informative."
        ),
    },
}

# Platform → (recommended aspect ratio, composition hint)
_PLATFORM_MAP = {
    "none": {
        "label": "No specific platform",
        "recommended_ratio": None,
        "hint": "",
    },
    "instagram_feed": {
        "label": "Instagram Feed Post",
        "recommended_ratio": "1:1",
        "hint": (
            "Optimise for Instagram feed: square composition, bold subject, "
            "attention-grabbing in a vertical scroll context. Leave space for "
            "optional text overlay."
        ),
    },
    "instagram_story": {
        "label": "Instagram Story / Reel",
        "recommended_ratio": "9:16",
        "hint": (
            "Full-screen vertical format for Stories/Reels. Subject centred, "
            "important elements away from top/bottom edges (safe zone). "
            "Punchy, immediate visual impact."
        ),
    },
    "linkedin": {
        "label": "LinkedIn Post",
        "recommended_ratio": "4:5",
        "hint": (
            "Professional LinkedIn context. Clean, corporate-friendly aesthetic. "
            "Vertical 4:5 for maximum feed real estate. Clear visual hierarchy."
        ),
    },
    "youtube_thumb": {
        "label": "YouTube Thumbnail",
        "recommended_ratio": "16:9",
        "hint": (
            "YouTube thumbnail at 16:9. High contrast, bold text-friendly, "
            "expressive face or dramatic subject. Must stand out at small sizes. "
            "Leave right third open for text if needed."
        ),
    },
    "tiktok": {
        "label": "TikTok",
        "recommended_ratio": "9:16",
        "hint": (
            "Vertical 9:16 for TikTok. Energetic, trend-aware, Gen-Z aesthetic. "
            "Vibrant colors, dynamic composition, main subject centred."
        ),
    },
    "facebook": {
        "label": "Facebook Post / Ad",
        "recommended_ratio": "1:1",
        "hint": (
            "Facebook feed optimised. Square or slight landscape. Clear subject, "
            "text-friendly negative space. Warm, inviting tones."
        ),
    },
    "twitter_x": {
        "label": "X (Twitter)",
        "recommended_ratio": "16:9",
        "hint": (
            "Landscape 16:9 for X/Twitter timeline. Concise visual message, "
            "high contrast for dark-mode readability."
        ),
    },
    "website_hero": {
        "label": "Website Hero Banner",
        "recommended_ratio": "16:9",
        "hint": (
            "Wide hero banner for website header. Atmospheric, cinematic. "
            "Space for headline text overlay on one side. Premium, polished look."
        ),
    },
}


class ImageCreator(BaseRecipe):
    slug = "image-creator"
    name = "Image Creator"
    short_description = "Describe what you need — the AI crafts the perfect image prompt and generates it."
    description = (
        "Tell the AI what you need in plain English, pick a style and platform, "
        "and optionally upload a reference image. The AI writes the perfect "
        "image prompt for you — incorporating your brand colours, persona voice, "
        "and visual style. Choose from free and premium models."
    )
    category = "content_creation"
    icon = "🖼️"
    estimated_cost = "Free – $0.10 per image"
    is_active = True

    how_to_use = """\
### How to use Image Creator

**Two modes:**

| Mode | Best For |
|------|----------|
| **🤖 Assisted** *(default)* | Describe what you want in plain English — the AI writes the detailed image prompt for you. No prompt-engineering skills needed. |
| **✍️ Manual** | You write the full image prompt yourself — for power users who want total control. |

**Steps:**
1. **Choose a mode** — Assisted (recommended) or Manual.
2. **Describe / write your prompt** — e.g. "a coffee shop ad for Instagram".
3. *(Optional)* **Upload a reference image** — the AI will analyse its style, composition, and colours.
4. *(Optional)* **Pick a style preset** — Product Shot, Lifestyle, Flat Lay, etc.
5. *(Optional)* **Pick a platform** — Instagram, LinkedIn, YouTube, etc. Auto-sets aspect ratio.
6. *(Optional)* **Add a negative prompt** — things you DON'T want in the image.
7. **Select a Brand and/or Persona** — your brand colours, style, and voice are injected automatically.
8. **Choose model and number of images**.
9. Click **Generate**.

**Available Models:**
| Model | Quality | Cost |
|-------|---------|------|
| Nano Banana Pro | Great | **Free** (Google AI) |
| GPT Image 1.5 | Excellent | ~$0.07 |

**Tips:**
- Start with **Assisted mode** — the AI writes better prompts than most humans.
- Upload a reference image of a competitor's ad or a mood board for style matching.
- The **Brand** injects your colours, audience, and guidelines.
- The **Persona** sets the tone for any text overlays or copy in the image.
- Use the free model to experiment, then switch to premium for final assets.
"""

    # ------------------------------------------------------------------
    # Input fields
    # ------------------------------------------------------------------

    def get_input_fields(self):
        return [
            InputField(
                name="creation_mode",
                label="Creation Mode",
                field_type="select",
                default="assisted",
                options=[
                    {"value": "assisted", "label": "🤖 Assisted — AI writes the prompt for you"},
                    {"value": "manual", "label": "✍️ Manual — write your own prompt"},
                ],
                help_text="Assisted mode: describe what you want in plain English. The AI writes the detailed prompt.",
            ),
            InputField(
                name="prompt",
                label="Your Description / Prompt",
                field_type="textarea",
                required=True,
                placeholder=(
                    "Assisted: \"A coffee shop ad showing our latte art, warm tones, "
                    "cozy morning vibe\"\n"
                    "Manual: \"A steaming latte with leaf art on a marble counter, "
                    "golden morning light through window, shallow DOF, 85mm lens\""
                ),
                help_text=(
                    "Assisted mode: just describe what you want. "
                    "Manual mode: write the full image generation prompt."
                ),
            ),
            InputField(
                name="reference_image",
                label="Reference Image (optional)",
                field_type="file",
                required=False,
                help_text=(
                    "Upload a reference photo — the AI analyses its style, colours, "
                    "and composition to guide the generation."
                ),
            ),
            InputField(
                name="style_preset",
                label="Style Preset",
                field_type="select",
                default="none",
                options=[
                    {"value": k, "label": v["label"]}
                    for k, v in _STYLE_PRESETS.items()
                ],
                help_text="Quick style direction — or choose 'None' to describe everything yourself.",
            ),
            InputField(
                name="platform",
                label="Platform / Use Case",
                field_type="select",
                default="none",
                options=[
                    {"value": k, "label": v["label"]}
                    for k, v in _PLATFORM_MAP.items()
                ],
                help_text="Auto-sets the best aspect ratio and composition for your target platform.",
            ),
            InputField(
                name="negative_prompt",
                label="Negative Prompt (optional)",
                field_type="textarea",
                required=False,
                placeholder="e.g. text, watermarks, people, blurry, low quality",
                help_text="List things you do NOT want in the image, comma-separated.",
            ),
            InputField(
                name="model",
                label="Model",
                field_type="select",
                default="nanobanana",
                options=[
                    {"value": "nanobanana", "label": "Nano Banana Pro — Free ✨"},
                    {"value": "gpt-image-1.5", "label": "GPT Image 1.5 — ~$0.07"},
                ],
                help_text="Start with the free model to experiment.",
            ),
            InputField(
                name="aspect_ratio",
                label="Aspect Ratio",
                field_type="select",
                default="1:1",
                options=[
                    {"value": "1:1", "label": "Square (1:1)"},
                    {"value": "9:16", "label": "Vertical (9:16)"},
                    {"value": "16:9", "label": "Horizontal (16:9)"},
                    {"value": "4:5", "label": "Portrait (4:5)"},
                    {"value": "3:4", "label": "Tall Portrait (3:4)"},
                ],
                help_text="Tip: if you selected a Platform above, this is auto-recommended.",
            ),
            InputField(
                name="image_count",
                label="How many images?",
                field_type="select",
                default="1",
                options=[
                    {"value": "1", "label": "1 image"},
                    {"value": "2", "label": "2 images"},
                    {"value": "4", "label": "4 images"},
                ],
            ),
        ]

    def get_steps(self):
        return [
            "Analysing inputs",
            "Crafting image prompt",
            "Generating images",
            "Processing output",
        ]

    # ------------------------------------------------------------------
    # Gemini helpers (same pattern as AdVideoMaker/PhotoToAd)
    # ------------------------------------------------------------------

    @staticmethod
    def _call_gemini(prompt: str) -> str:
        from ..services.agent_service import _call_gemini
        return _call_gemini(prompt)

    @staticmethod
    def _call_gemini_vision(prompt: str, image_path: str) -> str:
        from ..services.agent_service import _call_gemini_with_image
        return _call_gemini_with_image(prompt, image_path)

    # ------------------------------------------------------------------
    # Execute
    # ------------------------------------------------------------------

    def execute(self, inputs, run_id, user_id, on_progress=None,
                brand=None, persona=None):
        """Generate AI images with smart prompt assistance.

        Supports assisted mode (AI writes prompt), reference image analysis,
        style presets, platform hints, negative prompts, and brand photo
        library injection.
        """
        from tools.create_image import generate_ugc_image
        from tools.config import get_cost

        # ── Read & validate inputs ────────────────────────────────────
        raw_prompt = (inputs.get("prompt") or "").strip()
        if not raw_prompt:
            raise ValueError("A description or prompt is required.")

        creation_mode = inputs.get("creation_mode", "assisted")
        if creation_mode not in ("assisted", "manual"):
            creation_mode = "assisted"

        reference_image = inputs.get("reference_image")  # file path or None
        if reference_image and not os.path.exists(reference_image):
            logger.warning("Reference image path does not exist: %s", reference_image)
            reference_image = None

        style_key = inputs.get("style_preset", "none")
        if style_key not in _STYLE_PRESETS:
            style_key = "none"
        style = _STYLE_PRESETS[style_key]

        platform_key = inputs.get("platform", "none")
        if platform_key not in _PLATFORM_MAP:
            platform_key = "none"
        platform = _PLATFORM_MAP[platform_key]

        negative_prompt = (inputs.get("negative_prompt") or "").strip()

        model_key = inputs.get("model", "nanobanana")
        if model_key not in _MODEL_MAP:
            logger.warning("Unknown model '%s', falling back to nanobanana", model_key)
            model_key = "nanobanana"
        model_name, model_label, provider = _MODEL_MAP[model_key]

        # Aspect ratio: use platform recommendation if user left default
        aspect_ratio = inputs.get("aspect_ratio", "1:1")
        if aspect_ratio not in _VALID_RATIOS:
            aspect_ratio = "1:1"
        # Auto-apply platform recommendation if user hasn't explicitly changed it
        if platform["recommended_ratio"] and aspect_ratio == "1:1":
            aspect_ratio = platform["recommended_ratio"]

        count_str = inputs.get("image_count", "1")
        if count_str not in _VALID_COUNTS:
            count_str = "1"
        image_count = int(count_str)

        outputs = []

        # ── Step 0: Analyse inputs ────────────────────────────────────
        self.report_progress(on_progress, 0, "Analysing inputs…")

        # Build brand & persona context
        brand_ctx = self.build_brand_context(brand)
        persona_ctx = self.build_persona_context(persona)

        # Analyse reference image (if uploaded)
        reference_analysis = ""
        if reference_image:
            self.report_progress(on_progress, 0, "Analysing reference image…")
            try:
                reference_analysis = self._call_gemini_vision(
                    "You are an expert art director analysing a reference image.\n"
                    "Describe in detail:\n"
                    "1. Colour palette (list the main colours)\n"
                    "2. Composition and framing\n"
                    "3. Lighting style and mood\n"
                    "4. Visual style / aesthetic\n"
                    "5. Key elements and their arrangement\n"
                    "6. Overall feel and brand impression\n\n"
                    "Be specific and concise. This analysis will be used to guide "
                    "AI image generation to match this reference's style.",
                    reference_image,
                )
                outputs.append({
                    "type": "text",
                    "title": "🔍 Reference Image Analysis",
                    "value": reference_analysis,
                })
                logger.info("Reference image analysed for run %s", run_id)
            except Exception as exc:
                logger.warning("Reference image analysis failed: %s", exc)
                reference_analysis = ""
                outputs.append({
                    "type": "text",
                    "title": "⚠️ Reference Analysis",
                    "value": f"Could not analyse reference image: {exc}. Proceeding without it.",
                })

        # Collect brand reference images (Feature F)
        reference_paths = []
        if reference_image:
            reference_paths.append(reference_image)

        brand_refs = self.get_brand_reference_paths(brand, purpose="style_reference", limit=3)
        if brand_refs:
            reference_paths.extend(brand_refs)
            logger.info("Added %d brand reference image(s)", len(brand_refs))

        reference_paths = reference_paths or None

        # ── Step 1: Craft the image prompt ────────────────────────────
        self.report_progress(on_progress, 1, "Crafting image prompt…")

        if creation_mode == "assisted":
            final_prompt = self._build_assisted_prompt(
                user_description=raw_prompt,
                style=style,
                platform=platform,
                negative_prompt=negative_prompt,
                reference_analysis=reference_analysis,
                brand_ctx=brand_ctx,
                persona_ctx=persona_ctx,
                aspect_ratio=aspect_ratio,
            )
            outputs.append({
                "type": "text",
                "title": "✨ AI-Crafted Prompt",
                "value": final_prompt,
            })
        else:
            # Manual mode — use the raw prompt, but still enrich with context
            final_prompt = self._build_manual_prompt(
                raw_prompt=raw_prompt,
                style=style,
                platform=platform,
                negative_prompt=negative_prompt,
                reference_analysis=reference_analysis,
                brand_ctx=brand_ctx,
                persona_ctx=persona_ctx,
            )

        # ── Step 2: Generate images ───────────────────────────────────
        self.report_progress(on_progress, 2,
                             f"Generating {image_count} image(s) via {model_label}…")

        total_cost = 0.0

        for i in range(image_count):
            if image_count > 1:
                self.report_progress(
                    on_progress, 2,
                    f"Generating image {i + 1}/{image_count} via {model_label}…"
                )

            try:
                result = generate_ugc_image(
                    prompt=final_prompt,
                    reference_paths=reference_paths,
                    aspect_ratio=aspect_ratio,
                    model=model_name,
                    provider=provider,
                )
            except Exception as exc:
                logger.error("Image generation failed (%d/%d): %s",
                             i + 1, image_count, exc, exc_info=True)
                outputs.append({
                    "type": "text",
                    "title": f"Image {i + 1} — Error",
                    "value": f"⚠️ Generation failed: {exc}",
                })
                continue

            status = result.get("status", "")
            image_url = result.get("result_url", "")

            if status == "success" and image_url:
                outputs.append({
                    "type": "image",
                    "title": (f"Generated Image {i + 1}"
                              if image_count > 1 else "Generated Image"),
                    "url": image_url,
                })
                unit_cost = get_cost(model_name, provider)
                total_cost += unit_cost
            else:
                error_detail = result.get("error", "Unknown error")
                outputs.append({
                    "type": "text",
                    "title": f"Image {i + 1} — Error",
                    "value": f"⚠️ Status '{status}': {error_detail}",
                })

        # ── Step 3: Summary ───────────────────────────────────────────
        self.report_progress(on_progress, 3, "Processing output…")

        if not any(o["type"] == "image" for o in outputs):
            outputs.append({
                "type": "text",
                "title": "Error",
                "value": "⚠️ No images were generated. Please try again.",
            })

        success_count = sum(1 for o in outputs if o["type"] == "image")
        summary_lines = [
            f"**Mode:** {'🤖 Assisted' if creation_mode == 'assisted' else '✍️ Manual'}",
            f"**Model:** {model_label}",
            f"**Aspect Ratio:** {aspect_ratio}",
        ]
        if style_key != "none":
            summary_lines.append(f"**Style:** {style['label']}")
        if platform_key != "none":
            summary_lines.append(f"**Platform:** {platform['label']}")
        if reference_image:
            summary_lines.append("**Reference Image:** ✅ Analysed")
        if negative_prompt:
            summary_lines.append(f"**Exclude:** {negative_prompt[:100]}")
        summary_lines.extend([
            f"**Requested:** {image_count} image(s)",
            f"**Generated:** {success_count} image(s)",
            f"**Cost:** ${total_cost:.2f}",
        ])
        if brand:
            summary_lines.append(f"**Brand:** {brand.name}")
        if persona:
            summary_lines.append(f"**Persona:** {persona.name}")
        if brand_refs:
            summary_lines.append(
                f"**Brand Photos Used:** {len(brand_refs)} reference(s)"
            )

        outputs.insert(0, {
            "type": "text",
            "title": "Generation Summary",
            "value": "\n".join(summary_lines),
        })

        return {"outputs": outputs, "cost": total_cost}

    # ------------------------------------------------------------------
    # Prompt builders
    # ------------------------------------------------------------------

    def _build_assisted_prompt(self, *, user_description, style, platform,
                                negative_prompt, reference_analysis,
                                brand_ctx, persona_ctx, aspect_ratio):
        """Use Gemini to craft a detailed image prompt from plain English.

        This is the AI Prompt Assistant (Feature A) — the core differentiator
        that makes Image Creator valuable for non-technical users.
        """
        meta_prompt_parts = [
            "You are an expert art director and prompt engineer. "
            "Your job is to write a single, highly detailed image generation "
            "prompt based on the user's description and context below.\n",
        ]

        meta_prompt_parts.append(
            f"USER'S DESCRIPTION:\n\"{user_description}\"\n"
        )

        if style["prompt_fragment"]:
            meta_prompt_parts.append(
                f"STYLE DIRECTION:\n{style['prompt_fragment']}\n"
            )

        if platform["hint"]:
            meta_prompt_parts.append(
                f"PLATFORM CONTEXT ({platform['label']}):\n{platform['hint']}\n"
            )

        meta_prompt_parts.append(f"ASPECT RATIO: {aspect_ratio}\n")

        if reference_analysis:
            meta_prompt_parts.append(
                f"REFERENCE IMAGE ANALYSIS (match this style):\n"
                f"{reference_analysis}\n"
            )

        if brand_ctx:
            meta_prompt_parts.append(brand_ctx)

        if persona_ctx:
            meta_prompt_parts.append(persona_ctx)

        if negative_prompt:
            meta_prompt_parts.append(
                f"MUST EXCLUDE (negative prompt): {negative_prompt}\n"
            )

        # Determine if UGC style is selected
        style_hint = "ugc" if style.get("label", "").lower().startswith("ugc") else ""
        creative_directives = self.build_creative_directives(
            generation_type="image", style_hint=style_hint
        )
        meta_prompt_parts.append(creative_directives)

        meta_prompt_parts.append(
            "INSTRUCTIONS:\n"
            "1. Write a single, detailed image prompt (3–6 sentences).\n"
            "2. Describe: subject, setting/background, composition, camera angle, "
            "lighting, mood, colour palette, textures.\n"
            "3. Incorporate the style preset, platform context, and brand context "
            "naturally — don't just list them.\n"
            "4. If a reference image analysis is provided, match that visual style.\n"
            "5. If brand colours are provided, weave them into the scene "
            "(backgrounds, accents, clothing, props, lighting). "
            "NEVER use random colours when brand colours are available.\n"
            "6. NEVER alter the colour or any part of the product shown in "
            "the reference image.\n"
            "7. Respect every item in the negative prompt.\n"
            "8. Make the prompt specific and visual — avoid vague adjectives.\n"
            "9. Do NOT use double quotes inside the prompt.\n"
            "10. Ensure diversity in gender, ethnicity, and hair colour "
            "when people are part of the scene.\n\n"
            "OUTPUT: The image generation prompt ONLY — no labels, no quotes, "
            "no explanations, no markdown. Just the prompt text."
        )

        try:
            crafted = self._call_gemini("\n".join(meta_prompt_parts))
            # Clean up any stray quotes or labels
            crafted = crafted.strip().strip('"').strip("'")
            if crafted:
                return crafted
        except Exception as exc:
            logger.warning("AI prompt assistant failed: %s — using raw description", exc)

        # Fallback: use raw description + style fragment
        return self._build_manual_prompt(
            raw_prompt=user_description,
            style=style,
            platform=platform,
            negative_prompt=negative_prompt,
            reference_analysis=reference_analysis,
            brand_ctx=brand_ctx,
            persona_ctx=persona_ctx,
        )

    @staticmethod
    def _build_manual_prompt(*, raw_prompt, style, platform,
                              negative_prompt, reference_analysis,
                              brand_ctx, persona_ctx):
        """Build an enriched prompt for manual mode.

        Appends style, platform, brand/persona, and negative prompt context
        to the user's raw prompt text.
        """
        parts = [raw_prompt]

        if style["prompt_fragment"]:
            parts.append(f"\nStyle direction: {style['prompt_fragment']}")

        if platform["hint"]:
            parts.append(f"\nPlatform: {platform['hint']}")

        if reference_analysis:
            parts.append(
                f"\nMatch this reference style: {reference_analysis[:500]}"
            )

        if brand_ctx or persona_ctx:
            parts.append(
                "\n--- STYLE CONTEXT (incorporate into the visual) ---"
            )
            if brand_ctx:
                parts.append(brand_ctx)
            if persona_ctx:
                parts.append(persona_ctx)

        if negative_prompt:
            parts.append(f"\nDo NOT include: {negative_prompt}")

        return "\n".join(parts)
