from datetime import datetime, timezone
from flask import request
from flask_jwt_extended import decode_token
from flask_socketio import emit
from app.extensions import db, socketio
from app.models.user import User

connected_users = {}  # user_id -> set of Socket.IO session IDs, local process only
sid_users = {}


def current_socket_user():
    user_id = sid_users.get(request.sid)
    return db.session.get(User, user_id) if user_id else None


@socketio.on("connect")
def connect(auth):
    token = (auth or {}).get("token")
    if not token:
        return False
    try:
        payload = decode_token(token)
        if payload["type"] != "access": return False
        user = db.session.get(User, int(payload["sub"]))
    except Exception:
        return False
    if not user: return False
    sid_users[request.sid] = user.id
    sids = connected_users.setdefault(user.id, set()); was_offline = not sids; sids.add(request.sid)
    if was_offline:
        user.is_online = True; db.session.commit()
        socketio.emit("user_status", {"user_id": user.id, "is_online": True, "last_seen_at": None})
    emit("connected", {"user_id": user.id})


@socketio.on("disconnect")
def disconnect():
    user_id = sid_users.pop(request.sid, None)
    if not user_id: return
    sids = connected_users.get(user_id, set()); sids.discard(request.sid)
    if not sids:
        connected_users.pop(user_id, None)
        user = db.session.get(User, user_id)
        if user:
            user.is_online = False; user.last_seen_at = datetime.now(timezone.utc); db.session.commit()
            socketio.emit("user_status", {"user_id": user.id, "is_online": False, "last_seen_at": user.last_seen_at.isoformat()})

