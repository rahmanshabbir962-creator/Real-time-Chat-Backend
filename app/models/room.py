from datetime import datetime, timezone
from app.extensions import db


class Room(db.Model):
    __tablename__ = "rooms"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, index=True)
    description = db.Column(db.String(500))
    is_private = db.Column(db.Boolean, nullable=False, default=False, index=True)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    creator = db.relationship("User", back_populates="rooms_created", foreign_keys=[created_by])
    memberships = db.relationship("Membership", back_populates="room", cascade="all, delete-orphan")
    messages = db.relationship("Message", back_populates="room", cascade="all, delete-orphan", order_by="Message.created_at")

