from marshmallow import Schema, fields, validate


class RoomCreateSchema(Schema):
    name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    description = fields.Str(load_default=None, allow_none=True, validate=validate.Length(max=500))
    is_private = fields.Bool(load_default=False)


class RoomUpdateSchema(Schema):
    name = fields.Str(validate=validate.Length(min=1, max=100))
    description = fields.Str(allow_none=True, validate=validate.Length(max=500))
    is_private = fields.Bool()

