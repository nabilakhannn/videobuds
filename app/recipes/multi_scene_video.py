"""Multi-Scene Video — AI generates scenes and stitches them into one video.

Based on the R34 "VeoRobo 3 Scenes" n8n workflow.
"""

from .base import BaseRecipe, InputField


class MultiSceneVideo(BaseRecipe):
    slug = "multi-scene-video"
    name = "Multi-Scene Video"
    short_description = "Describe 3 scenes and AI creates a stitched video from them."
    description = (
        "Write a brief idea and the AI will plan 3 cinematic scenes, "
        "generate a video for each one, stitch them together, and give you "
        "a polished short-form video ready for social media."
    )
    category = "video_studio"
    icon = "🎞️"
    estimated_cost = "$0.15 – $0.60 per video"
    is_active = False  # Stub — not yet wired to backend

    how_to_use = """\
### How to use Multi-Scene Video

1. **Describe your idea** in a sentence or two (e.g. "A cozy café in Paris at sunrise").
2. *(Optional)* Write scene-by-scene prompts to have more control.
3. **Pick the aspect ratio** — vertical, horizontal, or square.
4. Click **Generate** — the AI plans 3 scenes, creates a video for each, and joins them.
5. Preview and download the final video.

**What happens behind the scenes:**
- Step 1: AI expands your idea into 3 detailed scene prompts
- Step 2: Each scene is generated as a short video clip
- Step 3: Clips are stitched together with smooth transitions
- Step 4: Final video is encoded and ready

**Tips:**
- Keep your idea focused on a single mood or story.
- For longer videos, run the recipe multiple times and combine.
"""

    def get_input_fields(self):
        return [
            InputField(
                name="idea",
                label="Video Idea",
                field_type="textarea",
                required=True,
                placeholder="e.g. A sneaker ad: street basketball → slow-mo dunk → shoes on display",
                help_text="A sentence describing the overall concept. The AI will plan scenes for you.",
            ),
            InputField(
                name="scene_1",
                label="Scene 1 (optional override)",
                field_type="textarea",
                required=False,
                placeholder="Leave blank for AI to decide",
            ),
            InputField(
                name="scene_2",
                label="Scene 2 (optional override)",
                field_type="textarea",
                required=False,
            ),
            InputField(
                name="scene_3",
                label="Scene 3 (optional override)",
                field_type="textarea",
                required=False,
            ),
            InputField(
                name="aspect_ratio",
                label="Aspect Ratio",
                field_type="select",
                default="9:16",
                options=[
                    {"value": "9:16", "label": "Vertical (9:16)"},
                    {"value": "16:9", "label": "Horizontal (16:9)"},
                    {"value": "1:1", "label": "Square (1:1)"},
                ],
            ),
        ]

    def get_steps(self):
        return [
            "Planning scenes",
            "Generating scene 1",
            "Generating scene 2",
            "Generating scene 3",
            "Stitching & encoding",
        ]

    def execute(self, inputs, run_id, user_id, on_progress=None,
                brand=None, persona=None):
        self.report_progress(on_progress, 0, "Planning scenes…")
        # TODO: Wire to tools/create_video.py with Veo 3 via Kie AI
        return {"outputs": [{"type": "text", "title": "Coming Soon", "value": "This recipe is under development and will be available soon. Stay tuned!"}], "cost": 0.0}
