"""Vertical Reframe — convert horizontal video to vertical (9:16).

Based on the R33 "AI Vertical Reframe System" n8n workflow.
"""

from .base import BaseRecipe, InputField


class VerticalReframe(BaseRecipe):
    slug = "vertical-reframe"
    name = "Vertical Reframe"
    short_description = "Convert any horizontal video to vertical for Reels, TikTok & Shorts."
    description = (
        "Got a horizontal (16:9) video and need it for TikTok or Reels? "
        "Upload it here and the AI will intelligently reframe it to vertical "
        "(9:16) — keeping the main subject in focus, cropping smartly, and "
        "maintaining the original audio."
    )
    category = "repurpose"
    icon = "📱"
    estimated_cost = "$0.05 – $0.15 per video"
    is_active = False  # Stub — not yet wired to backend

    how_to_use = """\
### How to use Vertical Reframe

1. **Upload your horizontal video** (16:9 or wider).
2. **Select the output format** — 9:16 (full vertical) or 4:5 (Instagram feed).
3. Click **Generate**.
4. Preview the reframed video and download it.

**What happens behind the scenes:**
- Step 1: AI detects the main subject (speaker, product, text)
- Step 2: Smart-crops each frame to keep the subject centred
- Step 3: Outputs a clean vertical video with original audio

**Tips:**
- Works best with talking-head or product demo videos.
- Avoid videos with lots of text at the edges — the crop may cut it off.
"""

    def get_input_fields(self):
        return [
            InputField(
                name="video_file",
                label="Horizontal Video",
                field_type="file",
                required=True,
                accept="video/*",
                help_text="Upload a 16:9 or wider video file.",
            ),
            InputField(
                name="output_ratio",
                label="Output Format",
                field_type="select",
                default="9:16",
                options=[
                    {"value": "9:16", "label": "9:16 — TikTok / Reels / Shorts"},
                    {"value": "4:5", "label": "4:5 — Instagram Feed"},
                ],
            ),
        ]

    def get_steps(self):
        return [
            "Detecting main subject",
            "Computing smart crop",
            "Reframing video",
            "Encoding output",
        ]

    def execute(self, inputs, run_id, user_id, on_progress=None,
                brand=None, persona=None):
        self.report_progress(on_progress, 0, "Detecting main subject…")
        # TODO: Wire to video reframe pipeline
        return {"outputs": [{"type": "text", "title": "Coming Soon", "value": "This recipe is under development and will be available soon. Stay tuned!"}], "cost": 0.0}
