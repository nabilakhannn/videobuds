"""Brand questionnaire model for storing interview responses."""

from datetime import datetime, timezone
from ..extensions import db


class BrandQuestionnaire(db.Model):
    __tablename__ = "brand_questionnaires"

    id = db.Column(db.Integer, primary_key=True)
    brand_id = db.Column(db.Integer, db.ForeignKey("brands.id"), nullable=False, index=True)
    question_key = db.Column(db.String(100), nullable=False)
    answer = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
