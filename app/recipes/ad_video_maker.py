"""Ad Video Maker — turn a product photo into AI-generated UGC ad videos.

Implements the **Compound Engineering** pipeline with **Ralph Loop**
(Research → Analyze → Learn → Plan → Hypothesize) and a mandatory
**script-approval gate** between the script and production phases.

Two-phase architecture (SOLID: Single Responsibility per phase):
  Phase 1 — SCRIPT  (Research + Analyze + Plan)
    1. Multimodal Gemini call — AI *sees* the product image (not text-only)
    2. Product-anchored scene writing — every scene must reference the
       actual product, its features, colors, and materials
    3. Outputs saved → status set to ``awaiting_approval``

  Phase 2 — PRODUCTION  (after user approves / edits the script)
    4. Generate a hero image per scene (tools/create_image)
    5. Turn each image into a short video (tools/create_video)
    6. Organize all assets in ``references/outputs/run_<id>/``
"""

import json
import logging
import os
import shutil

from .base import BaseRecipe, InputField

logger = logging.getLogger(__name__)


class AdVideoMaker(BaseRecipe):
    slug = "ad-video-maker"
    name = "Ad Video Maker"
    short_description = "Turn a product photo into scroll-stopping UGC-style ad videos."
    description = (
        "Upload a product or brand photo, and the AI analyses it to understand "
        "your product's exact look, colours, and features. It then writes creative "
        "ad scenes anchored to YOUR product. You review and approve the script "
        "before any videos are generated — no wasted credits, no off-brand content."
    )
    category = "content_creation"
    icon = "🎬"
    estimated_cost = "$0.00 – $0.50 per video"

    how_to_use = """\
### How to use Ad Video Maker

1. **Upload a photo** — a product shot, lifestyle image, or brand visual.
2. **Choose how many videos** you want (1, 3, or 5).
3. *(Optional)* Write a short script or dialogue line.
4. **Pick the aspect ratio** — 9:16 (vertical / Reels) or 16:9 (horizontal).
5. Click **Generate** — the AI will analyse your image and write a script.
6. **Review the script** — edit scenes, motion prompts, or ad copy as needed.
7. Click **Approve & Generate Videos** when you're happy with the script.
8. Wait a few minutes while images and videos are generated.
9. Preview, download, or re-run.

**What happens behind the scenes:**
- Step 1: AI **looks at** your photo (multimodal vision) and describes exactly
  what it sees — product type, colours, materials, shapes.
- Step 2: AI writes scene descriptions anchored to those real product details.
- ⏸️ **You review & approve** the script before any media is generated.
- Step 3: Images are generated for each approved scene.
- Step 4: Images are turned into short videos.
- Step 5: All assets are organized and ready for download.

**Tips:**
- Use a high-quality, well-lit product photo for the best results.
- Edit the generated scenes to make them more specific to your brand.
- The more specific your script, the more on-brand the output.
"""

    # ------------------------------------------------------------------
    # Input fields (rendered by the generic run form)
    # ------------------------------------------------------------------

    def get_input_fields(self):
        return [
            InputField(
                name="reference_image",
                label="Product / Brand Photo",
                field_type="file",
                required=True,
                accept="image/*",
                help_text="Upload a clear photo of your product or brand visual.",
            ),
            InputField(
                name="video_count",
                label="How many videos?",
                field_type="select",
                default="1",
                options=[
                    {"value": "1", "label": "1 video"},
                    {"value": "3", "label": "3 videos"},
                    {"value": "5", "label": "5 videos"},
                ],
            ),
            InputField(
                name="script",
                label="Script / Dialogue (optional)",
                field_type="textarea",
                required=False,
                placeholder="e.g. 'These sunglasses are made for the bold — lightweight titanium, UV400 lenses…'",
                help_text="Leave blank and the AI will write one for you.",
            ),
            InputField(
                name="aspect_ratio",
                label="Aspect Ratio",
                field_type="select",
                default="9:16",
                options=[
                    {"value": "9:16", "label": "Vertical (9:16) — Reels / TikTok"},
                    {"value": "16:9", "label": "Horizontal (16:9) — YouTube"},
                ],
            ),
        ]

    def get_steps(self):
        return [
            "Analysing your image (vision AI)",
            "Writing product-anchored scenes",
            "Generating scene images",
            "Creating videos",
            "Organising assets",
        ]

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _call_gemini(prompt: str) -> str:
        """Call Gemini text API — thin wrapper around agent_service helper."""
        from ..services.agent_service import _call_gemini
        return _call_gemini(prompt)

    @staticmethod
    def _call_gemini_vision(prompt: str, image_path: str) -> str:
        """Call Gemini with text + image (multimodal) so AI actually sees the product."""
        from ..services.agent_service import _call_gemini_with_image
        return _call_gemini_with_image(prompt, image_path)

    @staticmethod
    def _clean_json(raw: str) -> str:
        """Strip Markdown fences from Gemini JSON output."""
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            cleaned = "\n".join(lines)
        return cleaned

    def _get_run_output_dir(self, run_id):
        """Return (and create) a structured output directory for this run."""
        from tools.config import PROJECT_ROOT
        output_dir = os.path.join(
            PROJECT_ROOT, "references", "outputs", f"run_{run_id}"
        )
        os.makedirs(output_dir, exist_ok=True)
        return output_dir

    # ------------------------------------------------------------------
    # Phase dispatcher
    # ------------------------------------------------------------------

    def execute(self, inputs, run_id, user_id, on_progress=None,
                brand=None, persona=None):
        """Dispatch to the correct phase based on ``inputs['_phase']``."""
        phase = inputs.get("_phase", "script")

        if phase == "production":
            return self._execute_production(inputs, run_id, user_id, on_progress,
                                            brand=brand, persona=persona)
        else:
            return self._execute_script(inputs, run_id, user_id, on_progress,
                                        brand=brand, persona=persona)

    # ------------------------------------------------------------------
    # Phase 1: SCRIPT (Research → Analyze → Plan)
    # ------------------------------------------------------------------

    def _execute_script(self, inputs, run_id, user_id, on_progress=None,
                        brand=None, persona=None):
        """Phase 1: Analyse the product image and write creative scenes.

        Uses **multimodal Gemini** so the AI actually *sees* the product.
        Injects brand voice and persona context when available.
        Returns ``{"phase": "script", ...}`` which tells the route handler
        to set the run status to ``awaiting_approval``.
        """
        reference_image = inputs.get("reference_image")
        video_count = int(inputs.get("video_count", "1"))
        script = inputs.get("script", "")
        aspect_ratio = inputs.get("aspect_ratio", "9:16")

        # Build optional brand/persona context blocks
        brand_ctx = self.build_brand_context(brand)
        persona_ctx = self.build_persona_context(persona)

        outputs = []

        # ── Step 0: RESEARCH + ANALYZE — multimodal image analysis ────
        self.report_progress(on_progress, 0, "Analysing your image with vision AI…")

        analysis_prompt = (
            "You are an expert creative director with perfect visual acuity. "
            "LOOK CAREFULLY at this product photo and describe EXACTLY what you see.\n\n"
            "Your analysis MUST include:\n"
            "1. **Product Identity**: What EXACTLY is this product? (e.g. 'aviator sunglasses', "
            "'wireless earbuds', 'leather handbag') — be specific, not generic.\n"
            "2. **Physical Details**: Describe the shape, materials, textures, finishes, "
            "and any distinctive design features you can see.\n"
            "3. **Colors**: List the EXACT colors visible in the product (not the background).\n"
            "4. **Brand Cues**: Any visible logos, text, packaging, or branding elements.\n"
            "5. **Visual Style**: The photography style (studio, lifestyle, flat lay) and lighting.\n"
            "6. **Target Audience**: Based on the product's design and positioning, "
            "who would buy this?\n\n"
            "Be PRECISE and DETAILED. Your analysis will be used to create ad content "
            "that MUST accurately represent THIS specific product. "
            "Do NOT invent features you cannot see. "
            "Output ONLY the analysis text."
        )

        try:
            if reference_image and os.path.exists(reference_image):
                # ★ MULTIMODAL — AI actually sees the image
                image_analysis = self._call_gemini_vision(
                    analysis_prompt, reference_image
                )
                logger.info("Ad Video Maker: multimodal analysis succeeded for run %s", run_id)
            else:
                # Fallback to text-only if no image file
                image_analysis = self._call_gemini(analysis_prompt)
        except Exception as exc:
            logger.warning("Ad Video Maker: image analysis fallback – %s", exc)
            image_analysis = (
                "Unable to analyse the image. Using generic product description. "
                "Please review and edit the scenes below to match your product."
            )

        outputs.append({
            "label": "🔍 Product Analysis (Vision AI)",
            "type": "text",
            "value": image_analysis,
        })

        # ── Step 1: PLAN — write product-anchored creative scenes ─────
        self.report_progress(on_progress, 1, "Writing product-anchored scenes…")

        scene_prompt = (
            f"You are writing exactly {video_count} unique ad scene(s) for short-form "
            f"UGC video content ({aspect_ratio} format).\n\n"
            "═══ CRITICAL PRODUCT CONTEXT ═══\n"
            "The following is a DETAILED analysis of the ACTUAL product from its photo. "
            "Every scene you write MUST feature THIS SPECIFIC product — not a similar one, "
            "not a different category, not a generic item.\n\n"
            f"{image_analysis}\n\n"
            "═══ END PRODUCT CONTEXT ═══\n\n"
        )

        # Inject brand and persona context if provided
        if brand_ctx:
            scene_prompt += (
                f"{brand_ctx}\n"
                "Use the brand's voice, target audience, and guidelines above to "
                "ensure the ad copy and scene descriptions align with the brand identity.\n\n"
            )
        if persona_ctx:
            scene_prompt += (
                f"{persona_ctx}\n"
                "Write all ad copy in this persona's voice and tone. "
                "Use the keywords and phrases listed above. "
                "Avoid the words listed under 'Never Use Words'.\n\n"
            )

        if script:
            scene_prompt += (
                f"The user provided this script/dialogue to incorporate:\n"
                f'"{script}"\n\n'
                "Use the user's script as the basis but adapt it to work with "
                "the visual scenes below.\n\n"
            )
        else:
            scene_prompt += (
                "No user script provided — write catchy, authentic UGC-style dialogue "
                "that specifically references the product's real features, colors, and "
                "materials described in the analysis above.\n\n"
            )

        scene_prompt += (
            "For each scene provide:\n"
            '- "scene_description": A detailed image prompt (2-3 sentences). '
            "MUST show the EXACT product described above — mention its specific type, "
            "colors, materials, and distinctive features. Include subject, setting, "
            "composition, lighting, and mood.\n"
            '- "video_motion": A short video motion / animation prompt (1 sentence). '
            "Describe camera movement and action featuring the product.\n"
            '- "ad_copy": A punchy ad caption (1-2 sentences) that references '
            "the product's real attributes.\n\n"
            "RULES:\n"
            "- The product described in the analysis MUST be the central focus "
            "of every scene.\n"
            "- Do NOT introduce unrelated products or switch product categories.\n"
            "- Reference specific colors, materials, or features from the analysis.\n"
            "- Each scene should show the product from a different angle or context.\n\n"
            f"Output a JSON array of exactly {video_count} object(s). Example:\n"
            '[{"scene_description":"...","video_motion":"...","ad_copy":"..."}]\n\n'
            "Output ONLY the JSON array, no markdown fences, no explanation."
        )

        try:
            raw_scenes = self._call_gemini(scene_prompt)
            scenes = json.loads(self._clean_json(raw_scenes))
            if not isinstance(scenes, list) or len(scenes) == 0:
                raise ValueError("Expected a non-empty JSON array of scenes")
        except Exception as exc:
            logger.error("Ad Video Maker: scene generation failed – %s", exc)
            raise RuntimeError(f"Failed to generate creative scenes: {exc}") from exc

        # Trim to requested count (Gemini sometimes over-generates)
        scenes = scenes[:video_count]

        # Add each scene as a separate output for the approval UI
        for idx, scene in enumerate(scenes):
            outputs.append({
                "label": f"Scene {idx + 1}",
                "type": "scene",
                "index": idx,
                "scene_description": scene.get("scene_description", ""),
                "video_motion": scene.get("video_motion", ""),
                "ad_copy": scene.get("ad_copy", ""),
            })

        # Signal to the route handler: pause for approval
        return {
            "phase": "script",
            "outputs": outputs,
            "cost": 0.0,  # No media cost yet
        }

    # ------------------------------------------------------------------
    # Phase 2: PRODUCTION (Generate images + videos from approved scenes)
    # ------------------------------------------------------------------

    def _execute_production(self, inputs, run_id, user_id, on_progress=None,
                            brand=None, persona=None):
        """Phase 2: Generate images and videos from the approved scenes.

        Called after the user has reviewed and (optionally) edited the script.
        The approved scenes arrive in ``inputs['_approved_scenes']``.
        """
        approved_scenes = inputs.get("_approved_scenes", [])
        reference_image = inputs.get("reference_image")
        aspect_ratio = inputs.get("aspect_ratio", "9:16")
        script_outputs = inputs.get("_script_outputs", [])

        if not approved_scenes:
            raise RuntimeError("No approved scenes to produce.")

        # Start outputs with the script-phase outputs (analysis, scenes text)
        outputs = list(script_outputs)
        total_cost = 0.0

        # Create organized output directory
        output_dir = self._get_run_output_dir(run_id)

        # Copy the reference image into the run folder
        if reference_image and os.path.exists(reference_image):
            ref_ext = os.path.splitext(reference_image)[1]
            ref_dest = os.path.join(output_dir, f"input_product{ref_ext}")
            try:
                shutil.copy2(reference_image, ref_dest)
            except Exception:
                pass

        # ── Step 2: Generate scene images ─────────────────────────────
        self.report_progress(on_progress, 2, f"Generating {len(approved_scenes)} scene image(s)…")

        from tools.create_image import generate_ugc_image
        from tools.config import get_actual_cost as _actual_cost

        reference_paths = (
            [reference_image]
            if reference_image and os.path.exists(reference_image)
            else []
        )

        # Auto-inject brand photo library as additional reference
        brand_refs = self.get_brand_reference_paths(brand, purpose="product", limit=3)
        if brand_refs:
            reference_paths.extend(brand_refs)
            logger.info("Ad Video Maker: added %d brand reference image(s)", len(brand_refs))

        reference_paths = reference_paths or None

        image_results = []
        for idx, scene in enumerate(approved_scenes):
            self.report_progress(
                on_progress, 2,
                f"Generating image {idx + 1} of {len(approved_scenes)}…",
            )
            img_prompt = scene.get("scene_description", "A product advertisement scene")

            try:
                result = generate_ugc_image(
                    prompt=img_prompt,
                    reference_paths=reference_paths,
                    aspect_ratio=aspect_ratio,
                    resolution="1K",
                    model="nano-banana-pro",
                    provider="google",
                )
                image_results.append(result)
                total_cost += _actual_cost("nano-banana-pro", "google")

                # Copy generated image to run folder
                self._copy_asset_to_run_dir(
                    result.get("result_url"), output_dir,
                    f"scene_{idx + 1}_image",
                )
            except Exception as exc:
                logger.error("Ad Video Maker: image %d failed – %s", idx + 1, exc)
                image_results.append({
                    "status": "error",
                    "error": str(exc),
                    "result_url": None,
                })

        # ── Step 3: Create videos ─────────────────────────────────────
        self.report_progress(on_progress, 3, f"Creating {len(approved_scenes)} video(s)…")

        from tools.create_video import generate_ugc_video

        video_results = []
        for idx, (scene, img_res) in enumerate(zip(approved_scenes, image_results)):
            self.report_progress(
                on_progress, 3,
                f"Creating video {idx + 1} of {len(approved_scenes)}…",
            )

            source_url = img_res.get("result_url") if img_res.get("status") != "error" else None
            if not source_url:
                video_results.append({
                    "status": "error",
                    "error": "No source image available",
                    "result_url": None,
                })
                continue

            motion_prompt = scene.get(
                "video_motion",
                "Gentle camera movement revealing the product, cinematic feel",
            )

            try:
                result = generate_ugc_video(
                    prompt=motion_prompt,
                    image_url=source_url,
                    model="veo-3.1",
                    duration="8",
                    aspect_ratio=aspect_ratio,
                    provider="google",
                )
                video_results.append(result)
                total_cost += _actual_cost("veo-3.1", "google")

                # Copy generated video to run folder
                self._copy_asset_to_run_dir(
                    result.get("result_url"), output_dir,
                    f"scene_{idx + 1}_video",
                )
            except Exception as exc:
                logger.error("Ad Video Maker: video %d failed – %s", idx + 1, exc)
                video_results.append({
                    "status": "error",
                    "error": str(exc),
                    "result_url": None,
                })

        # ── Step 4: Organise & finalise output ────────────────────────
        self.report_progress(on_progress, 4, "Organising assets…")

        for idx, (scene, img_res, vid_res) in enumerate(
            zip(approved_scenes, image_results, video_results)
        ):
            ad_copy = scene.get("ad_copy", f"Scene {idx + 1}")
            label = f"🎬 Scene {idx + 1}: {ad_copy[:60]}"

            entry = {"label": label, "scene": scene}

            # Attach image URL
            if img_res.get("result_url"):
                entry["image_url"] = img_res["result_url"]

            # Attach video URL (primary download link)
            if vid_res.get("result_url"):
                entry["url"] = vid_res["result_url"]
                entry["type"] = "video"
            else:
                err = vid_res.get("error", "Unknown error")
                entry["value"] = f"Video generation error: {err}"

            outputs.append(entry)

        # Save metadata file in the run folder
        self._save_run_metadata(output_dir, run_id, approved_scenes, outputs, total_cost)

        return {"outputs": outputs, "cost": total_cost}

    # ------------------------------------------------------------------
    # Asset organization helpers
    # ------------------------------------------------------------------

    def _copy_asset_to_run_dir(self, url_or_path, output_dir, base_name):
        """Copy a generated asset into the organized run directory.

        Handles both ``/api/outputs/<file>`` web paths and absolute file paths.
        """
        if not url_or_path:
            return

        from tools.config import PROJECT_ROOT

        # Resolve the source file path
        if url_or_path.startswith("/api/outputs/"):
            filename = url_or_path.replace("/api/outputs/", "")
            src = os.path.join(PROJECT_ROOT, "references", "outputs", filename)
        elif os.path.isabs(url_or_path) and os.path.exists(url_or_path):
            src = url_or_path
        else:
            return  # External URL — can't copy locally

        if not os.path.exists(src):
            return

        ext = os.path.splitext(src)[1] or ".bin"
        dest = os.path.join(output_dir, f"{base_name}{ext}")
        try:
            shutil.copy2(src, dest)
            logger.debug("Copied asset → %s", dest)
        except Exception as exc:
            logger.warning("Failed to copy asset %s → %s: %s", src, dest, exc)

    @staticmethod
    def _save_run_metadata(output_dir, run_id, scenes, outputs, cost):
        """Write a metadata.json summarizing the run for easy browsing."""
        meta = {
            "run_id": run_id,
            "recipe": "ad_video_maker",
            "scenes": scenes,
            "total_cost": cost,
            "output_count": len([o for o in outputs if o.get("url") or o.get("image_url")]),
        }
        meta_path = os.path.join(output_dir, "metadata.json")
        try:
            with open(meta_path, "w") as f:
                json.dump(meta, f, indent=2, ensure_ascii=False)
        except Exception as exc:
            logger.warning("Failed to write run metadata: %s", exc)
