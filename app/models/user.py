from datetime import datetime, timezone
import bcrypt
from app.extensions import db


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32), unique=True, nullable=False, index=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128), nullable=False)
    display_name = db.Column(db.String(80), nullable=False)
    avatar_url = db.Column(db.String(500))
    is_online = db.Column(db.Boolean, nullable=False, default=False, index=True)
    last_seen_at = db.Column(db.DateTime(timezone=True))
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    rooms_created = db.relationship("Room", back_populates="creator", foreign_keys="Room.created_by")
    memberships = db.relationship("Membership", back_populates="user", cascade="all, delete-orphan")
    messages = db.relationship("Message", back_populates="author", cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    def check_password(self, password):
        return bcrypt.checkpw(password.encode(), self.password_hash.encode())

