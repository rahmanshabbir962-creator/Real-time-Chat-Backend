from datetime import datetime, timezone
from flask import request
from flask_socketio import emit, join_room, leave_room
from marshmallow import ValidationError
from app.extensions import db, socketio
from app.models.message import Message
from app.schemas.message import MessageCreateSchema, MessageUpdateSchema
from app.services.access import membership_or_403
from app.sockets.status import current_socket_user
from app.utils.serializers import message_data


def socket_error(message):
    emit("error", {"message": message})


@socketio.on("join_room")
def join_chat_room(data):
    user = current_socket_user(); room_id = (data or {}).get("room_id")
    if not user or not isinstance(room_id, int): return socket_error("Authentication and room_id are required")
    try: membership_or_403(user.id, room_id)
    except Exception: return socket_error("You are not a member of this room")
    join_room(f"room:{room_id}")
    emit("room_joined", {"room_id": room_id})
    emit("member_joined", {"room_id": room_id, "user_id": user.id}, to=f"room:{room_id}", include_self=False)


@socketio.on("leave_room")
def leave_chat_room(data):
    user = current_socket_user(); room_id = (data or {}).get("room_id")
    if not user or not isinstance(room_id, int): return socket_error("Authentication and room_id are required")
    leave_room(f"room:{room_id}")
    emit("member_left", {"room_id": room_id, "user_id": user.id}, to=f"room:{room_id}")


@socketio.on("send_message")
def send_message(data):
    user = current_socket_user(); room_id = (data or {}).get("room_id")
    if not user or not isinstance(room_id, int): return socket_error("Authentication and room_id are required")
    try:
        membership_or_403(user.id, room_id); payload = MessageCreateSchema().load(data)
    except (ValidationError, Exception) as exc:
        return socket_error(getattr(exc, "messages", "Invalid message or room access"))
    message = Message(room_id=room_id, author_id=user.id, content=payload["content"]); db.session.add(message); db.session.commit()
    emit("new_message", {"message": message_data(message)}, to=f"room:{room_id}")


@socketio.on("edit_message")
def edit_socket_message(data):
    user = current_socket_user(); message = db.session.get(Message, (data or {}).get("message_id"))
    if not user or not message or message.author_id != user.id or message.deleted_at: return socket_error("Message cannot be edited")
    try: message.content = MessageUpdateSchema().load(data)["content"]
    except ValidationError as exc: return socket_error(exc.messages)
    message.edited_at = datetime.now(timezone.utc); db.session.commit()
    emit("message_updated", {"message": message_data(message)}, to=f"room:{message.room_id}")


@socketio.on("delete_message")
def delete_socket_message(data):
    user = current_socket_user(); message = db.session.get(Message, (data or {}).get("message_id"))
    if not user or not message or message.author_id != user.id: return socket_error("Message cannot be deleted")
    message.deleted_at = datetime.now(timezone.utc); db.session.commit()
    emit("message_deleted", {"message_id": message.id, "room_id": message.room_id}, to=f"room:{message.room_id}")


@socketio.on("mark_read")
def mark_read(data):
    user = current_socket_user(); message = db.session.get(Message, (data or {}).get("message_id"))
    if not user or not message: return socket_error("Message not found")
    try: membership = membership_or_403(user.id, message.room_id)
    except Exception: return socket_error("You are not a member of this room")
    membership.last_read_message_id = message.id; db.session.commit()
    emit("message_read", {"room_id": message.room_id, "message_id": message.id, "user_id": user.id}, to=f"room:{message.room_id}")

