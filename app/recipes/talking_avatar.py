"""Talking Avatar — still image + script → talking-head video + B-roll footage.

Pipeline:
  1. User uploads a headshot and writes (or AI-generates) a script.
  2. Gemini TTS converts the script to speech audio (WAV).
  3. Audio + image are uploaded to a CDN (WaveSpeed media upload).
  4. A talking-head video is generated using a 3-tier fallback chain:
       Priority 1 → Higgsfield Speak v2  (best quality)
       Priority 2 → Higgsfield talking_photo  (legacy fallback)
       Priority 3 → WaveSpeed InfiniteTalk  (last resort)
  5. (Optional) B-Roll pipeline — when a style-reference image is provided:
       a. Gemini Vision analyses the style reference (color, mood, composition)
       b. AI generates SEALCaM B-roll prompts aligned to the script
       c. B-roll images are generated via generate_ugc_image
       d. B-roll video clips are created from those images via generate_ugc_video

Based on the proven R52 longform pipeline (r52_longform_app.py).
"""

import json
import logging
import os
import re

from .base import BaseRecipe, InputField

logger = logging.getLogger(__name__)

# Voice preset → Gemini TTS voice name mapping
_VOICE_MAP = {
    "natural_female": "Kore",
    "natural_male": "Charon",
    "energetic_female": "Aoede",
    "energetic_male": "Puck",
    "calm_female": "Leda",
    "calm_male": "Orus",
}

# SEALCaM B-roll system prompt (from R52 pipeline)
_BROLL_SYSTEM_PROMPT = """\
## SEALCaM B-Roll Segment Generator

You are a cinematic B-roll director. Analyze a spoken script and generate
B-roll visual prompts using the SEALCaM framework.

Rules:
- All outputs are B-roll only — do NOT depict a narrator speaking to camera
- Visuals should metaphorically support the narration
- Color hues must be consistent across ALL segments and match the style reference
- Each image prompt must be self-contained (no references to other segments)

SEALCaM format for prompts (each key on new line):
Subject: <primary visual focus>
Environment: <surrounding context>
Action: <subtle motion or activity>
Lighting: <light source and mood>
Camera: <lens type, framing, angle>
Metatokens: <style, realism, quality cues>
"""

_IMAGE_ANALYSIS_PROMPT = (
    "Focus on the design type and theme of this image. "
    "Describe the visual style, color palette, typography, layout composition, "
    "and overall aesthetic. Use cinema and photography terminology. "
    "Output a concise analysis paragraph."
)


