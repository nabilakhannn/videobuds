"""Reference image model for mood boards and style references."""

from datetime import datetime, timezone
from ..extensions import db


class ReferenceImage(db.Model):
    __tablename__ = "reference_images"

    id = db.Column(db.Integer, primary_key=True)
    brand_id = db.Column(db.Integer, db.ForeignKey("brands.id"), index=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey("campaigns.id"), index=True)
    file_path = db.Column(db.String(500), nullable=False)
    hosted_url = db.Column(db.String(500))
    purpose = db.Column(db.String(50), default="mood")  # mood, product, style_reference
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
