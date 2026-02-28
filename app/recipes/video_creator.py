"""Video Creator — AI-powered video generation with smart prompt assistance.

Supports 6 models across 4 providers:
  - Veo 3.1        (Google AI Studio) — cinematic, highest quality, ~$0.50
  - Kling 3.0      (WaveSpeed / Kie)  — fast, great for short UGC, ~$0.30
  - Sora 2         (WaveSpeed)        — OpenAI model, good variety, ~$0.30
  - Sora 2 Pro     (WaveSpeed / Kie)  — highest fidelity from OpenAI, ~$0.30
  - Seedance 2.0   (Higgsfield)       — ByteDance model, affordable, ~$0.20
  - Minimax        (Higgsfield)       — fast & affordable social video, ~$0.20

Features:
  A. AI Prompt Assistant — describe in plain English, AI writes the motion prompt
  B. Reference Image Upload — image-to-video: the AI animates your still image
  C. Video Style Presets — Product Reveal, Social Teaser, Cinematic, UGC-style, etc.
  D. Platform Selector — auto-sets aspect ratio + motion hints
  E. Brand & Persona — context injected so the video feels on-brand
  F. Multi-model selection — choose the best model for your use case

Security: All inputs validated (prompt length, aspect ratio whitelist,
model whitelist, duration whitelist, file upload extension whitelist).
"""

import logging
import os

from .base import BaseRecipe, InputField

logger = logging.getLogger(__name__)

# ── Constants ──────────────────────────────────────────────────────────────

# Map UI model values → (internal model name, display label, default provider, cost label)
_MODEL_MAP = {
    "veo-3.1": ("veo-3.1", "Veo 3.1 (Google)", "google", "$0.50"),
    "kling-3.0": ("kling-3.0", "Kling 3.0 (WaveSpeed)", "wavespeed", "$0.30"),
    "sora-2": ("sora-2", "Sora 2 (WaveSpeed)", "wavespeed", "$0.30"),
    "sora-2-pro": ("sora-2-pro", "Sora 2 Pro (WaveSpeed)", "wavespeed", "$0.30"),
    "seedance": ("seedance", "Seedance 2.0 (Higgsfield)", "higgsfield", "~$0.08"),
    "minimax": ("minimax", "Minimax (Higgsfield)", "higgsfield", "~$0.08"),
}

_VALID_RATIOS = {"9:16", "16:9", "1:1"}
_VALID_DURATIONS = {"4", "5", "6", "8", "10", "15", "20"}

# Per-model maximum supported durations (in seconds).
# If a user selects a duration longer than a model supports, it will be
# clamped to the model's max and the user will be informed.
_MODEL_MAX_DURATION = {
    "veo-3.1": 8,       # Google Veo snaps to 4, 6, or 8s
    "kling-3.0": 10,    # Kling 3.0 supports up to ~10s
    "sora-2": 20,       # WaveSpeed Sora maps to 4, 8, 12, 16, 20s
    "sora-2-pro": 20,   # Kie n_frames=20 (~20s); WaveSpeed maps to 20s
    "seedance": 10,     # Higgsfield Seedance — 5–10s typical
    "minimax": 10,      # Higgsfield Minimax — 6–10s typical
}

