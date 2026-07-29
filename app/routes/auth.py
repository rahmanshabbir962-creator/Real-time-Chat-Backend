from datetime import datetime, timezone
from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, create_refresh_token, get_jwt, get_jwt_identity, jwt_required
from app.extensions import db
from app.models.user import User
from app.models.token_blocklist import TokenBlocklist
from app.schemas.auth import LoginSchema, SignupSchema
from app.utils.serializers import user_data

auth_bp = Blueprint("auth", __name__)


@auth_bp.post("/signup")
def signup():
    data = SignupSchema().load(request.get_json() or {})
    if User.query.filter((User.email == data["email"].lower()) | (User.username == data["username"])).first():
        return {"error": "conflict", "message": "Email or username is already in use"}, 409
    user = User(username=data["username"], email=data["email"].lower(), display_name=data["display_name"])
    user.set_password(data["password"])
    db.session.add(user); db.session.commit()
    return jsonify({"user": user_data(user), "access_token": create_access_token(str(user.id)), "refresh_token": create_refresh_token(str(user.id))}), 201


@auth_bp.post("/login")
def login():
    data = LoginSchema().load(request.get_json() or {})
    user = User.query.filter_by(email=data["email"].lower()).first()
    if not user or not user.check_password(data["password"]):
        return {"error": "invalid_credentials", "message": "Invalid email or password"}, 401
    return jsonify({"user": user_data(user), "access_token": create_access_token(str(user.id)), "refresh_token": create_refresh_token(str(user.id))})


@auth_bp.post("/refresh")
@jwt_required(refresh=True)
def refresh():
    return {"access_token": create_access_token(get_jwt_identity())}


@auth_bp.post("/logout")
@jwt_required(verify_type=False)
def logout():
    token = get_jwt()
    db.session.add(TokenBlocklist(jti=token["jti"], token_type=token["type"], expires_at=datetime.fromtimestamp(token["exp"], timezone.utc)))
    db.session.commit()
    return "", 204


from app.extensions import jwt
@jwt.token_in_blocklist_loader
def token_revoked(_header, payload):
    return db.session.query(TokenBlocklist.id).filter_by(jti=payload["jti"]).first() is not None
