from flask_socketio import emit
from app.extensions import socketio
from app.services.access import membership_or_403
from app.sockets.status import current_socket_user


@socketio.on("typing")
def typing(data):
    user = current_socket_user(); room_id = (data or {}).get("room_id"); is_typing = (data or {}).get("is_typing", False)
    if not user or not isinstance(room_id, int): return
    try: membership_or_403(user.id, room_id)
    except Exception: return
    emit("typing", {"room_id": room_id, "user_id": user.id, "is_typing": bool(is_typing)}, to=f"room:{room_id}", include_self=False)
