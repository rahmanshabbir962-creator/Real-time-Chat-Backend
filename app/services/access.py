from flask import abort
from app.extensions import db
from app.models.membership import Membership
from app.models.room import Room


def get_room_or_404(room_id):
    room = db.session.get(Room, room_id)
    if not room:
        abort(404, description="Room not found")
    return room


def membership_or_403(user_id, room_id):
    membership = Membership.query.filter_by(user_id=user_id, room_id=room_id).first()
    if not membership:
        abort(403, description="You are not a member of this room")
    return membership


def room_visible_to(user_id, room):
    return not room.is_private or Membership.query.filter_by(user_id=user_id, room_id=room.id).first() is not None
