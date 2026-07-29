# Realtime Chat Backend

A Flask + Socket.IO API for multi-room chat. It provides token authentication, user presence, public/private rooms, real-time messages, typing, and read receipts. The app uses MySQL in production and includes a SQLite-friendly test configuration.

## Quick start

1. Install Python 3.12 and MySQL 8.
2. Copy `.env.example` to `.env`, generate strong `SECRET_KEY` and `JWT_SECRET_KEY` values, and set `DATABASE_URL`.
3. Create the database named in `DATABASE_URL`.
4. Run:

```bash
pip install -r requirements.txt
flask db upgrade
python run.py
```

The API listens on `http://localhost:5000`; `GET /health` returns service health. For Docker, copy `.env.example` to `.env` and run `docker compose up --build`.

## Environment

| Variable | Purpose |
| --- | --- |
| `DATABASE_URL` | SQLAlchemy connection string, e.g. `mysql+pymysql://user:password@host/db` |
| `SECRET_KEY` / `JWT_SECRET_KEY` | Long random production secrets |
| `CORS_ORIGINS` | Comma-separated browser origins |
| `JWT_ACCESS_TOKEN_EXPIRES_MINUTES` | Access token TTL (default 30) |
| `JWT_REFRESH_TOKEN_EXPIRES_DAYS` | Refresh token TTL (default 30) |
| `SOCKETIO_MESSAGE_QUEUE` | Redis/RabbitMQ queue URL for multi-worker Socket.IO deployments |

## REST API

Send access tokens as `Authorization: Bearer <access_token>`.

| Method | Path | Description |
| --- | --- | --- |
| POST | `/api/auth/signup`, `/login` | Create account or sign in |
| POST | `/api/auth/refresh`, `/logout` | Refresh or revoke a token |
| GET/PATCH | `/api/users/me` | Read or update profile |
| GET | `/api/users/search?q=ada` | Search users |
| GET/POST | `/api/rooms` | List (`scope=joined|public`) or create rooms |
| GET/PATCH/DELETE | `/api/rooms/:id` | Get, update, or delete a room |
| POST | `/api/rooms/:id/join`, `/members` | Join a public room or invite to a private room |
| DELETE | `/api/rooms/:id/leave` | Leave a room |
| GET/POST | `/api/messages/rooms/:id` | Paginated history or create message |
| PATCH/DELETE | `/api/messages/:id` | Edit or soft-delete own message |
| POST | `/api/messages/:id/read` | Record a read receipt |

List endpoints accept `page` and `per_page` (maximum 100). Validation errors use HTTP 422, authorization failures 401/403, and missing records 404.

## Socket.IO

Connect using `io(url, { auth: { token: accessToken } })`. Before messaging, call `join_room` with `{room_id}`. The server verifies membership for every room action.

| Client event | Payload | Server event(s) |
| --- | --- | --- |
| `join_room` / `leave_room` | `{room_id}` | `room_joined`, `member_joined`, `member_left` |
| `send_message` | `{room_id, content}` | `new_message` |
| `edit_message` / `delete_message` | `{message_id, content?}` | `message_updated`, `message_deleted` |
| `typing` | `{room_id, is_typing}` | `typing` |
| `mark_read` | `{message_id}` | `message_read` |
| — | — | `user_status`, `connected`, `room_updated`, `room_deleted`, `error` |

Delivery is represented by broadcast of `new_message`; `message_read` is the persistent per-member read receipt. JWT revocations are persisted in MySQL, so logout survives restarts. For horizontally scaled Socket.IO workers, configure a shared `SOCKETIO_MESSAGE_QUEUE`; use Redis in a production deployment.

## Structure

- `app/models`: SQLAlchemy entities and relationships.
- `app/routes`: authenticated REST resources.
- `app/sockets`: Socket.IO presence, chat, and typing handlers.
- `app/schemas`: Marshmallow request validation.
- `app/services`: reusable authorization rules.
- `migrations`: Flask-Migrate/Alembic schema history.
- `tests`: auth, room, and message lifecycle tests.

## Test

```bash
pytest -q
```

## Production notes

Terminate TLS at a reverse proxy, set non-default secrets and explicit CORS origins, run database backups, and use a shared Socket.IO message queue when scaling beyond one process.
