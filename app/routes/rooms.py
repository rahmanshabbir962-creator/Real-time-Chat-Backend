from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from app.extensions import db, socketio
from app.models.membership import Membership
from app.models.room import Room
from app.schemas.room import RoomCreateSchema, RoomUpdateSchema
from app.services.access import get_room_or_404, membership_or_403
from app.utils.serializers import room_data

rooms_bp = Blueprint("rooms", __name__)


@rooms_bp.get("")
@jwt_required()
def list_rooms():
    user_id = int(get_jwt_identity())
    page = max(1, request.args.get("page", 1, type=int)); per_page = min(100, max(1, request.args.get("per_page", 20, type=int)))
    scope = request.args.get("scope", "joined")
    query = Room.query
    if scope == "public": query = query.filter_by(is_private=False)
    elif scope == "joined": query = query.join(Membership).filter(Membership.user_id == user_id)
    else: return {"error": "validation_error", "message": "scope must be joined or public"}, 422
    result = query.order_by(Room.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return {"rooms": [room_data(r) for r in result.items], "pagination": {"page": page, "per_page": per_page, "pages": result.pages, "total": result.total}}


@rooms_bp.post("")
@jwt_required()
def create_room():
    user_id = int(get_jwt_identity()); data = RoomCreateSchema().load(request.get_json() or {})
    room = Room(**data, created_by=user_id)
    db.session.add(room); db.session.flush()
    db.session.add(Membership(user_id=user_id, room_id=room.id, role="owner")); db.session.commit()
    return {"room": room_data(room, True)}, 201


@rooms_bp.get("/<int:room_id>")
@jwt_required()
def get_room(room_id):
    membership_or_403(int(get_jwt_identity()), room_id)
    return {"room": room_data(get_room_or_404(room_id), True)}


@rooms_bp.patch("/<int:room_id>")
@jwt_required()
def update_room(room_id):
    user_id = int(get_jwt_identity()); membership = membership_or_403(user_id, room_id)
    if membership.role not in ("owner", "admin"): return {"error": "forbidden", "message": "Admin role required"}, 403
    room = get_room_or_404(room_id); data = RoomUpdateSchema().load(request.get_json() or {})
    for field, value in data.items(): setattr(room, field, value)
    db.session.commit(); socketio.emit("room_updated", {"room": room_data(room)}, to=f"room:{room.id}")
    return {"room": room_data(room, True)}


@rooms_bp.delete("/<int:room_id>")
@jwt_required()
def delete_room(room_id):
    room = get_room_or_404(room_id)
    if room.created_by != int(get_jwt_identity()): return {"error": "forbidden", "message": "Only the owner can delete a room"}, 403
    db.session.delete(room); db.session.commit(); socketio.emit("room_deleted", {"room_id": room_id}, to=f"room:{room_id}")
    return "", 204


@rooms_bp.post("/<int:room_id>/join")
@jwt_required()
def join_room(room_id):
    user_id = int(get_jwt_identity()); room = get_room_or_404(room_id)
    if room.is_private: return {"error": "forbidden", "message": "Private rooms require an invitation"}, 403
    membership = Membership.query.filter_by(user_id=user_id, room_id=room_id).first()
    if not membership:
        membership = Membership(user_id=user_id, room_id=room_id); db.session.add(membership); db.session.commit()
    return {"room": room_data(room, True)}, 200


@rooms_bp.post("/<int:room_id>/members")
@jwt_required()
def add_member(room_id):
    actor = membership_or_403(int(get_jwt_identity()), room_id)
    if actor.role not in ("owner", "admin"): return {"error": "forbidden", "message": "Admin role required"}, 403
    user_id = (request.get_json() or {}).get("user_id")
    if not isinstance(user_id, int): return {"error": "validation_error", "message": "user_id is required"}, 422
    if not db.session.get(__import__('app.models.user', fromlist=['User']).User, user_id): return {"error": "not_found", "message": "User not found"}, 404
    membership = Membership.query.filter_by(user_id=user_id, room_id=room_id).first()
    if not membership: db.session.add(Membership(user_id=user_id, room_id=room_id)); db.session.commit()
    return {"message": "Member added"}, 201


@rooms_bp.delete("/<int:room_id>/leave")
@jwt_required()
def leave_room(room_id):
    user_id = int(get_jwt_identity()); membership = membership_or_403(user_id, room_id)
    if membership.role == "owner": return {"error": "validation_error", "message": "Transfer ownership or delete the room first"}, 422
    db.session.delete(membership); db.session.commit(); socketio.emit("member_left", {"room_id": room_id, "user_id": user_id}, to=f"room:{room_id}")
    return "", 204