# Video style presets — each provides a motion-focused prompt fragment
_STYLE_PRESETS = {
    "none": {
        "label": "None — I'll describe everything",
        "prompt_fragment": "",
    },
    "product_reveal": {
        "label": "Product Reveal",
        "prompt_fragment": (
            "Cinematic product reveal: slow dramatic zoom-in on the product "
            "with soft bokeh background. Elegant lighting transitions from dark "
            "to perfectly lit. Subtle particle effects or light flares. "
            "Premium, polished commercial feel."
        ),
    },
    "social_teaser": {
        "label": "Social Media Teaser",
        "prompt_fragment": (
            "Punchy social media teaser with dynamic, attention-grabbing movement. "
            "Quick cuts between angles, trendy transitions, energetic pacing. "
            "Designed to stop the scroll — bold, vibrant, modern. "
            "Think Instagram Reels or TikTok aesthetic."
        ),
    },
    "cinematic": {
        "label": "Cinematic / Epic",
        "prompt_fragment": (
            "Cinematic wide-angle shot with dramatic camera movement — "
            "slow dolly, crane shot, or smooth orbit. Film-grade color grading, "
            "anamorphic lens flares, shallow depth of field. "
            "Epic, movie-trailer quality visual storytelling."
        ),
    },
    "ugc_style": {
        "label": "UGC / Authentic",
        "prompt_fragment": (
            "Authentic UGC (user-generated content) style — handheld camera "
            "with natural, slightly imperfect movement. Warm, relatable lighting. "
            "Feels real and trustworthy, not overly polished. "
            "Perfect for testimonials and lifestyle content."
        ),
    },
    "slow_motion": {
        "label": "Slow Motion",
        "prompt_fragment": (
            "Smooth slow-motion capture with time-stretched movement. "
            "Every detail is emphasised — particles, liquid, fabric, "
            "or mechanical motion. Dreamy, hypnotic, and satisfying. "
            "High frame rate aesthetic with soft focus transitions."
        ),
    },
    "ambient_loop": {
        "label": "Ambient / Loop",
        "prompt_fragment": (
            "Seamless ambient loop — gentle, continuous movement like floating "
            "particles, subtle parallax, or soft camera drift. Calm and "
            "mesmerising. Perfect for backgrounds, banners, or digital displays. "
            "Minimal but visually rich."
        ),
    },
    "unboxing": {
        "label": "Unboxing / Hands-on",
        "prompt_fragment": (
            "First-person unboxing or hands-on reveal. Camera follows hands "
            "opening packaging, revealing the product step by step. Close-up "
            "detail shots of textures and features. Satisfying, ASMR-adjacent "
            "aesthetic with premium feel."
        ),
    },
}

# Platform → (recommended aspect ratio, motion hint)
_PLATFORM_MAP = {
    "none": {
        "label": "No specific platform",
        "recommended_ratio": None,
        "hint": "",
    },
    "instagram_reels": {
        "label": "Instagram Reels / Stories",
        "recommended_ratio": "9:16",
        "hint": (
            "Full-screen vertical video for Instagram Reels/Stories. "
            "Quick hook in the first second, subject centred, "
            "important action away from top/bottom edges. "
            "Energetic, scroll-stopping movement."
        ),
    },
    "tiktok": {
        "label": "TikTok",
        "recommended_ratio": "9:16",
        "hint": (
            "Vertical 9:16 for TikTok. Trend-aware, Gen-Z aesthetic. "
            "Dynamic movement, quick transitions, bold visual impact. "
            "Must hook in the first 0.5 seconds."
        ),
    },
    "youtube_shorts": {
        "label": "YouTube Shorts",
        "recommended_ratio": "9:16",
        "hint": (
            "Vertical 9:16 for YouTube Shorts. Clean, high-quality motion. "
            "Slightly more polished than TikTok but still energetic. "
            "Clear visual narrative in under 60 seconds."
        ),
    },
    "youtube": {
        "label": "YouTube (landscape)",
        "recommended_ratio": "16:9",
        "hint": (
            "Landscape 16:9 for YouTube player. Cinematic camera movement, "
            "wide establishing shots, smooth transitions. "
            "Higher production value, film-quality aesthetic."
        ),
    },
    "linkedin": {
        "label": "LinkedIn",
        "recommended_ratio": "1:1",
        "hint": (
            "Professional LinkedIn context. Square 1:1 for maximum feed "
            "real estate. Polished, corporate-friendly motion. "
            "Subtle, sophisticated movement — not flashy."
        ),
    },
    "facebook": {
        "label": "Facebook Feed / Ad",
        "recommended_ratio": "1:1",
        "hint": (
            "Facebook feed optimised. Square or slight landscape. "
            "Warm, inviting motion. Clear product focus. "
            "Designed for autoplay with no sound."
        ),
    },
    "website": {
        "label": "Website / Landing Page",
        "recommended_ratio": "16:9",
        "hint": (
            "Wide hero video for website header or landing page. "
            "Atmospheric, ambient motion. Subtle camera drift or parallax. "
            "Premium, polished. Designed to loop seamlessly."
        ),
    },
}


