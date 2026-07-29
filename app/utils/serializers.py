def iso(value):
    return value.isoformat() if value else None


def user_data(user):
    return {"id": user.id, "username": user.username, "email": user.email, "display_name": user.display_name,
            "avatar_url": user.avatar_url, "is_online": user.is_online, "last_seen_at": iso(user.last_seen_at), "created_at": iso(user.created_at)}


def room_data(room, include_members=False):
    result = {"id": room.id, "name": room.name, "description": room.description, "is_private": room.is_private,
              "created_by": room.created_by, "created_at": iso(room.created_at), "updated_at": iso(room.updated_at),
              "member_count": len(room.memberships)}
    if include_members:
        result["members"] = [{"user": user_data(m.user), "role": m.role, "joined_at": iso(m.joined_at)} for m in room.memberships]
    return result


def message_data(message):
    return {"id": message.id, "room_id": message.room_id, "author_id": message.author_id, "author": user_data(message.author),
            "content": None if message.deleted_at else message.content, "created_at": iso(message.created_at),
            "edited_at": iso(message.edited_at), "deleted_at": iso(message.deleted_at)}

