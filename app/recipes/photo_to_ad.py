"""Photo to Ad — snap a product photo → get branded ad images + videos.

Two-phase architecture (mirrors Ad Video Maker):
  Phase 1 — SCRIPT  (Analyse product + write ad concepts)
    1. Multimodal Gemini call — AI *sees* the product photo
    2. Ad concept writing — one concept per requested variation,
       each with a scene description, ad copy, and optional tagline overlay
    3. Outputs saved → status set to ``awaiting_approval``

  Phase 2 — PRODUCTION  (after user approves / edits the concepts)
    4. Generate ad images for each approved concept
    5. (Optional) Turn images into short videos
    6. Organise all assets in ``references/outputs/run_<id>/``
"""

import json
import logging
import os
import shutil

from .base import BaseRecipe, InputField

logger = logging.getLogger(__name__)


class PhotoToAd(BaseRecipe):
    slug = "photo-to-ad"
    name = "Photo to Ad"
    short_description = "Snap a product photo — get branded ad images and videos instantly."
    description = (
        "Take a quick photo of your product (even from your phone), upload "
        "it, and the AI generates professional-looking ad images and short "
        "videos — styled to match your brand. No design skills needed."
    )
    category = "content_creation"
    icon = "📸"
    estimated_cost = "$0.00 – $0.30 per set"

    how_to_use = """\
### How to use Photo to Ad

1. **Upload a product photo** — even a casual phone snap works.
2. *(Optional)* **Add a tagline** — e.g. "Now in stores" or "Limited edition".
3. **Choose the output** — images only, video only, or both.
4. **Choose the number of variations** — 1, 3, or 5.
5. Click **Generate** — the AI will analyse your product and write ad concepts.
6. **Review the concepts** — edit scene descriptions, ad copy, or motion prompts.
7. Click **Approve & Generate** when you're happy.
8. Download your ready-to-post ad assets.

**What happens behind the scenes:**
- Step 1: AI **looks at** your photo (multimodal vision) and describes exactly
  what it sees — product type, colours, materials, shapes.
- Step 2: AI writes ad concepts anchored to the real product details.
- ⏸️ **You review & approve** before any media is generated.
- Step 3: Professional ad images are generated with the approved concepts.
- Step 4: Short video versions are created (if selected).
- Step 5: Everything is organised and ready for download.

**Tips:**
- Photos with a clean background work best.
- If you've set up a User Persona, your brand colours and tone are auto-applied.
- Great for quick Instagram stories and product launch teasers.
"""

    # ------------------------------------------------------------------
    # Input fields
    # ------------------------------------------------------------------

    def get_input_fields(self):
        return [
            InputField(
                name="product_photo",
                label="Product Photo",
                field_type="file",
                required=True,
                accept="image/*",
                help_text="Upload a photo of your product — phone quality is fine.",
            ),
            InputField(
                name="tagline",
                label="Tagline (optional)",
                field_type="text",
                required=False,
                placeholder="e.g. Now available! / Limited edition / Shop now",
                help_text="A short line of text to overlay on the ad.",
            ),
            InputField(
                name="output_type",
                label="What to Generate",
                field_type="select",
                default="both",
                options=[
                    {"value": "images", "label": "Ad images only"},
                    {"value": "videos", "label": "Ad videos only"},
                    {"value": "both", "label": "Both images + videos"},
                ],
            ),
            InputField(
                name="variations",
                label="Number of Variations",
                field_type="select",
                default="3",
                options=[
                    {"value": "1", "label": "1 variation"},
                    {"value": "3", "label": "3 variations"},
                    {"value": "5", "label": "5 variations"},
                ],
            ),
        ]

    def get_steps(self):
        return [
            "Analysing product photo",
            "Writing ad concepts",
            "Generating ad images",
            "Creating video versions",
            "Packaging assets",
        ]

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _call_gemini(prompt: str) -> str:
        from ..services.agent_service import _call_gemini
        return _call_gemini(prompt)

    @staticmethod
    def _call_gemini_vision(prompt: str, image_path: str) -> str:
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
        phase = inputs.get("_phase", "script")
        if phase == "production":
            return self._execute_production(inputs, run_id, user_id, on_progress,
                                            brand=brand, persona=persona)
        else:
            return self._execute_script(inputs, run_id, user_id, on_progress,
                                        brand=brand, persona=persona)

    # ------------------------------------------------------------------
    # Phase 1: SCRIPT (Analyse → Concept → Approval gate)
    # ------------------------------------------------------------------

    def _execute_script(self, inputs, run_id, user_id, on_progress=None,
                        brand=None, persona=None):
        product_photo = inputs.get("product_photo")
        variations = int(inputs.get("variations", "3"))
        tagline = inputs.get("tagline", "")
        output_type = inputs.get("output_type", "both")

        outputs = []

        # ── Step 0: ANALYSE — multimodal image analysis ───────────────
        self.report_progress(on_progress, 0, "Analysing your product photo with vision AI…")

        analysis_prompt = (
            "You are an expert creative director and product photographer with "
            "perfect visual acuity. LOOK CAREFULLY at this product photo and "
            "describe EXACTLY what you see.\n\n"
            "Your analysis MUST include:\n"
            "1. **Product Identity**: What EXACTLY is this product? Be very specific "
            "(e.g. 'wireless noise-cancelling earbuds', not just 'earbuds').\n"
            "2. **Physical Details**: Shape, materials, textures, finishes, and "
            "distinctive design features.\n"
            "3. **Colors**: List the EXACT colors visible in the product.\n"
            "4. **Brand Cues**: Any visible logos, text, packaging, or branding.\n"
            "5. **Visual Style**: Photography style and lighting of the source image.\n"
            "6. **Target Audience**: Based on the design, who would buy this?\n\n"
            "Be PRECISE and DETAILED. This analysis will be used to create ad images "
            "that MUST accurately represent THIS specific product. "
            "Do NOT invent features you cannot see.\n"
            "Output ONLY the analysis text."
        )

        try:
            if product_photo and os.path.exists(product_photo):
                image_analysis = self._call_gemini_vision(analysis_prompt, product_photo)
                logger.info("Photo to Ad: multimodal analysis succeeded for run %s", run_id)
            else:
                image_analysis = self._call_gemini(analysis_prompt)
        except Exception as exc:
            logger.warning("Photo to Ad: image analysis fallback – %s", exc)
            image_analysis = (
                "Unable to analyse the image. Using generic product description. "
                "Please review and edit the concepts below to match your product."
            )

        outputs.append({
            "label": "🔍 Product Analysis (Vision AI)",
            "type": "text",
            "value": image_analysis,
        })

        # ── Step 1: WRITE AD CONCEPTS ─────────────────────────────────
        self.report_progress(on_progress, 1, "Writing ad concepts…")

        include_video = output_type in ("videos", "both")

        concept_prompt = (
            f"You are writing exactly {variations} unique ad concept(s) for "
            f"professional product advertising images.\n\n"
            "═══ CRITICAL PRODUCT CONTEXT ═══\n"
            "The following is a DETAILED analysis of the ACTUAL product from its photo. "
            "Every ad concept you write MUST feature THIS SPECIFIC product — not a "
            "similar one, not a different category, not a generic item.\n\n"
            f"{image_analysis}\n\n"
            "═══ END PRODUCT CONTEXT ═══\n\n"
        )

        # Inject brand and persona context + creative directives
        brand_ctx = self.build_brand_context(brand)
        persona_ctx = self.build_persona_context(persona)
        if brand_ctx or persona_ctx:
            concept_prompt += brand_ctx + persona_ctx
            concept_prompt += (
                "Use the above brand and persona context to inform the tone, style, "
                "color palette, and target audience of the ad concepts.\n"
                "IMPORTANT: If brand colours are provided, use them as the primary, "
                "secondary, and tertiary colours in the ad. NEVER use random colours "
                "when brand colours are available.\n\n"
            )

        # Add universal creative quality directives
        concept_prompt += self.build_creative_directives(
            generation_type="image", style_hint=""
        ) + "\n"

        if tagline:
            concept_prompt += (
                f"The user wants this tagline incorporated into the ads:\n"
                f'"{tagline}"\n\n'
            )

        concept_prompt += (
            "For each ad concept provide:\n"
            '- "scene_description": A detailed image prompt (2-3 sentences). '
            "MUST show the EXACT product described above — mention its specific type, "
            "colors, materials, and distinctive features. Describe the setting, "
            "composition, lighting, and mood for a professional advertisement.\n"
            '- "ad_copy": A punchy advertising headline/caption (1-2 sentences) '
            "that highlights the product's real attributes.\n"
        )

        if include_video:
            concept_prompt += (
                '- "video_motion": A short video motion / camera movement prompt '
                "(1 sentence). Describe how the camera moves around the product.\n"
            )

        concept_prompt += (
            "\nRULES:\n"
            "- The product described in the analysis MUST be the central focus.\n"
            "- Do NOT introduce unrelated products or switch product categories.\n"
            "- Reference specific colors, materials, or features from the analysis.\n"
            "- Each concept should show the product in a different style/setting "
            "(e.g. studio, lifestyle, close-up, flat lay, in-use).\n"
            "- Make the ads visually striking and social-media-ready.\n\n"
            f"Output a JSON array of exactly {variations} object(s). Example:\n"
        )

        if include_video:
            concept_prompt += (
                '[{"scene_description":"...","ad_copy":"...","video_motion":"..."}]\n\n'
            )
        else:
            concept_prompt += (
                '[{"scene_description":"...","ad_copy":"..."}]\n\n'
            )

        concept_prompt += "Output ONLY the JSON array, no markdown fences, no explanation."

        try:
            raw_concepts = self._call_gemini(concept_prompt)
            concepts = json.loads(self._clean_json(raw_concepts))
            if not isinstance(concepts, list) or len(concepts) == 0:
                raise ValueError("Expected a non-empty JSON array of concepts")
        except Exception as exc:
            logger.error("Photo to Ad: concept generation failed – %s", exc)
            raise RuntimeError(f"Failed to generate ad concepts: {exc}") from exc

        concepts = concepts[:variations]

        # Add each concept as a scene output for the approval UI
        for idx, concept in enumerate(concepts):
            scene_out = {
                "label": f"Scene {idx + 1}",
                "type": "scene",
                "index": idx,
                "scene_description": concept.get("scene_description", ""),
                "ad_copy": concept.get("ad_copy", ""),
            }
            if include_video:
                scene_out["video_motion"] = concept.get("video_motion", "")
            else:
                scene_out["video_motion"] = ""
            outputs.append(scene_out)

        return {
            "phase": "script",
            "outputs": outputs,
            "cost": 0.0,
        }

    # ------------------------------------------------------------------
    # Phase 2: PRODUCTION (Generate images + optional videos)
    # ------------------------------------------------------------------

    def _execute_production(self, inputs, run_id, user_id, on_progress=None,
                            brand=None, persona=None):
        approved_scenes = inputs.get("_approved_scenes", [])
        product_photo = inputs.get("product_photo")
        output_type = inputs.get("output_type", "both")
        script_outputs = inputs.get("_script_outputs", [])

        if not approved_scenes:
            raise RuntimeError("No approved concepts to produce.")

        include_images = output_type in ("images", "both")
        include_videos = output_type in ("videos", "both")

        outputs = list(script_outputs)
        total_cost = 0.0

        output_dir = self._get_run_output_dir(run_id)

        # Copy the reference photo into the run folder
        if product_photo and os.path.exists(product_photo):
            ref_ext = os.path.splitext(product_photo)[1]
            ref_dest = os.path.join(output_dir, f"input_product{ref_ext}")
            try:
                shutil.copy2(product_photo, ref_dest)
            except Exception:
                pass

        # ── Step 2: Generate ad images ────────────────────────────────
        self.report_progress(
            on_progress, 2,
            f"Generating {len(approved_scenes)} ad image(s)…",
        )

        from tools.create_image import generate_ugc_image
        from tools.config import get_actual_cost as _actual_cost

        reference_paths = (
            [product_photo]
            if product_photo and os.path.exists(product_photo)
            else []
        )

        # Auto-inject brand photo library as additional reference
        brand_refs = self.get_brand_reference_paths(brand, purpose="product", limit=3)
        if brand_refs:
            reference_paths.extend(brand_refs)
            logger.info("Photo to Ad: added %d brand reference image(s)", len(brand_refs))

        reference_paths = reference_paths or None

        image_results = []
        for idx, scene in enumerate(approved_scenes):
            self.report_progress(
                on_progress, 2,
                f"Generating ad image {idx + 1} of {len(approved_scenes)}…",
            )
            img_prompt = scene.get("scene_description", "A product advertisement")

            try:
                result = generate_ugc_image(
                    prompt=img_prompt,
                    reference_paths=reference_paths,
                    aspect_ratio="1:1",       # Square ads are most versatile
                    resolution="1K",
                    model="nano-banana-pro",
                    provider="google",
                )
                image_results.append(result)
                total_cost += _actual_cost("nano-banana-pro", "google")

                self._copy_asset_to_run_dir(
                    result.get("result_url"), output_dir,
                    f"ad_{idx + 1}_image",
                )
            except Exception as exc:
                logger.error("Photo to Ad: image %d failed – %s", idx + 1, exc)
                image_results.append({
                    "status": "error",
                    "error": str(exc),
                    "result_url": None,
                })

        # ── Step 3: Create video versions (if requested) ──────────────
        video_results = []
        if include_videos:
            self.report_progress(
                on_progress, 3,
                f"Creating {len(approved_scenes)} video(s)…",
            )

            from tools.create_video import generate_ugc_video

            for idx, (scene, img_res) in enumerate(
                zip(approved_scenes, image_results)
            ):
                self.report_progress(
                    on_progress, 3,
                    f"Creating video {idx + 1} of {len(approved_scenes)}…",
                )

                source_url = (
                    img_res.get("result_url")
                    if img_res.get("status") != "error"
                    else None
                )
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
                        aspect_ratio="9:16",
                        provider="google",
                    )
                    video_results.append(result)
                    total_cost += _actual_cost("veo-3.1", "google")

                    self._copy_asset_to_run_dir(
                        result.get("result_url"), output_dir,
                        f"ad_{idx + 1}_video",
                    )
                except Exception as exc:
                    logger.error("Photo to Ad: video %d failed – %s", idx + 1, exc)
                    video_results.append({
                        "status": "error",
                        "error": str(exc),
                        "result_url": None,
                    })
        else:
            self.report_progress(on_progress, 3, "Skipping videos (images only)…")
            video_results = [{"status": "skipped"}] * len(approved_scenes)

        # ── Step 4: Organise & finalise ───────────────────────────────
        self.report_progress(on_progress, 4, "Packaging assets…")

        for idx, scene in enumerate(approved_scenes):
            ad_copy = scene.get("ad_copy", f"Ad {idx + 1}")
            label = f"📸 Ad {idx + 1}: {ad_copy[:60]}"

            img_res = image_results[idx] if idx < len(image_results) else {}
            vid_res = video_results[idx] if idx < len(video_results) else {}

            entry = {"label": label, "scene": scene}

            # Attach image
            if img_res.get("result_url"):
                entry["image_url"] = img_res["result_url"]

            # Attach video (if generated)
            if vid_res.get("result_url"):
                entry["url"] = vid_res["result_url"]
                entry["type"] = "video"
            elif vid_res.get("status") == "error":
                entry["value"] = f"Video generation error: {vid_res.get('error', 'Unknown')}"
            elif include_images and not include_videos:
                # Image-only mode: primary output is the image
                if img_res.get("result_url"):
                    entry["url"] = img_res["result_url"]
                    entry["type"] = "image"
            elif img_res.get("result_url") and not vid_res.get("result_url"):
                # Had an image but video was skipped
                entry["url"] = img_res["result_url"]
                entry["type"] = "image"

            outputs.append(entry)

        # Save metadata
        self._save_run_metadata(output_dir, run_id, approved_scenes, outputs, total_cost)

        return {"outputs": outputs, "cost": total_cost}

    # ------------------------------------------------------------------
    # Asset organization helpers
    # ------------------------------------------------------------------

    def _copy_asset_to_run_dir(self, url_or_path, output_dir, base_name):
        if not url_or_path:
            return

        from tools.config import PROJECT_ROOT

        if url_or_path.startswith("/api/outputs/"):
            filename = url_or_path.replace("/api/outputs/", "")
            src = os.path.join(PROJECT_ROOT, "references", "outputs", filename)
        elif os.path.isabs(url_or_path) and os.path.exists(url_or_path):
            src = url_or_path
        else:
            return

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
        meta = {
            "run_id": run_id,
            "recipe": "photo_to_ad",
            "scenes": scenes,
            "total_cost": cost,
            "output_count": len([
                o for o in outputs
                if o.get("url") or o.get("image_url")
            ]),
        }
        meta_path = os.path.join(output_dir, "metadata.json")
        try:
            with open(meta_path, "w") as f:
                json.dump(meta, f, indent=2, ensure_ascii=False)
        except Exception as exc:
            logger.warning("Failed to write run metadata: %s", exc)
