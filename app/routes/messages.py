from datetime import datetime, timezone
from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from app.extensions import db, socketio
from app.models.message import Message
from app.schemas.message import MessageCreateSchema, MessageUpdateSchema
from app.services.access import membership_or_403
from app.utils.serializers import message_data

messages_bp = Blueprint("messages", __name__)


@messages_bp.get("/rooms/<int:room_id>")
@jwt_required()
def history(room_id):
    membership_or_403(int(get_jwt_identity()), room_id)
    page = max(1, request.args.get("page", 1, type=int)); per_page = min(100, max(1, request.args.get("per_page", 50, type=int)))
    result = Message.query.filter_by(room_id=room_id).order_by(Message.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return {"messages": [message_data(m) for m in reversed(result.items)], "pagination": {"page": page, "per_page": per_page, "pages": result.pages, "total": result.total}}


@messages_bp.post("/rooms/<int:room_id>")
@jwt_required()
def create_message(room_id):
    user_id = int(get_jwt_identity()); membership_or_403(user_id, room_id)
    message = Message(room_id=room_id, author_id=user_id, **MessageCreateSchema().load(request.get_json() or {}))
    db.session.add(message); db.session.commit()
    payload = message_data(message); socketio.emit("new_message", {"message": payload}, to=f"room:{room_id}")
    return {"message": payload}, 201


@messages_bp.patch("/<int:message_id>")
@jwt_required()
def edit_message(message_id):
    message = db.session.get(Message, message_id)
    if not message: return {"error": "not_found", "message": "Message not found"}, 404
    if message.author_id != int(get_jwt_identity()) or message.deleted_at: return {"error": "forbidden", "message": "Message cannot be edited"}, 403
    message.content = MessageUpdateSchema().load(request.get_json() or {})["content"]; message.edited_at = datetime.now(timezone.utc); db.session.commit()
    payload = message_data(message); socketio.emit("message_updated", {"message": payload}, to=f"room:{message.room_id}")
    return {"message": payload}


@messages_bp.delete("/<int:message_id>")
@jwt_required()
def delete_message(message_id):
    message = db.session.get(Message, message_id)
    if not message: return {"error": "not_found", "message": "Message not found"}, 404
    if message.author_id != int(get_jwt_identity()): return {"error": "forbidden", "message": "Only the author can delete this message"}, 403
    message.deleted_at = datetime.now(timezone.utc); db.session.commit(); socketio.emit("message_deleted", {"message_id": message_id, "room_id": message.room_id}, to=f"room:{message.room_id}")
    return "", 204


@messages_bp.post("/<int:message_id>/read")
@jwt_required()
def read_message(message_id):
    message = db.session.get(Message, message_id)
    if not message: return {"error": "not_found", "message": "Message not found"}, 404
    membership = membership_or_403(int(get_jwt_identity()), message.room_id)
    membership.last_read_message_id = message.id; db.session.commit()
    socketio.emit("message_read", {"room_id": message.room_id, "message_id": message.id, "user_id": membership.user_id}, to=f"room:{message.room_id}")
    return {"message": "Read receipt recorded"}
