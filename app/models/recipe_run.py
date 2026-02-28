"""RecipeRun model — tracks every execution of a workflow recipe.

Stores the user inputs, step-by-step progress, outputs, cost, and errors
so the user can review past runs and the admin can see aggregate stats.
"""

import json
from datetime import datetime, timezone
from ..extensions import db


class RecipeRun(db.Model):
    __tablename__ = "recipe_runs"

    id = db.Column(db.Integer, primary_key=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey("recipes.id"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    brand_id = db.Column(db.Integer, db.ForeignKey("brands.id"), nullable=True, index=True)
    persona_id = db.Column(db.Integer, db.ForeignKey("user_personas.id"), nullable=True)

    # Status tracking
    status = db.Column(db.String(20), default="pending")  # pending, running, awaiting_approval, completed, failed, cancelled
    steps_completed = db.Column(db.Integer, default=0)
    total_steps = db.Column(db.Integer, default=1)
    current_step_label = db.Column(db.String(200))  # e.g. "Generating images (2 of 5)…"

    # Inputs & outputs (flexible JSON blobs)
    inputs_json = db.Column(db.Text, default="{}")  # What the user submitted
    outputs_json = db.Column(db.Text, default="[]")  # Result files / URLs / data
    error_message = db.Column(db.Text)

    # Cost tracking
    cost = db.Column(db.Float, default=0.0)  # Actual cost incurred
    retail_cost = db.Column(db.Float, default=0.0)  # Price shown to user

    # Model used (for pricing display & audit)
    model_used = db.Column(db.String(80))  # e.g. "veo-3.1", "nano-banana", "gpt-image-1"

    # Timestamps
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # --- JSON helpers ---

    @property
    def inputs(self):
        return json.loads(self.inputs_json) if self.inputs_json else {}

    @inputs.setter
    def inputs(self, value):
        self.inputs_json = json.dumps(value)

    @property
    def outputs(self):
        return json.loads(self.outputs_json) if self.outputs_json else []

    @outputs.setter
    def outputs(self, value):
        self.outputs_json = json.dumps(value)

    @property
    def progress_pct(self):
        """Return 0–100 progress percentage."""
        if self.total_steps <= 0:
            return 0
        return min(100, int((self.steps_completed / self.total_steps) * 100))

    def __repr__(self):
        return f"<RecipeRun {self.id} recipe={self.recipe_id} status={self.status}>"
