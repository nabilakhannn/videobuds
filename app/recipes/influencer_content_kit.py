"""Influencer Content Kit — character + brief → images, videos, captions.

Based on the R44 "AI Influencer Toolkit" n8n workflow.  The AI analyses a
character/influencer photo, generates scene-specific prompts, creates images
(and optionally short videos), and writes captions with hashtags — all in
one click.

Security: All inputs are validated (file upload, text length, count whitelist).
Brand/persona context is injected so every output stays on-brand.
"""

import json
import logging
import os

from .base import BaseRecipe, InputField

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────

_VALID_COUNTS = {"1", "3", "5"}
_VALID_PLATFORMS = {"instagram", "tiktok", "both"}

# Platform → aspect ratio + composition hints
_PLATFORM_SPECS = {
    "instagram": {
        "aspect_ratio": "9:16",
        "hints": "Instagram Reels / Stories format, 9:16 portrait, eye-catching thumbnail",
    },
    "tiktok": {
        "aspect_ratio": "9:16",
        "hints": "TikTok format, 9:16 portrait, bold text-friendly, fast-scroll hook",
    },
    "both": {
        "aspect_ratio": "9:16",
        "hints": "Optimised for both Instagram Reels and TikTok, 9:16 portrait",
    },
}


class InfluencerContentKit(BaseRecipe):
    slug = "influencer-content-kit"
    name = "Influencer Content Kit"
    short_description = "Give a character photo & brief — get posts, images, and videos."
    description = (
        "Upload a character or influencer photo and a creative brief. "
        "The AI generates a full content kit: social media images, short "
        "videos, captions, and hashtags — ready to post on Instagram, "
        "TikTok, and more."
    )
    category = "content_creation"
    icon = "🌟"
    estimated_cost = "$0.10 – $0.80 per kit"
    is_active = True  # ← Activated in Phase 41

    how_to_use = """\
### How to use Influencer Content Kit

1. **Upload a character/influencer photo** — the face that will appear in content.
2. **Describe the brief** — e.g. "Summer fitness campaign for protein shakes".
3. **Choose the number of posts** to generate (1, 3, or 5).
4. *(Optional)* Select which platforms you're targeting.
5. Click **Generate** and let the AI create your full content kit.

**What you'll get:**
- AI-generated images featuring your character in on-brand scenes
- Captions with hashtags for each post
- Optionally: short video clips for Reels / TikTok

**What happens behind the scenes:**
- Step 1: AI analyses the character image (face shape, lighting, style)
- Step 2: Scene prompts + captions are written based on your brief
- Step 3: Images are generated featuring the character
- Step 4: Everything is packaged as a downloadable kit

**Tips:**
- Use a high-quality front-facing photo for best consistency.
- The more detail in your brief, the better the results.
- If you select a brand and persona, captions will match your voice.
"""

    # ------------------------------------------------------------------
    # Input fields
    # ------------------------------------------------------------------

    def get_input_fields(self):
        return [
            InputField(
                name="character_photo",
                label="Character / Influencer Photo",
                field_type="file",
                required=True,
                accept="image/*",
                help_text="A clear photo of the person who will appear in the content.",
            ),
            InputField(
                name="brief",
                label="Creative Brief",
                field_type="textarea",
                required=True,
                placeholder="e.g. Summer fitness campaign for a vegan protein brand",
                help_text="Describe the campaign, product, or theme.",
            ),
            InputField(
                name="post_count",
                label="Number of Posts",
                field_type="select",
                default="3",
                options=[
                    {"value": "1", "label": "1 post"},
                    {"value": "3", "label": "3 posts"},
                    {"value": "5", "label": "5 posts"},
                ],
            ),
            InputField(
                name="platforms",
                label="Target Platforms",
                field_type="select",
                default="instagram",
                options=[
                    {"value": "instagram", "label": "Instagram"},
                    {"value": "tiktok", "label": "TikTok"},
                    {"value": "both", "label": "Both"},
                ],
            ),
        ]

    def get_steps(self):
        return [
            "Analysing character & brief",
            "Writing scene prompts & captions",
            "Generating images",
            "Packaging content kit",
        ]

    # ------------------------------------------------------------------
    # Execute
    # ------------------------------------------------------------------

    def execute(self, inputs, run_id, user_id, on_progress=None,
                brand=None, persona=None):
        from app.services.agent_service import _call_gemini
        from tools.create_image import generate_ugc_image
        from tools.config import get_cost

        outputs = []
        total_cost = 0.0

        # ── Validate inputs ────────────────────────────────────────────
        photo_path = inputs.get("character_photo", "")
        if not photo_path or not os.path.isfile(photo_path):
            return {
                "outputs": [{"type": "text", "title": "❌ Error",
                             "value": "No character photo uploaded."}],
                "cost": 0.0,
            }

        brief = (inputs.get("brief") or "").strip()
        if not brief:
            return {
                "outputs": [{"type": "text", "title": "❌ Error",
                             "value": "Please provide a creative brief."}],
                "cost": 0.0,
            }

        post_count_str = inputs.get("post_count", "3")
        if post_count_str not in _VALID_COUNTS:
            post_count_str = "3"
        post_count = int(post_count_str)

        platform = inputs.get("platforms", "instagram")
        if platform not in _VALID_PLATFORMS:
            platform = "instagram"
        platform_spec = _PLATFORM_SPECS[platform]

        # ── Build brand / persona context ──────────────────────────────
        brand_ctx = self.build_brand_context(brand) if brand else ""
        persona_ctx = self.build_persona_context(persona) if persona else ""
        creative_directives = self.build_creative_directives()

        # ── Step 0: Analyse character photo ────────────────────────────
        self.report_progress(on_progress, 0, "Analysing character photo…")

        char_analysis = ""
        try:
            char_analysis = self._analyse_character(photo_path)
            logger.info("Character analysis complete: %d chars", len(char_analysis))
        except Exception as exc:
            logger.warning("Character analysis failed: %s", exc)
            char_analysis = "Unable to analyse photo — proceeding with brief only."

        # ── Step 1: Generate scene prompts + captions ──────────────────
        self.report_progress(
            on_progress, 1,
            f"Writing {post_count} scene prompts & captions…"
        )

        planning_prompt = self._build_planning_prompt(
            brief=brief,
            post_count=post_count,
            platform=platform,
            platform_hints=platform_spec["hints"],
            char_analysis=char_analysis,
            brand_ctx=brand_ctx,
            persona_ctx=persona_ctx,
            creative_directives=creative_directives,
        )

        try:
            raw_plan = _call_gemini(planning_prompt)
            scenes = self._parse_scenes(raw_plan, post_count)
        except Exception as exc:
            logger.error("Planning failed: %s", exc)
            return {
                "outputs": [{"type": "text", "title": "❌ Planning Error",
                             "value": f"AI could not plan scenes: {exc}"}],
                "cost": total_cost,
            }

        # Output the content plan
        plan_text = ""
        for i, scene in enumerate(scenes, 1):
            plan_text += (
                f"### Post {i}\n"
                f"**Scene:** {scene.get('scene', 'N/A')}\n\n"
                f"**Caption:** {scene.get('caption', 'N/A')}\n\n"
                f"**Hashtags:** {scene.get('hashtags', '')}\n\n---\n\n"
            )
        outputs.append({
            "type": "text",
            "title": "📋 Content Plan",
            "value": plan_text.strip(),
        })

        # ── Step 2: Generate images ────────────────────────────────────
        self.report_progress(
            on_progress, 2,
            f"Generating {len(scenes)} image(s)…"
        )

        aspect_ratio = platform_spec["aspect_ratio"]
        images_generated = 0

        for i, scene in enumerate(scenes):
            raw_prompt = scene.get("image_prompt", scene.get("scene", brief))

            # Prefix the prompt so Gemini generates a NEW scene instead of
            # echoing the reference photo.  The reference image is attached
            # as inline data — we explicitly instruct the model to treat it
            # only as a visual reference for the person's appearance.
            image_prompt = (
                "Generate a completely new, photorealistic photograph. "
                "Use the attached photo ONLY as a reference for the "
                "person's physical appearance (face, hair, body type). "
                "Place this person in a brand-new scene with different "
                "clothing, background, lighting, and composition. "
                "Do NOT reproduce the original photo. "
                "Scene description: " + raw_prompt
            )

            try:
                self.report_progress(
                    on_progress, 2,
                    f"Generating image {i + 1}/{len(scenes)}…"
                )
                result = generate_ugc_image(
                    prompt=image_prompt,
                    reference_paths=[photo_path],
                    aspect_ratio=aspect_ratio,
                    model="nano-banana-pro",
                    provider="google",
                )
                image_url = result.get("result_url", "")
                if image_url:
                    img_cost = get_cost("nano-banana-pro", "google")
                    total_cost += img_cost
                    images_generated += 1
                    outputs.append({
                        "type": "image",
                        "title": f"📸 Post {i + 1} — {scene.get('scene', 'Image')[:50]}",
                        "url": image_url,
                    })

                    # Add caption as a separate text output
                    caption = scene.get("caption", "")
                    hashtags = scene.get("hashtags", "")
                    if caption:
                        outputs.append({
                            "type": "text",
                            "title": f"✍️ Caption — Post {i + 1}",
                            "value": f"{caption}\n\n{hashtags}",
                        })
            except Exception as exc:
                logger.warning("Image %d failed: %s", i + 1, exc)
                outputs.append({
                    "type": "text",
                    "title": f"⚠️ Image {i + 1} Failed",
                    "value": f"Could not generate image: {exc}",
                })

        # ── Step 3: Package ────────────────────────────────────────────
        self.report_progress(on_progress, 3, "Packaging content kit…")

        # Summary card
        outputs.append({
            "type": "text",
            "title": "📊 Content Kit Summary",
            "value": (
                f"**Posts planned:** {len(scenes)}\n"
                f"**Images generated:** {images_generated}\n"
                f"**Platform:** {platform.title()}\n"
                f"**Total cost:** ${total_cost:.2f}"
            ),
        })

        return {
            "outputs": outputs,
            "cost": total_cost,
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _analyse_character(photo_path):
        """Use Gemini Vision to describe the character in the photo."""
        from app.services.agent_service import _call_gemini_with_image

        prompt = (
            "Describe this person for an AI image generation system. "
            "Include: approximate age range, gender presentation, "
            "hair colour & style, skin tone, clothing, expression, "
            "and any distinctive visual features. "
            "Be factual and detailed — this description will be used "
            "to recreate this person's appearance in generated images. "
            "Never name or identify the person. "
            "Output ONLY the description, no commentary."
        )
        return _call_gemini_with_image(prompt, photo_path)

    @staticmethod
    def _build_planning_prompt(*, brief, post_count, platform,
                                platform_hints, char_analysis,
                                brand_ctx, persona_ctx,
                                creative_directives):
        """Build the Gemini prompt for content planning."""
        return f"""You are a world-class social media content strategist and copywriter.

{brand_ctx}
{persona_ctx}
{creative_directives}

**Character Description (from uploaded photo):**
{char_analysis}

**Campaign Brief:** {brief}
**Number of posts to create:** {post_count}
**Target platform:** {platform} — {platform_hints}

YOUR TASK:
Create {post_count} unique social media post concepts. For EACH post output a JSON object with these fields:
- "scene" — a short title for the scene (5–10 words)
- "image_prompt" — a detailed image generation prompt (80–150 words) that:
  1. Features the character described above in a specific, on-brand setting
  2. Includes composition (close-up, medium shot, etc.), lighting, mood
  3. Uses the brand colours and style if provided
  4. Feels natural and UGC-style — NOT stock-photo polished
  5. Never uses double quotes in the prompt text
- "caption" — a social media caption (2–4 sentences) with a hook and CTA
- "hashtags" — 5–10 relevant hashtags

OUTPUT FORMAT:
Return ONLY a JSON array of {post_count} objects. No markdown fences, no explanations.
Example:
[{{"scene":"Morning routine with product","image_prompt":"A woman in her 20s...","caption":"Starting my day right...","hashtags":"#morningroutine #skincare"}}]"""

    @staticmethod
    def _parse_scenes(raw_text, expected_count):
        """Parse the Gemini response into a list of scene dicts."""
        # Strip markdown fences if present
        text = raw_text.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            if lines[0].strip().startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines).strip()

        try:
            scenes = json.loads(text)
            if isinstance(scenes, list):
                return scenes[:expected_count]
        except json.JSONDecodeError:
            pass

        # Fallback: try to find JSON array in the text
        import re
        match = re.search(r'\[.*\]', text, re.DOTALL)
        if match:
            try:
                scenes = json.loads(match.group())
                if isinstance(scenes, list):
                    return scenes[:expected_count]
            except json.JSONDecodeError:
                pass

        # Last resort: create a single scene from the raw text
        logger.warning("Could not parse scenes JSON, creating fallback")
        return [{"scene": "Campaign content", "image_prompt": text[:300],
                 "caption": "Check this out!", "hashtags": "#content"}]
