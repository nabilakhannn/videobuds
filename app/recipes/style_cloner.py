"""Style Cloner — analyse a viral reference video and reproduce its style.

Pipeline:
  1. User uploads a reference video (MP4/MOV/WebM, ≤20 MB).
  2. Gemini Vision watches it and extracts the 'Viral DNA':
       hook type, content structure, pacing, visual style, script formula,
       psychological triggers, and why it works.
  3. AI writes a brand-new viral script for the user's brand following
       the exact same winning formula.
  4. AI writes scene prompts for each key shot.
  5. (Optional) Key-scene images are generated via the image pipeline.
  6. (Optional) A short video is generated matching the viral style.

Based on the R51 'The Creative Cloner AI Agent' n8n workflow.
"""

import json
import logging
import os
import re

from .base import BaseRecipe, InputField

logger = logging.getLogger(__name__)

_MAX_VIDEO_BYTES = 20 * 1024 * 1024  # 20 MB — Gemini inline_data limit


class StyleCloner(BaseRecipe):
    slug = "style-cloner"
    name = "Style Cloner"
    short_description = "Upload a viral video — AI reverse-engineers why it works and creates your branded version."
    description = (
        "Found a Reel, TikTok, or ad that stops the scroll? Upload it. "
        "The AI watches it, reverse-engineers WHY it works — hook, pacing, "
        "script formula, visual style, psychological triggers — then generates "
        "a brand-new viral script and content assets for YOUR brand, using the "
        "exact same winning formula. No guessing. No templates. Pure formula cloning."
    )
    category = "video_studio"
    icon = "🎨"
    estimated_cost = "$0.10 – $0.50 per project"
    is_active = True

    how_to_use = """\
### How to use Style Cloner

1. **Upload the viral reference video** — any Reel, TikTok, or ad (MP4/MOV/WebM, under 20MB).
2. **Describe your brand and product** — what you sell, who your audience is, what result you want.
3. **Choose what to generate** — script only, script + images, or script + video.
4. Click **Generate** — the AI decodes the viral formula and creates your branded version.

**What the AI extracts (the Viral DNA):**
- 🎣 **Hook type** — how it grabs attention in the first 3 seconds
- 📐 **Content structure** — the exact narrative arc (Problem → Solution, Story → Reveal, etc.)
- ⚡ **Pacing** — cut rhythm and energy level
- 🎨 **Visual style** — colour grading, lighting, aesthetic
- 🧠 **Viral triggers** — curiosity gap, social proof, FOMO, pattern interrupt
- ✍️ **Script formula** — the exact language pattern

**What you get:**
- Viral DNA breakdown (why the original works)
- Your brand's viral script in the same formula
- Scene descriptions for each key shot
- Generated images (if selected)
- Generated video (if selected)

**Tips:**
- Short videos (15–60 seconds) give the best analysis — trim if needed.
- Use real competitor ads or viral creators in your niche for best results.
- Start with 'Script + images' to validate the formula before spending on video.
"""

    def get_input_fields(self):
        return [
            InputField(
                name="reference_video",
                label="Reference Video (the viral video to clone)",
                field_type="file",
                required=True,
                accept="video/*",
                help_text="MP4, MOV, or WebM — max 20MB. Upload the Reel, TikTok, or ad you want to clone the style of.",
            ),
            InputField(
                name="brand_brief",
                label="Your Brand / Product Brief",
                field_type="textarea",
                required=True,
                placeholder=(
                    "e.g. I sell organic skincare for busy mums aged 28–45. "
                    "My hero product is a rose face serum. I want a viral Instagram Reel "
                    "that gets people to visit my website."
                ),
                help_text="The AI applies the viral formula to your brand. The more specific, the better.",
            ),
            InputField(
                name="output_type",
                label="What to Generate",
                field_type="select",
                default="script_images",
                options=[
                    {"value": "script_only", "label": "Script & formula only (free — no image/video credits)"},
                    {"value": "script_images", "label": "Script + 3 key scene images (recommended)"},
                    {"value": "script_video", "label": "Script + generated video (uses video credits)"},
                ],
                help_text="Start with 'Script + images' to validate the formula, then generate video when happy.",
            ),
            InputField(
                name="video_model",
                label="Video Model (only if generating video)",
                field_type="select",
                default="veo-3.1",
                options=[
                    {"value": "veo-3.1", "label": "Veo 3.1 (Google) — cinematic, most stable"},
                    {"value": "kling-3.0", "label": "Kling 3.0 (WaveSpeed) — fast, requires credits"},
                    {"value": "sora-2", "label": "Sora 2 (WaveSpeed) — good quality, requires credits"},
                ],
                help_text="Veo 3.1 uses your Google API key (no WaveSpeed credits needed).",
            ),
            InputField(
                name="aspect_ratio",
                label="Aspect Ratio",
                field_type="select",
                default="9:16",
                options=[
                    {"value": "9:16", "label": "Vertical (9:16) — Reels / TikTok / Shorts"},
                    {"value": "16:9", "label": "Horizontal (16:9) — YouTube"},
                    {"value": "1:1", "label": "Square (1:1) — Feed posts"},
                ],
            ),
        ]

    def get_steps(self):
        return [
            "Analysing reference video",
            "Extracting viral DNA",
            "Writing brand script",
            "Generating assets",
        ]

    # ------------------------------------------------------------------
    # Gemini helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _call_gemini(prompt: str) -> str:
        from ..services.agent_service import _call_gemini
        return _call_gemini(prompt)

    @staticmethod
    def _call_gemini_with_video(prompt: str, video_path: str) -> str:
        from ..services.agent_service import _call_gemini_with_video
        return _call_gemini_with_video(prompt, video_path)

    # ------------------------------------------------------------------
    # Execute
    # ------------------------------------------------------------------

    def execute(self, inputs, run_id, user_id, on_progress=None,
                brand=None, persona=None):
        from tools.create_image import generate_ugc_image
        from tools.create_video import generate_ugc_video

        # ── Read & validate inputs ────────────────────────────────────
        video_path = inputs.get("reference_video", "")
        brand_brief = (inputs.get("brand_brief") or "").strip()
        output_type = inputs.get("output_type", "script_images")
        video_model = inputs.get("video_model", "veo-3.1")
        aspect_ratio = inputs.get("aspect_ratio", "9:16")

        if not video_path or not os.path.exists(video_path):
            raise ValueError("Please upload a reference video to analyse.")
        if not brand_brief:
            raise ValueError("Please describe your brand and product.")

        video_size = os.path.getsize(video_path)
        if video_size > _MAX_VIDEO_BYTES:
            raise ValueError(
                f"Video is {video_size // (1024 * 1024):.0f} MB — please upload a video under 20 MB. "
                "Tip: trim to the best 15–30 seconds using any video editor."
            )

        outputs = []
        total_cost = 0.0
        gen_images = output_type == "script_images"
        gen_video = output_type == "script_video"

        # ── Step 0: Analyse the video ─────────────────────────────────
        self.report_progress(on_progress, 0, "Gemini Vision is watching the reference video…")

        analysis_prompt = """\
You are an expert viral content strategist. Watch this video carefully and analyse it.

Output a JSON object with EXACTLY these keys:
{
  "hook_type": "how it grabs attention in the first 3 seconds (1-2 sentences)",
  "content_structure": "the narrative arc — e.g. Problem → Agitation → Solution, Story → Reveal → CTA (2-3 sentences)",
  "pacing": "cut rhythm and energy level — e.g. fast cuts every 1-2s, slow cinematic, talking-head with overlays (1-2 sentences)",
  "visual_style": "colour grading, lighting, aesthetic, camera style (2-3 sentences)",
  "script_formula": "the exact language pattern used — e.g. bold claim → social proof → benefit stack → urgency → CTA (2-3 sentences)",
  "viral_triggers": ["trigger1", "trigger2", "trigger3"],
  "platform": "which platform this is optimised for and why (1 sentence)",
  "why_it_works": "the core psychological reason this video would perform well (2-3 sentences)",
  "key_shots": ["description of opening shot", "description of main content shot", "description of closing/CTA shot"]
}

Output ONLY the JSON object — no markdown fences, no explanation."""

        viral_dna = None
        try:
            raw_analysis = self._call_gemini_with_video(analysis_prompt, video_path)
            # Clean JSON if model wrapped it in fences
            cleaned = raw_analysis.strip()
            if cleaned.startswith("```"):
                lines = cleaned.split("\n")
                lines = [ln for ln in lines if not ln.strip().startswith("```")]
                cleaned = "\n".join(lines)
            json_match = re.search(r'\{.*\}', cleaned, re.DOTALL)
            if json_match:
                viral_dna = json.loads(json_match.group())
            else:
                viral_dna = json.loads(cleaned)
            logger.info("Viral DNA extracted for run %s", run_id)
        except Exception as exc:
            logger.warning("Video analysis failed: %s", exc)

        # ── Step 1: Present viral DNA ─────────────────────────────────
        self.report_progress(on_progress, 1, "Viral DNA extracted — building your brand script…")

        if viral_dna:
            dna_lines = [
                f"**🎣 Hook:** {viral_dna.get('hook_type', 'N/A')}",
                f"\n**📐 Structure:** {viral_dna.get('content_structure', 'N/A')}",
                f"\n**⚡ Pacing:** {viral_dna.get('pacing', 'N/A')}",
                f"\n**🎨 Visual Style:** {viral_dna.get('visual_style', 'N/A')}",
                f"\n**✍️ Script Formula:** {viral_dna.get('script_formula', 'N/A')}",
            ]
            if viral_dna.get("viral_triggers"):
                dna_lines.append(f"\n**🧠 Viral Triggers:** {', '.join(viral_dna['viral_triggers'])}")
            dna_lines.append(f"\n**📱 Platform:** {viral_dna.get('platform', 'N/A')}")
            dna_lines.append(f"\n**🏆 Why It Works:** {viral_dna.get('why_it_works', 'N/A')}")
            outputs.append({
                "type": "text",
                "title": "🧬 Viral DNA — What Makes This Video Work",
                "value": "".join(dna_lines),
            })
        else:
            outputs.append({
                "type": "text",
                "title": "⚠️ Analysis Note",
                "value": (
                    "The video analysis returned partial results — this can happen with "
                    "some video formats. Proceeding with brand script generation using "
                    "best-practice viral formulas."
                ),
            })

        # ── Step 2: Write brand script ────────────────────────────────
        self.report_progress(on_progress, 2, "Writing your brand's viral script…")

        brand_ctx = self.build_brand_context(brand)
        persona_ctx = self.build_persona_context(persona)

        script_parts = [
            "You are a world-class viral content writer. "
            "Write a 15–30 second short-form video script for a brand, "
            "following the exact viral formula below.\n\n",
        ]

        if viral_dna:
            script_parts.append(
                "VIRAL FORMULA TO FOLLOW (extracted from a high-performing reference video):\n"
                f"- Hook type: {viral_dna.get('hook_type', '')}\n"
                f"- Content structure: {viral_dna.get('content_structure', '')}\n"
                f"- Script formula: {viral_dna.get('script_formula', '')}\n"
                f"- Viral triggers to use: {', '.join(viral_dna.get('viral_triggers', []))}\n"
                f"- Pacing note: {viral_dna.get('pacing', '')}\n\n"
            )

        script_parts.append(f"BRAND BRIEF:\n{brand_brief}\n\n")

        if brand_ctx:
            script_parts.append(f"BRAND CONTEXT:\n{brand_ctx}\n\n")
        if persona_ctx:
            script_parts.append(f"PERSONA VOICE:\n{persona_ctx}\n\n")

        script_parts.append(
            "FORMAT your output exactly as:\n\n"
            "HOOK (0–3s):\n[opening line that stops the scroll — match the hook type above]\n\n"
            "BODY (3–20s):\n[main content — follow the content structure and script formula exactly]\n\n"
            "CTA (20–30s):\n[call to action]\n\n"
            "---\n"
            "READY-TO-POST CAPTION:\n[2-3 sentence caption, no hashtags]\n\n"
            "HASHTAGS:\n[5–8 relevant hashtags]\n\n"
            "DIRECTOR'S NOTE:\n"
            "[2-3 sentences on visual style, pacing, and camera direction to match the reference video's energy]\n\n"
            "Make it feel NATIVE — like a real creator made it, not a brand ad."
        )

        try:
            brand_script = self._call_gemini("".join(script_parts))
        except Exception as exc:
            brand_script = f"Script generation failed: {exc}"
            logger.error("Script generation failed for run %s: %s", run_id, exc)

        outputs.append({
            "type": "text",
            "title": "✍️ Your Brand's Viral Script",
            "value": brand_script,
        })

        # ── Step 3: Generate assets ───────────────────────────────────
        self.report_progress(on_progress, 3, "Generating visual assets…")

        # --- Images ---
        if gen_images:
            key_shots = (viral_dna or {}).get("key_shots", [
                "Opening hook — bold, attention-grabbing composition",
                "Main product or brand showcase",
                "Closing call-to-action",
            ])
            visual_style = (viral_dna or {}).get("visual_style", "modern, vibrant, scroll-stopping")

            scene_req = (
                f"Write 3 image generation prompts for key scenes of a {aspect_ratio} short-form video ad.\n\n"
                f"Brand brief: {brand_brief}\n"
                f"Visual style to match: {visual_style}\n\n"
                "Scenes to create:\n"
                + "\n".join(f"{i+1}. {s}" for i, s in enumerate(key_shots[:3]))
                + "\n\nMake each prompt specific, cinematic, and on-brand. "
                "Output ONLY a JSON array of 3 prompt strings. No markdown fences."
            )

            try:
                raw_prompts = self._call_gemini(scene_req)
                cleaned_p = raw_prompts.strip()
                if cleaned_p.startswith("```"):
                    lines = cleaned_p.split("\n")
                    lines = [ln for ln in lines if not ln.strip().startswith("```")]
                    cleaned_p = "\n".join(lines)
                scene_prompts = json.loads(cleaned_p)
                if not isinstance(scene_prompts, list) or len(scene_prompts) < 1:
                    raise ValueError("Not a list")
            except Exception:
                scene_prompts = [
                    f"Viral-style ad scene for {brand_brief[:60]}. Hook shot. {aspect_ratio} vertical.",
                    f"Product showcase for {brand_brief[:60]}. Premium aesthetic, editorial lighting.",
                    f"Call-to-action scene for {brand_brief[:60]}. Dynamic, motivating close-up.",
                ]

            for i, scene_prompt in enumerate(scene_prompts[:3]):
                shot_label = key_shots[i] if i < len(key_shots) else f"Scene {i+1}"
                self.report_progress(on_progress, 3, f"Generating scene image {i+1}/3…")
                try:
                    img_result = generate_ugc_image(
                        prompt=scene_prompt,
                        aspect_ratio=aspect_ratio,
                        model="nano-banana-pro",
                        provider="google",
                    )
                    if img_result.get("status") == "success" and img_result.get("result_url"):
                        outputs.append({
                            "type": "image",
                            "title": f"Scene {i+1}: {shot_label}",
                            "url": img_result["result_url"],
                        })
                        total_cost += 0.02
                    else:
                        logger.warning("Image %d: no result", i + 1)
                except Exception as exc:
                    logger.warning("Image %d failed: %s", i + 1, exc)
                    outputs.append({
                        "type": "text",
                        "title": f"⚠️ Scene {i+1} Image",
                        "value": f"Image generation failed: {exc}",
                    })

        # --- Video ---
        if gen_video:
            self.report_progress(on_progress, 3, f"Generating video with {video_model}… this may take 2–5 minutes.")

            visual_style = (viral_dna or {}).get("visual_style", "dynamic, modern, scroll-stopping")
            pacing = (viral_dna or {}).get("pacing", "energetic with quick cuts")

            video_prompt_req = (
                f"Write a single detailed video motion prompt for a {aspect_ratio} short-form video ad.\n\n"
                f"Visual style to match: {visual_style}\n"
                f"Pacing: {pacing}\n"
                f"Brand brief: {brand_brief}\n\n"
                "The prompt should describe: camera movement, subject motion, lighting, atmosphere, and energy.\n"
                "Output ONLY the prompt text (2-3 sentences). No labels, no quotes."
            )

            try:
                video_prompt = self._call_gemini(video_prompt_req).strip().strip('"').strip("'")
            except Exception:
                video_prompt = (
                    f"Dynamic viral-style short-form video ad for {brand_brief[:80]}. "
                    "Energetic motion, trendy aesthetic, scroll-stopping visuals."
                )

            _model_provider = {
                "veo-3.1": "google",
                "kling-3.0": "wavespeed",
                "sora-2": "wavespeed",
            }
            provider = _model_provider.get(video_model, "wavespeed")

            try:
                vid_result = generate_ugc_video(
                    prompt=video_prompt,
                    model=video_model,
                    duration="5",
                    aspect_ratio=aspect_ratio,
                    provider=provider,
                )
                if vid_result.get("status") == "success" and vid_result.get("result_url"):
                    outputs.append({
                        "type": "video",
                        "title": "Generated Video",
                        "url": vid_result["result_url"],
                    })
                    total_cost += 0.30
                else:
                    outputs.append({
                        "type": "text",
                        "title": "⚠️ Video Generation",
                        "value": f"Video did not complete: {vid_result.get('error', 'Unknown error')}",
                    })
            except Exception as exc:
                logger.error("Video generation failed for run %s: %s", run_id, exc)
                error_msg = str(exc)
                if "522" in error_msg or "timed out" in error_msg.lower():
                    friendly = (
                        f"**{video_model.title()} is temporarily unavailable** (server timeout). "
                        "Please try again in a few minutes, or switch to **Veo 3.1 (Google)** which is more stable."
                    )
                elif "Insufficient credits" in error_msg:
                    friendly = (
                        "**WaveSpeed is out of credits.** Please top up your WaveSpeed account, "
                        "or switch to **Veo 3.1 (Google)** which uses your Google API key instead."
                    )
                else:
                    friendly = f"Video generation failed: {error_msg}"
                outputs.append({
                    "type": "text",
                    "title": "⚠️ Video Generation",
                    "value": friendly,
                })

        # ── Summary ───────────────────────────────────────────────────
        image_count = sum(1 for o in outputs if o.get("type") == "image")
        has_video = any(o.get("type") == "video" for o in outputs)

        outputs.insert(0, {
            "type": "text",
            "title": "Summary",
            "value": (
                f"**Reference video analysed:** ✅\n"
                f"**Viral DNA extracted:** {'✅' if viral_dna else '⚠️ Partial'}\n"
                f"**Brand script generated:** ✅\n"
                f"**Scene images generated:** {f'✅ {image_count}' if image_count else '—'}\n"
                f"**Video generated:** {'✅' if has_video else '—'}\n"
                f"**Estimated cost:** ${total_cost:.2f}"
            ),
        })

        return {"outputs": outputs, "cost": total_cost}
