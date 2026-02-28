"""Generation model for tracking image generation jobs and costs."""

from datetime import datetime, timezone
from ..extensions import db


class Generation(db.Model):
    __tablename__ = "generations"

    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey("posts.id"), index=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey("campaigns.id"), index=True)
    brand_id = db.Column(db.Integer, db.ForeignKey("brands.id"), index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    prompt = db.Column(db.Text, nullable=False)
    model = db.Column(db.String(50), nullable=False, default="nano-banana")
    provider = db.Column(db.String(50), nullable=False, default="google")
    aspect_ratio = db.Column(db.String(10), default="9:16")
    status = db.Column(db.String(20), default="pending")  # pending, processing, success, error
    result_url = db.Column(db.String(500))
    local_path = db.Column(db.String(500))
    error_message = db.Column(db.Text)
    cost = db.Column(db.Float, default=0.0)  # actual cost incurred
    retail_cost = db.Column(db.Float, default=0.0)  # retail price shown to users
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
