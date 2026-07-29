from datetime import datetime, timezone
from app.extensions import db


class Message(db.Model):
    __tablename__ = "messages"
    __table_args__ = (db.Index("ix_messages_room_created", "room_id", "created_at"),)
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey("rooms.id", ondelete="CASCADE"), nullable=False, index=True)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    content = db.Column(db.Text, nullable=False)
    edited_at = db.Column(db.DateTime(timezone=True))
    deleted_at = db.Column(db.DateTime(timezone=True), index=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), index=True)
    room = db.relationship("Room", back_populates="messages")
    author = db.relationship("User", back_populates="messages")
