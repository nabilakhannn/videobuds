"""Motion Capture — animate a still photo using a driving video.

Based on the R47 "AI Motion Capture System" n8n workflow (video only).
"""

from .base import BaseRecipe, InputField


class MotionCapture(BaseRecipe):
    slug = "motion-capture"
    name = "Motion Capture"
    short_description = "Make a still photo move by copying motion from another video."
    description = (
        "Upload a still image (a person, character, or avatar) and a "
        "driving video (someone talking, dancing, or gesturing). The AI "
        "transfers the motion from the video onto your still image — "
        "making it look like the photo is alive and moving."
    )
    category = "video_studio"
    icon = "🕺"
    estimated_cost = "$0.10 – $0.40 per video"
    is_active = False  # Stub — not yet wired to backend

    how_to_use = """\
### How to use Motion Capture

1. **Upload a still image** — a headshot, character, or avatar.
2. **Upload a driving video** — a clip of someone moving, talking, or dancing.
3. Click **Generate**.
4. The AI maps the motion from the video onto your still image.
5. Download your animated video.

**What happens behind the scenes:**
- Step 1: AI detects facial landmarks and body pose in the driving video
- Step 2: Motion keypoints are mapped onto your still image
- Step 3: Each frame is rendered with the transferred motion
- Step 4: Final video is assembled with smooth animation

**Tips:**
- Use a front-facing, well-lit photo for best results.
- The driving video should be stable (avoid shaky footage).
- Keep the driving video under 15 seconds for faster processing.
"""

    def get_input_fields(self):
        return [
            InputField(
                name="still_image",
                label="Still Image",
                field_type="file",
                required=True,
                accept="image/*",
                help_text="The character or person you want to animate.",
            ),
            InputField(
                name="driving_video",
                label="Driving Video",
                field_type="file",
                required=True,
                accept="video/*",
                help_text="A video showing the motion you want to transfer.",
            ),
        ]

    def get_steps(self):
        return [
            "Analysing driving video",
            "Detecting motion keypoints",
            "Rendering animation",
            "Encoding output",
        ]

    def execute(self, inputs, run_id, user_id, on_progress=None,
                brand=None, persona=None):
        self.report_progress(on_progress, 0, "Analysing driving video…")
        # TODO: Wire to motion capture pipeline (WaveSpeed)
        return {"outputs": [{"type": "text", "title": "Coming Soon", "value": "This recipe is under development and will be available soon. Stay tuned!"}], "cost": 0.0}
