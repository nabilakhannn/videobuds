"""Recipe model — database record for each workflow recipe.

Recipe *definitions* live in Python (app/recipes/), but this DB record lets
admins enable/disable recipes and tracks aggregate usage stats. The `slug`
column is the join key between the Python class and the database row.
"""

from datetime import datetime, timezone
from ..extensions import db


# Valid categories for recipes
RECIPE_CATEGORIES = [
    "content_creation",
    "video_studio",
    "repurpose",
    "research",
    "distribution",
]


class Recipe(db.Model):
    __tablename__ = "recipes"

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(80), unique=True, nullable=False, index=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(40), default="content_creation")
    icon = db.Column(db.String(10), default="🧪")  # Emoji or short icon code
    is_enabled = db.Column(db.Boolean, default=True)
    usage_count = db.Column(db.Integer, default=0)
    estimated_cost_label = db.Column(db.String(60))  # e.g. "$0.05 – $0.30 per run"
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    runs = db.relationship("RecipeRun", backref="recipe", lazy="dynamic")

    def __repr__(self):
        return f"<Recipe {self.slug} enabled={self.is_enabled}>"
