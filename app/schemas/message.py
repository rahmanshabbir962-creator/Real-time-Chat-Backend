from marshmallow import Schema, fields, validate


class MessageCreateSchema(Schema):
    content = fields.Str(required=True, validate=validate.Length(min=1, max=5000))


class MessageUpdateSchema(Schema):
    content = fields.Str(required=True, validate=validate.Length(min=1, max=5000))