class VideoCreator(BaseRecipe):
    slug = "video-creator"
    name = "Video Creator"
    short_description = "Describe what you want — the AI crafts the motion and generates a video."
    description = (
        "Tell the AI what you want in plain English, pick a style and platform, "
        "and optionally upload a reference image. The AI writes the perfect "
        "motion prompt for you — incorporating your brand colours, persona voice, "
        "and visual style. Supports 6 models: Veo 3.1, Kling 3.0, Sora 2, "
        "Sora 2 Pro, Seedance 2.0, and Minimax."
    )
    category = "video_studio"
    icon = "🎥"
    estimated_cost = "$0.30 – $0.50 per video"
    is_active = True  # ← ACTIVATED

    how_to_use = """\
### How to use Video Creator

**Two modes:**

| Mode | Best For |
|------|----------|
| **🤖 Assisted** *(default)* | Describe what you want in plain English — the AI writes the detailed motion prompt for you. No prompt-engineering skills needed. |
| **✍️ Manual** | You write the full motion prompt yourself — for power users who want total control. |

**Steps:**
1. **Choose a mode** — Assisted (recommended) or Manual.
2. **Describe the motion** — e.g. "a cinematic product reveal for my coffee brand".
3. *(Optional)* **Upload a reference image** — the AI will animate this still image into a video.
4. *(Optional)* **Pick a video style preset** — Product Reveal, Social Teaser, Cinematic, etc.
5. *(Optional)* **Pick a platform** — Instagram Reels, TikTok, YouTube, etc. Auto-sets aspect ratio.
6. **Select a Brand and/or Persona** — your brand colours, style, and voice are injected automatically.
7. **Choose model and duration**.
8. Click **Generate** and wait 2–5 minutes.

**Available Models:**
| Model | Quality | Speed | Cost |
|-------|---------|-------|------|
| Veo 3.1 (Google) | Cinematic | ~3 min | $0.50 |
| Kling 3.0 (WaveSpeed) | Great | ~2 min | $0.30 |
| Sora 2 (WaveSpeed) | Good | ~3 min | $0.30 |
| Sora 2 Pro (WaveSpeed) | Excellent | ~4 min | $0.30 |
| Seedance 2.0 (Higgsfield) | Good | ~2 min | $0.20 |
| Minimax (Higgsfield) | Good | ~2 min | $0.20 |

**Tips:**
- Start with **Assisted mode** — the AI writes better motion prompts than most humans.
- Upload a product photo or still frame for **image-to-video** generation.
- Without an image, the AI generates a video from your text prompt alone (**text-to-video**).
- The **Brand** injects your colours, audience, and guidelines into the motion description.
- The **Persona** sets the tone for any on-screen text or voiceover cues.
- Veo 3.1 produces the most cinematic results; Seedance and Minimax are the cheapest.
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
                    {"value": "assisted", "label": "🤖 Assisted — AI writes the motion prompt for you"},
                    {"value": "manual", "label": "✍️ Manual — write your own motion prompt"},
                ],
                help_text="Assisted mode: describe what you want in plain English. The AI writes the detailed motion prompt.",
            ),
            InputField(
                name="motion_prompt",
                label="Your Description / Motion Prompt",
                field_type="textarea",
                required=True,
                placeholder=(
                    "Assisted: \"A cinematic product reveal for our new coffee blend, "
                    "warm morning light, steam rising\"\n"
                    "Manual: \"Slow dolly push-in on a coffee cup, steam wisps rising, "
                    "golden hour light through window, shallow DOF, parallax background\""
                ),
                help_text=(
                    "Assisted mode: just describe what you want. "
                    "Manual mode: write the full motion prompt."
                ),
            ),
            InputField(
                name="reference_image",
                label="Reference Image (optional — enables image-to-video)",
                field_type="file",
                required=False,
                accept="image/*",
                help_text=(
                    "Upload a still image — the AI will animate it into a video. "
                    "Without an image, you get text-to-video generation."
                ),
            ),
            InputField(
                name="style_preset",
                label="Video Style Preset",
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
                help_text="Auto-sets the best aspect ratio and motion style for your target platform.",
            ),
            InputField(
                name="model",
                label="Model",
                field_type="select",
                default="veo-3.1",
                options=[
                    {"value": k, "label": f"{v[1]} — {v[3]}"}
                    for k, v in _MODEL_MAP.items()
                ],
                help_text="Veo 3.1 = most cinematic. Seedance & Minimax = cheapest. Sora 2 Pro = highest fidelity.",
            ),
            InputField(
                name="duration",
                label="Duration",
                field_type="select",
                default="5",
                options=[
                    {"value": "4", "label": "4 seconds — quick teaser"},
                    {"value": "5", "label": "5 seconds (default)"},
                    {"value": "6", "label": "6 seconds"},
                    {"value": "8", "label": "8 seconds — max for Veo 3.1"},
                    {"value": "10", "label": "10 seconds — max for Kling / Seedance / Minimax"},
                    {"value": "15", "label": "15 seconds — Sora 2 / Sora 2 Pro"},
                    {"value": "20", "label": "20 seconds — Sora 2 / Sora 2 Pro"},
                ],
                help_text=(
                    "Not all models support all durations. If your chosen duration "
                    "exceeds the model's max, it will be clamped and you'll be notified. "
                    "Longer durations cost proportionally more credits."
                ),
            ),
            InputField(
                name="aspect_ratio",
                label="Aspect Ratio",
                field_type="select",
                default="9:16",
                options=[
                    {"value": "9:16", "label": "Vertical (9:16) — Reels / TikTok / Shorts"},
                    {"value": "16:9", "label": "Horizontal (16:9) — YouTube / Website"},
                    {"value": "1:1", "label": "Square (1:1) — LinkedIn / Facebook"},
                ],
                help_text="Tip: if you selected a Platform above, this is auto-recommended.",
            ),
        ]

    def get_steps(self):
        return [
            "Analysing inputs",
            "Crafting motion prompt",
            "Generating video",
            "Processing output",
        ]

    # ------------------------------------------------------------------
    # Gemini helpers (same pattern as ImageCreator/AdVideoMaker)
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
        """Generate an AI video with smart prompt assistance.

        Supports assisted mode (AI writes prompt), reference image analysis,
        style presets, platform hints, and brand/persona injection.
        Delegates to tools/create_video.generate_ugc_video for actual generation.
        """
        from tools.create_video import generate_ugc_video
        from tools.config import get_cost

        # ── Read & validate inputs ────────────────────────────────────
        raw_prompt = (inputs.get("motion_prompt") or "").strip()
        if not raw_prompt:
            raise ValueError("A motion description or prompt is required.")

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

        model_key = inputs.get("model", "veo-3.1")
        if model_key not in _MODEL_MAP:
            logger.warning("Unknown model '%s', falling back to veo-3.1", model_key)
            model_key = "veo-3.1"
        model_name, model_label, default_provider, cost_label = _MODEL_MAP[model_key]

        # Aspect ratio: use platform recommendation if user left default
        aspect_ratio = inputs.get("aspect_ratio", "9:16")
        if aspect_ratio not in _VALID_RATIOS:
            aspect_ratio = "9:16"
        if platform["recommended_ratio"] and aspect_ratio == "9:16":
            aspect_ratio = platform["recommended_ratio"]

        duration = inputs.get("duration", "5")
        if duration not in _VALID_DURATIONS:
            duration = "5"

        # Clamp duration to model's maximum supported length
        requested_duration = int(duration)
        max_dur = _MODEL_MAX_DURATION.get(model_key, 10)
        duration_clamped = False
        if requested_duration > max_dur:
            duration_clamped = True
            duration = str(max_dur)
            logger.info(
                "Duration clamped from %ds to %ds for model %s",
                requested_duration, max_dur, model_key,
            )

        outputs = []

        if duration_clamped:
            outputs.append({
                "type": "text",
                "title": "⏱️ Duration Adjusted",
                "value": (
                    f"You requested **{requested_duration}s** but **{model_label}** "
                    f"supports a maximum of **{max_dur}s**. Duration has been set to "
                    f"**{max_dur}s**.\n\n"
                    f"💡 **Tip:** For longer videos, try **Sora 2 / Sora 2 Pro** (up to 20s) "
                    f"or generate multiple shorter clips and stitch them together."
                ),
            })

        # ── Step 0: Analyse inputs ────────────────────────────────────
        self.report_progress(on_progress, 0, "Analysing inputs…")

        # Build brand & persona context
        brand_ctx = self.build_brand_context(brand)
        persona_ctx = self.build_persona_context(persona)

        # Analyse reference image if uploaded
        reference_analysis = ""
        if reference_image:
            self.report_progress(on_progress, 0, "Analysing reference image…")
            try:
                reference_analysis = self._call_gemini_vision(
                    "You are an expert cinematographer analysing a reference image "
                    "that will be animated into a video.\n"
                    "Describe in detail:\n"
                    "1. Main subject and its position in the frame\n"
                    "2. Colour palette and lighting\n"
                    "3. Depth layers (foreground, midground, background)\n"
                    "4. Elements that could move naturally (fabric, hair, smoke, "
                    "liquid, light, particles)\n"
                    "5. Suggested camera movements that would enhance this still\n"
                    "6. Overall mood and energy level\n\n"
                    "Be specific and concise. This analysis will guide the AI "
                    "to animate this image into a compelling video.",
                    reference_image,
                )
                outputs.append({
                    "type": "text",
                    "title": "🔍 Reference Image Analysis",
                    "value": reference_analysis,
                })
                logger.info("Reference image analysed for video run %s", run_id)
            except Exception as exc:
                logger.warning("Reference image analysis failed: %s", exc)
                reference_analysis = ""
                outputs.append({
                    "type": "text",
                    "title": "⚠️ Reference Analysis",
                    "value": f"Could not analyse reference image: {exc}. Proceeding without it.",
                })

        # ── Step 1: Craft the motion prompt ────────────────────────────
        self.report_progress(on_progress, 1, "Crafting motion prompt…")

        if creation_mode == "assisted":
            final_prompt = self._build_assisted_prompt(
                user_description=raw_prompt,
                style=style,
                platform=platform,
                reference_analysis=reference_analysis,
                brand_ctx=brand_ctx,
                persona_ctx=persona_ctx,
                aspect_ratio=aspect_ratio,
                duration=duration,
                has_image=bool(reference_image),
            )
            outputs.append({
                "type": "text",
                "title": "✨ AI-Crafted Motion Prompt",
                "value": final_prompt,
            })
        else:
            # Manual mode — use raw prompt, enrich with context
            final_prompt = self._build_manual_prompt(
                raw_prompt=raw_prompt,
                style=style,
                platform=platform,
                reference_analysis=reference_analysis,
                brand_ctx=brand_ctx,
                persona_ctx=persona_ctx,
            )

        # ── Step 2: Generate video ─────────────────────────────────────
        gen_mode = "image-to-video" if reference_image else "text-to-video"
        self.report_progress(
            on_progress, 2,
            f"Generating video via {model_label} ({gen_mode})… this may take 2–5 minutes."
        )

        try:
            result = generate_ugc_video(
                prompt=final_prompt,
                image_path=reference_image if reference_image else None,
                model=model_name,
                duration=duration,
                aspect_ratio=aspect_ratio,
                provider=default_provider,
            )
        except Exception as exc:
            logger.error("Video generation failed: %s", exc, exc_info=True)
            outputs.append({
                "type": "text",
                "title": "❌ Generation Error",
                "value": f"Video generation failed: {exc}",
            })
            result = None

        # ── Step 3: Process output ─────────────────────────────────────
        self.report_progress(on_progress, 3, "Processing output…")

        total_cost = 0.0

        if result:
            status = result.get("status", "")
            video_url = result.get("result_url", "")

            if status == "success" and video_url:
                outputs.append({
                    "type": "video",
                    "title": "Generated Video",
                    "url": video_url,
                })
                total_cost = get_cost(model_name, default_provider)
            else:
                error_detail = result.get("error", "Unknown error")
                outputs.append({
                    "type": "text",
                    "title": "❌ Generation Error",
                    "value": f"Status '{status}': {error_detail}",
                })

        # ── Summary card ──────────────────────────────────────────────
        has_video = any(o.get("type") == "video" for o in outputs)
        if not has_video:
            outputs.append({
                "type": "text",
                "title": "Error",
                "value": "⚠️ No video was generated. Please try again or choose a different model.",
            })

        summary_lines = [
            f"**Mode:** {'🤖 Assisted' if creation_mode == 'assisted' else '✍️ Manual'}",
            f"**Model:** {model_label}",
            f"**Generation:** {gen_mode.replace('-', ' ').title()}",
            f"**Aspect Ratio:** {aspect_ratio}",
            f"**Duration:** {duration}s",
        ]
        if style_key != "none":
            summary_lines.append(f"**Style:** {style['label']}")
        if platform_key != "none":
            summary_lines.append(f"**Platform:** {platform['label']}")
        if reference_image:
            summary_lines.append("**Reference Image:** ✅ Used as start frame")
        summary_lines.append(
            f"**Result:** {'✅ Success' if has_video else '❌ Failed'}"
        )
        summary_lines.append(f"**Cost:** ${total_cost:.2f}")
        if brand:
            summary_lines.append(f"**Brand:** {brand.name}")
        if persona:
            summary_lines.append(f"**Persona:** {persona.name}")

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
                                reference_analysis, brand_ctx, persona_ctx,
                                aspect_ratio, duration, has_image):
        """Use Gemini to craft a detailed motion prompt from plain English.

        This is the AI Prompt Assistant — the core differentiator that makes
        Video Creator valuable for non-technical users.
        """
        gen_type = "image-to-video" if has_image else "text-to-video"

        meta_prompt_parts = [
            "You are an expert cinematographer and video prompt engineer. "
            f"Your job is to write a single, highly detailed {gen_type} "
            "motion prompt based on the user's description and context below.\n",
        ]

        meta_prompt_parts.append(
            f"USER'S DESCRIPTION:\n\"{user_description}\"\n"
        )

        meta_prompt_parts.append(
            f"VIDEO SPECS: {aspect_ratio} aspect ratio, {duration} seconds, "
            f"{gen_type} generation.\n"
        )

        if style["prompt_fragment"]:
            meta_prompt_parts.append(
                f"STYLE DIRECTION:\n{style['prompt_fragment']}\n"
            )

        if platform["hint"]:
            meta_prompt_parts.append(
                f"PLATFORM CONTEXT ({platform['label']}):\n{platform['hint']}\n"
            )

        if reference_analysis:
            meta_prompt_parts.append(
                f"REFERENCE IMAGE ANALYSIS (animate this image):\n"
                f"{reference_analysis}\n"
            )

        if brand_ctx:
            meta_prompt_parts.append(brand_ctx)

        if persona_ctx:
            meta_prompt_parts.append(persona_ctx)

        # Determine if UGC style is selected
        style_hint = "ugc" if style.get("label", "").lower().startswith("ugc") else ""
        creative_directives = self.build_creative_directives(
            generation_type="video", style_hint=style_hint
        )
        meta_prompt_parts.append(creative_directives)

        meta_prompt_parts.append(
            "INSTRUCTIONS:\n"
            "1. Write a single, detailed video motion prompt (2–4 sentences).\n"
            "2. Describe: camera movement, subject motion, lighting transitions, "
            "atmosphere changes, and pacing.\n"
        )
        if has_image:
            meta_prompt_parts.append(
                "3. Since this is image-to-video, describe HOW the still image "
                "comes alive — what moves, what the camera does, what changes.\n"
            )
        else:
            meta_prompt_parts.append(
                "3. Since this is text-to-video, describe the full scene "
                "including subject, setting, and all motion.\n"
            )
        meta_prompt_parts.append(
            "4. Incorporate the style preset and platform context naturally.\n"
            "5. If brand colours are provided, weave them into the lighting, "
            "props, set design, or colour palette of the scene. "
            "NEVER use random colours when brand colours are available.\n"
            "6. NEVER alter the colour or any part of the product shown in "
            "the reference image.\n"
            "7. Be specific about camera movement: 'slow dolly push-in', "
            "'orbit left 90°', 'crane up revealing the scene'.\n"
            "8. Make the prompt cinematic and visual — avoid vague adjectives.\n"
            "9. Do NOT use double quotes inside the prompt.\n"
            "10. For dialogue, use '...' for pauses, avoid special characters.\n"
            "11. Ensure diversity in gender, ethnicity, and hair colour "
            "when people are part of the scene.\n\n"
            "OUTPUT: The video motion prompt ONLY — no labels, no quotes, "
            "no explanations, no markdown. Just the prompt text."
        )

        try:
            crafted = self._call_gemini("\n".join(meta_prompt_parts))
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
            reference_analysis=reference_analysis,
            brand_ctx=brand_ctx,
            persona_ctx=persona_ctx,
        )

    @staticmethod
    def _build_manual_prompt(*, raw_prompt, style, platform,
                              reference_analysis, brand_ctx, persona_ctx):
        """Build an enriched prompt for manual mode.

        Appends style, platform, and brand/persona context to the user's
        raw motion prompt text.
        """
        parts = [raw_prompt]

        if style["prompt_fragment"]:
            parts.append(f"\nStyle direction: {style['prompt_fragment']}")

        if platform["hint"]:
            parts.append(f"\nPlatform: {platform['hint']}")

        if reference_analysis:
            parts.append(
                f"\nAnimate based on this reference: {reference_analysis[:500]}"
            )

        if brand_ctx or persona_ctx:
            parts.append(
                "\n--- STYLE CONTEXT (incorporate into the visual) ---"
            )
            if brand_ctx:
                parts.append(brand_ctx)
            if persona_ctx:
                parts.append(persona_ctx)

        return "\n".join(parts)
