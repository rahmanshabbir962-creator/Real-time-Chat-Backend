from datetime import datetime, timezone
from app.extensions import db


class Membership(db.Model):
    __tablename__ = "memberships"
    __table_args__ = (db.UniqueConstraint("user_id", "room_id", name="uq_membership_user_room"),)
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    room_id = db.Column(db.Integer, db.ForeignKey("rooms.id", ondelete="CASCADE"), nullable=False, index=True)
    role = db.Column(db.String(20), nullable=False, default="member")
    last_read_message_id = db.Column(db.Integer, db.ForeignKey("messages.id", use_alter=True, name="fk_membership_last_read"))
    joined_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    user = db.relationship("User", back_populates="memberships")
    room = db.relationship("Room", back_populates="memberships")