class TalkingAvatar(BaseRecipe):
    slug = "talking-avatar"
    name = "Talking Avatar"
    short_description = "Upload a photo and a script — get a realistic talking-head video + optional B-roll footage."
    description = (
        "Upload any headshot photo and a script (or let AI write one). "
        "The AI generates a realistic talking-head video where the person "
        "in the photo speaks your script with lip-sync, natural expressions, "
        "and natural gestures. Optionally upload a style-reference image to "
        "also generate cinematic B-roll clips that visually support the script — "
        "just like your original R52 production pipeline. "
        "Perfect for explainers, ads, or social content without being on camera."
    )
    category = "video_studio"
    icon = "🗣️"
    estimated_cost = "$0.15 – $1.00 per run (varies with B-roll)"
    is_active = True  # ← Activated in Phase 41

    how_to_use = """\
### How to use Talking Avatar

1. **Upload a headshot** — a clear, front-facing photo of the person.
2. **Enter the script** — what you want the person to say.
   - Or leave blank and provide a brief — AI will write the script for you.
3. **Pick a voice style** — Natural, Energetic, or Calm (male / female).
4. **(Optional) Upload a style-reference image** — for B-roll footage.
   - This can be a product shot, mood board, brand visual, or any image whose
     *style* you want the B-roll to match.
5. **Choose B-roll options** — enable/disable and set clip count.
6. Click **Generate** and wait 2–10 minutes (longer with B-roll).
7. Preview and download your talking-head video + B-roll clips.

**What happens behind the scenes:**
- Step 1: AI analyses the headshot (face shape, lighting, skin tone)
- Step 2: If no script provided, AI writes one from your brief
- Step 3: Script is converted to natural speech audio (Gemini TTS)
- Step 4: AI animates the face with lip-sync and micro-expressions
- Steps 5–8 (if B-roll enabled):
  - AI analyses your style-reference image for visual direction
  - AI generates SEALCaM B-roll prompts that match the script
  - B-roll images are created matching the style reference
  - B-roll video clips are generated from those images

**3-tier quality chain for talking head (automatic fallback):**
| Priority | Engine | Quality |
|----------|--------|---------|
| 1 | Higgsfield Speak v2 | Best — natural gestures & movement |
| 2 | Higgsfield Talking Photo | Good — reliable lip-sync |
| 3 | WaveSpeed InfiniteTalk | Baseline — always available |

**Use cases:**
- 📢 Product explainer videos without filming
- 🎓 Course intro / educational content
- 📱 Social media talking-head posts with supporting visuals
- 🤖 Digital spokesperson for your brand
- 🎬 Full video packages: talking head + matching B-roll

**Tips:**
- Use a neutral expression photo — the AI will add expressions.
- Keep scripts under 60 seconds for best quality.
- Front-facing photos with good lighting produce the best results.
- Upload a style reference that matches your brand aesthetic for cohesive B-roll.
"""

    # ------------------------------------------------------------------
    # Input fields
    # ------------------------------------------------------------------

    def get_input_fields(self):
        return [
            InputField(
                name="headshot",
                label="Headshot Photo",
                field_type="file",
                required=True,
                accept="image/*",
                help_text="A clear front-facing headshot of the speaker.",
            ),
            InputField(
                name="script",
                label="Script",
                field_type="textarea",
                required=False,
                placeholder=(
                    "e.g. Hi! I'm Sarah, and I'm going to show you "
                    "how this product changed my morning routine…"
                ),
                help_text=(
                    "What should the person say? Leave blank to let AI "
                    "write it from your brief."
                ),
            ),
            InputField(
                name="brief",
                label="AI Script Brief (if no script)",
                field_type="text",
                required=False,
                placeholder="e.g. 30-second product promo for organic skincare",
                help_text=(
                    "Describe what the video should be about. "
                    "Used only when the Script field is empty."
                ),
            ),
            InputField(
                name="voice_preset",
                label="Voice Style",
                field_type="select",
                default="natural_female",
                options=[
                    {"value": "natural_female", "label": "Natural Female"},
                    {"value": "natural_male", "label": "Natural Male"},
                    {"value": "energetic_female", "label": "Energetic Female"},
                    {"value": "energetic_male", "label": "Energetic Male"},
                    {"value": "calm_female", "label": "Calm Female"},
                    {"value": "calm_male", "label": "Calm Male"},
                ],
                help_text="Choose the voice style for the AI speech.",
            ),
            # ── B-Roll inputs (from R52 pipeline) ─────────────────────
            InputField(
                name="style_reference",
                label="Style Reference (for B-Roll)",
                field_type="file",
                required=False,
                accept="image/*",
                help_text=(
                    "Upload a reference image whose visual style you want "
                    "the B-roll to match (product shot, mood board, brand "
                    "visual). Leave empty for a clean default style."
                ),
            ),
            InputField(
                name="generate_broll",
                label="Generate B-Roll Clips",
                field_type="select",
                default="no",
                options=[
                    {"value": "no", "label": "No — talking head only"},
                    {"value": "yes", "label": "Yes — also generate B-roll footage"},
                ],
                help_text=(
                    "Generate cinematic B-roll clips that visually "
                    "support the script. Adds ~$0.40–$0.90 extra."
                ),
            ),
            InputField(
                name="broll_count",
                label="Number of B-Roll Clips",
                field_type="select",
                default="3",
                options=[
                    {"value": "2", "label": "2 clips"},
                    {"value": "3", "label": "3 clips (recommended)"},
                    {"value": "4", "label": "4 clips"},
                ],
                help_text="How many B-roll clips to generate alongside the talking head.",
            ),
        ]

    def get_steps(self):
        return [
            "Analysing headshot",           # 0
            "Preparing script",             # 1
            "Generating speech audio",      # 2
            "Creating talking-head video",  # 3
            "Analysing style reference",    # 4
            "Generating B-roll prompts",    # 5
            "Generating B-roll images",     # 6
            "Generating B-roll videos",     # 7
            "Finalising",                   # 8
        ]

    def validate_inputs(self, inputs):
        """Ensure the user provides either a script or a brief."""
        script = (inputs.get("script") or "").strip()
        brief = (inputs.get("brief") or "").strip()
        if not script and not brief:
            return (
                "Please provide either a Script (what the person should say) "
                "or a Brief (let AI write the script for you)."
            )
        return None

    # ------------------------------------------------------------------
    # Execute — full pipeline
    # ------------------------------------------------------------------

    def execute(self, inputs, run_id, user_id, on_progress=None,
                brand=None, persona=None):
        from tools.config import get_cost
        from tools.providers.tts import generate_speech
        from tools.providers import wavespeed, higgsfield

        outputs = []
        total_cost = 0.0

        # ── Step 0: Analyse headshot ──────────────────────────────────
        self.report_progress(on_progress, 0, "Analysing headshot…")

        headshot_path = inputs.get("headshot", "")
        if not headshot_path or not os.path.isfile(headshot_path):
            return {
                "outputs": [{"type": "text", "title": "❌ Error",
                             "value": "No headshot photo uploaded."}],
                "cost": 0.0,
            }

        # Read headshot bytes for uploading later
        with open(headshot_path, "rb") as f:
            headshot_bytes = f.read()

        # Detect content type from extension
        ext = os.path.splitext(headshot_path)[1].lower()
        img_content_type = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".webp": "image/webp",
        }.get(ext, "image/jpeg")

        # ── Step 1: Prepare script ────────────────────────────────────
        self.report_progress(on_progress, 1, "Preparing script…")

        script = (inputs.get("script") or "").strip()
        brief = (inputs.get("brief") or "").strip()

        if not script:
            if not brief:
                return {
                    "outputs": [{"type": "text", "title": "❌ Error",
                                 "value": "Please provide either a script "
                                          "or a brief for AI to write one."}],
                    "cost": 0.0,
                }

            # Generate script from brief using Gemini
            script = self._generate_script(brief, brand, persona)
            outputs.append({
                "type": "text",
                "title": "📝 AI-Generated Script",
                "value": script,
            })

        # Validate script length for TTS
        if len(script) > 8000:
            script = script[:8000]
            outputs.append({
                "type": "text",
                "title": "⚠️ Script Trimmed",
                "value": "Script was trimmed to 8,000 characters for TTS.",
            })

        # ── Step 2: Generate speech audio ─────────────────────────────
        self.report_progress(on_progress, 2, "Generating speech audio…")

        voice_preset = inputs.get("voice_preset", "natural_female")
        voice_name = _VOICE_MAP.get(voice_preset, "Kore")

        try:
            wav_bytes = generate_speech(
                text=script,
                voice_name=voice_name,
            )
            total_cost += get_cost("gemini-tts", "gemini")
            logger.info(
                "TTS generated: %d bytes, voice=%s",
                len(wav_bytes), voice_name,
            )
        except Exception as exc:
            logger.error("TTS failed: %s", exc, exc_info=True)
            return {
                "outputs": outputs + [{
                    "type": "text", "title": "❌ TTS Error",
                    "value": f"Speech generation failed: {exc}",
                }],
                "cost": total_cost,
            }

        # ── Upload audio + image to CDN ───────────────────────────────
        self.report_progress(
            on_progress, 2, "Uploading media to CDN…"
        )

        try:
            audio_url = wavespeed.upload_media(
                wav_bytes, content_type="audio/wav"
            )
            image_url = wavespeed.upload_media(
                headshot_bytes, content_type=img_content_type
            )
            logger.info(
                "Media uploaded — audio: %s, image: %s",
                audio_url[:80], image_url[:80],
            )
        except Exception as exc:
            logger.error("Media upload failed: %s", exc, exc_info=True)
            return {
                "outputs": outputs + [{
                    "type": "text", "title": "❌ Upload Error",
                    "value": f"Failed to upload media to CDN: {exc}",
                }],
                "cost": total_cost,
            }

        # ── Step 3: Generate talking-head video ───────────────────────
        self.report_progress(
            on_progress, 3,
            "Creating talking-head video… this may take 2–5 minutes."
        )

        # Build a speech prompt for the talking head engine
        speech_prompt = (
            "Natural conversational gestures, subtle head movements, "
            "realistic lip sync, slight body sway"
        )

        video_url = None
        method_used = None

        # Priority 1: Higgsfield Speak v2 (best quality)
        try:
            logger.info("Trying Speak v2 (high quality)…")
            request_id = higgsfield.submit_speak_v2(
                image_url=image_url,
                audio_url=audio_url,
                prompt=speech_prompt,
                quality="high",
                duration=15,
            )
            result = higgsfield.poll_speak_v2(
                request_id, max_wait=600, poll_interval=10
            )
            video_url = result.get("result_url", "")
            if video_url:
                method_used = "speak-v2"
                total_cost += get_cost("speak-v2", "higgsfield")
                logger.info("Speak v2 succeeded: %s", video_url[:80])
        except Exception as exc:
            logger.warning("Speak v2 failed, trying fallback: %s", exc)

        # Priority 2: Higgsfield talking_photo (legacy fallback)
        if not video_url:
            try:
                logger.info("Trying talking_photo (fallback)…")
                gen_id = higgsfield.submit_talking_photo(
                    image_url=image_url,
                    audio_url=audio_url,
                    prompt=speech_prompt,
                )
                result = higgsfield.poll_talking_photo(
                    gen_id, max_wait=300, poll_interval=5
                )
                video_url = result.get("result_url", "")
                if video_url:
                    method_used = "talking-photo"
                    total_cost += get_cost("talking-photo", "higgsfield")
                    logger.info(
                        "talking_photo succeeded: %s", video_url[:80]
                    )
            except Exception as exc:
                logger.warning(
                    "talking_photo failed, trying InfiniteTalk: %s", exc
                )

        # Priority 3: WaveSpeed InfiniteTalk (last resort)
        if not video_url:
            try:
                logger.info("Trying InfiniteTalk (last resort)…")
                get_url = wavespeed.submit_infinitetalk(
                    audio_url=audio_url,
                    image_url=image_url,
                    prompt=speech_prompt,
                    resolution="480p",
                )
                video_url = wavespeed.poll_infinitetalk(
                    get_url, max_wait=600, interval=5
                )
                if video_url:
                    method_used = "infinitetalk"
                    total_cost += get_cost("infinitetalk", "wavespeed")
                    logger.info(
                        "InfiniteTalk succeeded: %s",
                        video_url[:80] if isinstance(video_url, str) else video_url,
                    )
            except Exception as exc:
                logger.error("InfiniteTalk also failed: %s", exc)

        # Record talking-head result
        if video_url:
            outputs.append({
                "type": "video",
                "title": f"🗣️ Talking Head Video ({method_used})",
                "url": video_url,
            })
        else:
            outputs.append({
                "type": "text",
                "title": "❌ All Engines Failed",
                "value": (
                    "All three talking-head engines failed. "
                    "Please check your API keys and try again. "
                    "Make sure HIGGSFIELD_API_KEY_ID, "
                    "HIGGSFIELD_API_KEY_SECRET, and "
                    "WAVESPEED_API_KEY are set in your .env file."
                ),
            })

        # ── Steps 4–7: B-Roll Pipeline (optional) ────────────────────
        do_broll = inputs.get("generate_broll", "no") == "yes"
        broll_count = int(inputs.get("broll_count", "3"))

        if do_broll:
            broll_outputs, broll_cost = self._run_broll_pipeline(
                script=script,
                style_ref_path=inputs.get("style_reference", ""),
                headshot_path=headshot_path,
                broll_count=broll_count,
                brand=brand,
                persona=persona,
                on_progress=on_progress,
            )
            outputs.extend(broll_outputs)
            total_cost += broll_cost
        else:
            # Skip B-roll steps
            self.report_progress(on_progress, 4, "B-roll not selected — skipping")
            self.report_progress(on_progress, 5, "—")
            self.report_progress(on_progress, 6, "—")
            self.report_progress(on_progress, 7, "—")

        # ── Step 8: Finalise ──────────────────────────────────────────
        self.report_progress(on_progress, 8, "Finalising…")

        broll_img_count = sum(1 for o in outputs if o.get("type") == "image")
        broll_vid_count = sum(
            1 for o in outputs
            if o.get("type") == "video" and "B-Roll" in o.get("title", "")
        )

        outputs.append({
            "type": "text",
            "title": "📊 Summary",
            "value": (
                f"**Voice:** {voice_preset.replace('_', ' ').title()}\n"
                f"**Talking-head engine:** {method_used or 'None succeeded'}\n"
                f"**Script length:** {len(script):,} characters\n"
                f"**B-Roll images:** {broll_img_count}\n"
                f"**B-Roll videos:** {broll_vid_count}\n"
                f"**Total cost:** ${total_cost:.2f}"
            ),
        })

        return {
            "outputs": outputs,
            "cost": total_cost,
            "model_used": method_used or "none",
        }

    # ------------------------------------------------------------------
    # B-Roll Pipeline (ported from R52 longform pipeline)
    # ------------------------------------------------------------------

    def _run_broll_pipeline(self, *, script, style_ref_path, headshot_path,
                            broll_count, brand, persona, on_progress):
        """Execute the full B-roll pipeline: analyse → prompts → images → videos.

        Returns:
            tuple[list, float]: (output_items, total_broll_cost)
        """
        outputs = []
        broll_cost = 0.0

        # ── Step 4: Analyse style reference ───────────────────────────
        self.report_progress(on_progress, 4, "Analysing style reference…")
        style_analysis = self._analyse_style_reference(style_ref_path)
        outputs.append({
            "type": "text",
            "title": "🎨 Style Analysis",
            "value": style_analysis[:800],
        })

        # ── Step 5: Generate B-roll prompts ───────────────────────────
        self.report_progress(on_progress, 5, "Generating B-roll prompts…")
        broll_prompts = self._generate_broll_prompts(
            script, style_analysis, broll_count, brand, persona,
        )

        if not broll_prompts:
            outputs.append({
                "type": "text",
                "title": "⚠️ B-Roll Prompts",
                "value": "AI could not generate B-roll prompts. Skipping B-roll.",
            })
            self.report_progress(on_progress, 6, "Skipped")
            self.report_progress(on_progress, 7, "Skipped")
            return outputs, broll_cost

        prompt_summary = "\n\n".join(
            f"**Clip {i + 1} — {p.get('segment_name', 'Untitled')}**\n"
            f"{p.get('image_prompt', '')[:200]}…"
            for i, p in enumerate(broll_prompts)
        )
        outputs.append({
            "type": "text",
            "title": "🎬 B-Roll Prompts",
            "value": prompt_summary,
        })

        # ── Step 6: Generate B-roll images ────────────────────────────
        self.report_progress(on_progress, 6, "Generating B-roll images…")
        broll_images = self._generate_broll_images(
            broll_prompts, style_ref_path, on_progress,
        )

        for img in broll_images:
            outputs.append({
                "type": "image",
                "title": f"🖼️ B-Roll Image — {img['name']}",
                "url": img["url"],
            })
            broll_cost += img.get("cost", 0)

        if not broll_images:
            outputs.append({
                "type": "text",
                "title": "⚠️ B-Roll Images",
                "value": "No B-roll images were generated. Skipping videos.",
            })
            self.report_progress(on_progress, 7, "Skipped")
            return outputs, broll_cost

        # ── Step 7: Generate B-roll videos ────────────────────────────
        self.report_progress(
            on_progress, 7,
            f"Generating {len(broll_images)} B-roll videos… (2–4 min each)"
        )
        broll_videos = self._generate_broll_videos(
            broll_images, broll_prompts, on_progress,
        )

        for vid in broll_videos:
            outputs.append({
                "type": "video",
                "title": f"🎥 B-Roll Video — {vid['name']}",
                "url": vid["url"],
            })
            broll_cost += vid.get("cost", 0)

        if not broll_videos:
            outputs.append({
                "type": "text",
                "title": "⚠️ B-Roll Videos",
                "value": "No B-roll videos were generated. Images are still available above.",
            })

        return outputs, broll_cost

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _generate_script(self, brief, brand=None, persona=None):
        """Use Gemini to write a short video script from a brief."""
        from app.services.agent_service import _call_gemini

        brand_ctx = self.build_brand_context(brand) if brand else ""
        persona_ctx = self.build_persona_context(persona) if persona else ""

        prompt = f"""You are a professional video scriptwriter.

{brand_ctx}
{persona_ctx}

Write a short, natural-sounding script for a talking-head video based on
this brief:

**Brief:** {brief}

RULES:
1. Write ONLY the spoken words — no stage directions, no [brackets].
2. Keep it conversational and natural — like someone talking to a friend.
3. Aim for 30–60 seconds of speech (~100–200 words).
4. Start with a hook that grabs attention in the first 3 seconds.
5. End with a clear call to action.
6. If brand context is provided, match the brand voice and tone.
7. Do NOT use double quotes in the script text.

Output ONLY the script text, nothing else."""

        try:
            script = _call_gemini(prompt)
            return script.strip()
        except Exception as exc:
            logger.error("Script generation failed: %s", exc)
            raise RuntimeError(
                f"AI could not generate a script from your brief: {exc}"
            ) from exc

    # -- B-Roll helpers (ported from R52) --

    def _analyse_style_reference(self, style_ref_path):
        """Analyse a style-reference image using Gemini Vision.

        Returns a text description of the visual style, colors, and mood.
        Falls back to a sensible default if no image or analysis fails.
        """
        default = (
            "No reference image provided. Use a clean, modern, professional "
            "visual style with cinematic lighting, neutral color palette, and "
            "shallow depth of field."
        )
        if not style_ref_path or not os.path.isfile(style_ref_path):
            return default

        try:
            from app.services.agent_service import _call_gemini_with_image
            analysis = _call_gemini_with_image(
                _IMAGE_ANALYSIS_PROMPT, style_ref_path,
            )
            return analysis.strip() if analysis else default
        except Exception as exc:
            logger.warning("Style reference analysis failed: %s", exc)
            return default

    def _generate_broll_prompts(self, script, style_analysis, count,
                                brand=None, persona=None):
        """Generate SEALCaM B-roll prompts from the script + style analysis.

        Returns a list of dicts, each with:
            segment_number, segment_name, image_prompt, video_prompt
        """
        from app.services.agent_service import _call_gemini

        brand_ctx = self.build_brand_context(brand) if brand else ""
        persona_ctx = self.build_persona_context(persona) if persona else ""

        prompt = f"""{_BROLL_SYSTEM_PROMPT}

{brand_ctx}
{persona_ctx}

Generate exactly {count} B-roll segments for the following script.

Visual Style Reference:
{style_analysis}

Script:
{script}

Output ONLY valid JSON with this exact structure:
{{
  "segments": [
    {{
      "segment_number": 1,
      "segment_name": "Short Visual Title",
      "image_prompt": "Subject: ...\\nEnvironment: ...\\nAction: ...\\nLighting: ...\\nCamera: ...\\nMetatokens: ...",
      "video_prompt": "Subject: ...\\nEnvironment: ...\\nAction: ...\\nLighting: ...\\nCamera: ...\\nMetatokens: ..."
    }}
  ]
}}"""

        try:
            raw = _call_gemini(prompt)
            # Strip markdown fences
            cleaned = re.sub(r"```(?:json)?\s*", "", raw)
            cleaned = cleaned.strip().rstrip("`")
            data = json.loads(cleaned)
            segments = data.get("segments", [])
            return segments[:count]
        except Exception as exc:
            logger.error("B-roll prompt generation failed: %s", exc)
            return []

    def _generate_broll_images(self, broll_prompts, style_ref_path=None,
                               on_progress=None):
        """Generate B-roll images from SEALCaM prompts.

        Uses generate_ugc_image (multi-provider). Passes the style reference
        as a local reference image when available.
        """
        from tools.create_image import generate_ugc_image
        from tools.config import get_cost

        ref_paths = None
        if style_ref_path and os.path.isfile(style_ref_path):
            ref_paths = [style_ref_path]

        results = []
        for i, segment in enumerate(broll_prompts):
            img_prompt = segment.get("image_prompt", "")
            name = segment.get("segment_name", f"Clip {i + 1}")
            if not img_prompt:
                continue

            try:
                self.report_progress(
                    on_progress, 6,
                    f"Generating B-roll image {i + 1}/{len(broll_prompts)}…",
                )
                result = generate_ugc_image(
                    prompt=img_prompt,
                    reference_paths=ref_paths,
                    aspect_ratio="16:9",
                    resolution="1K",
                    model="nano-banana-pro",
                )
                img_url = result.get("result_url", "")
                if img_url:
                    cost = get_cost("nano-banana-pro", "google")
                    results.append({
                        "name": name,
                        "url": img_url,
                        "cost": cost,
                        "segment": segment,
                    })
                else:
                    logger.warning(
                        "No image URL for B-roll segment %d", i + 1,
                    )
            except Exception as exc:
                logger.error("B-roll image %d failed: %s", i + 1, exc)

        return results

    def _generate_broll_videos(self, broll_images, broll_prompts,
                               on_progress=None):
        """Generate B-roll video clips from the B-roll images.

        Uses generate_ugc_video (multi-provider) with the video_prompt
        from each segment to describe the desired motion.
        """
        from tools.create_video import generate_ugc_video
        from tools.config import get_cost

        results = []
        for i, img_data in enumerate(broll_images):
            segment = img_data.get("segment", {})
            vid_prompt = segment.get("video_prompt", "")
            name = img_data.get("name", f"Clip {i + 1}")
            img_url = img_data.get("url", "")

            if not img_url or not vid_prompt:
                continue

            try:
                self.report_progress(
                    on_progress, 7,
                    f"Generating B-roll video {i + 1}/{len(broll_images)}…",
                )
                result = generate_ugc_video(
                    prompt=vid_prompt,
                    image_url=img_url,
                    model="kling-3.0",
                    duration="5",
                    aspect_ratio="16:9",
                )
                vid_url = result.get("result_url", "")
                if vid_url:
                    cost = get_cost("kling-3.0", "wavespeed")
                    results.append({
                        "name": name,
                        "url": vid_url,
                        "cost": cost,
                    })
                else:
                    logger.warning(
                        "No video URL for B-roll segment %d", i + 1,
                    )
            except Exception as exc:
                logger.error("B-roll video %d failed: %s", i + 1, exc)

        return results
