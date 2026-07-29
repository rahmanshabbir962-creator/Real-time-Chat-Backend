from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from app.extensions import db
from app.models.user import User
from app.utils.serializers import user_data

users_bp = Blueprint("users", __name__)


@users_bp.get("/me")
@jwt_required()
def me():
    return {"user": user_data(db.session.get(User, int(get_jwt_identity())))}


@users_bp.patch("/me")
@jwt_required()
def update_me():
    user = db.session.get(User, int(get_jwt_identity()))
    data = request.get_json() or {}
    allowed = {"display_name", "avatar_url"}
    unexpected = set(data) - allowed
    if unexpected:
        return {"error": "validation_error", "message": "Unsupported profile fields"}, 422
    if "display_name" in data and not isinstance(data["display_name"], str):
        return {"error": "validation_error", "message": "display_name must be text"}, 422
    user.display_name = data.get("display_name", user.display_name)[:80]
    user.avatar_url = data.get("avatar_url", user.avatar_url)
    db.session.commit()
    return {"user": user_data(user)}


@users_bp.get("/search")
@jwt_required()
def search():
    query = request.args.get("q", "").strip()
    if len(query) < 2:
        return {"error": "validation_error", "message": "q must contain at least 2 characters"}, 422
    users = User.query.filter((User.username.ilike(f"%{query}%")) | (User.display_name.ilike(f"%{query}%"))).limit(30).all()
    return {"users": [user_data(user) for user in users]}
