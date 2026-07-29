"""initial chat schema

Revision ID: 0001_initial
Revises:
"""
from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("users", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("username", sa.String(32), nullable=False), sa.Column("email", sa.String(255), nullable=False), sa.Column("password_hash", sa.String(128), nullable=False), sa.Column("display_name", sa.String(80), nullable=False), sa.Column("avatar_url", sa.String(500)), sa.Column("is_online", sa.Boolean(), nullable=False), sa.Column("last_seen_at", sa.DateTime(timezone=True)), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_users_username", "users", ["username"], unique=True); op.create_index("ix_users_email", "users", ["email"], unique=True); op.create_index("ix_users_is_online", "users", ["is_online"])
    op.create_table("rooms", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("name", sa.String(100), nullable=False), sa.Column("description", sa.String(500)), sa.Column("is_private", sa.Boolean(), nullable=False), sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_rooms_name", "rooms", ["name"]); op.create_index("ix_rooms_is_private", "rooms", ["is_private"]); op.create_index("ix_rooms_created_by", "rooms", ["created_by"]); op.create_index("ix_rooms_created_at", "rooms", ["created_at"])
    op.create_table("messages", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("room_id", sa.Integer(), sa.ForeignKey("rooms.id", ondelete="CASCADE"), nullable=False), sa.Column("author_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False), sa.Column("content", sa.Text(), nullable=False), sa.Column("edited_at", sa.DateTime(timezone=True)), sa.Column("deleted_at", sa.DateTime(timezone=True)), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_messages_room_id", "messages", ["room_id"]); op.create_index("ix_messages_author_id", "messages", ["author_id"]); op.create_index("ix_messages_created_at", "messages", ["created_at"]); op.create_index("ix_messages_deleted_at", "messages", ["deleted_at"]); op.create_index("ix_messages_room_created", "messages", ["room_id", "created_at"])
    op.create_table("memberships", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False), sa.Column("room_id", sa.Integer(), sa.ForeignKey("rooms.id", ondelete="CASCADE"), nullable=False), sa.Column("role", sa.String(20), nullable=False), sa.Column("last_read_message_id", sa.Integer(), sa.ForeignKey("messages.id")), sa.Column("joined_at", sa.DateTime(timezone=True), nullable=False), sa.UniqueConstraint("user_id", "room_id", name="uq_membership_user_room"))
    op.create_index("ix_memberships_user_id", "memberships", ["user_id"]); op.create_index("ix_memberships_room_id", "memberships", ["room_id"])
    op.create_table("token_blocklist", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("jti", sa.String(36), nullable=False), sa.Column("token_type", sa.String(10), nullable=False), sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_token_blocklist_jti", "token_blocklist", ["jti"], unique=True); op.create_index("ix_token_blocklist_expires_at", "token_blocklist", ["expires_at"])


def downgrade():
    op.drop_table("token_blocklist"); op.drop_table("memberships"); op.drop_table("messages"); op.drop_table("rooms"); op.drop_table("users")
