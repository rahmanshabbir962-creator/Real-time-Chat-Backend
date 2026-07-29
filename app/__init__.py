from dotenv import load_dotenv
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from marshmallow import ValidationError

from app.config import Config
from app.extensions import db, jwt, migrate, socketio


def create_app(config_object=Config):
    load_dotenv()
    app = Flask(__name__)
    app.config.from_object(config_object)
    CORS(app, resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}}, supports_credentials=False)
    db.init_app(app)
    migrate.init_app(app, db, compare_type=True)
    jwt.init_app(app)
    socketio.init_app(app, cors_allowed_origins=app.config["CORS_ORIGINS"], message_queue=app.config["SOCKETIO_MESSAGE_QUEUE"])

    from app.models import message, membership, room, token_blocklist, user  # register model metadata
    from app.routes.auth import auth_bp
    from app.routes.users import users_bp
    from app.routes.rooms import rooms_bp
    from app.routes.messages import messages_bp
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(users_bp, url_prefix="/api/users")
    app.register_blueprint(rooms_bp, url_prefix="/api/rooms")
    app.register_blueprint(messages_bp, url_prefix="/api/messages")
    from app.sockets import chat, status, typing  # register socket events

    @app.get("/")
    def index():
        return send_from_directory(app.static_folder, "index.html")

    @app.get("/health")
    def health():
        return {"status": "ok"}, 200

    @app.errorhandler(ValidationError)
    def validation_error(error):
        return jsonify({"error": "validation_error", "messages": error.messages}), 422

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"error": "not_found", "message": "Resource not found"}), 404

    @app.errorhandler(500)
    def server_error(error):
        db.session.rollback()
        return jsonify({"error": "internal_server_error", "message": "An unexpected error occurred"}), 500

    return app
