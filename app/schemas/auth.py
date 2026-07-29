from marshmallow import Schema, fields, validate


class SignupSchema(Schema):
    username = fields.Str(required=True, validate=validate.And(validate.Length(min=3, max=32), validate.Regexp(r"^[A-Za-z0-9_.-]+$")))
    email = fields.Email(required=True)
    password = fields.Str(required=True, load_only=True, validate=validate.Length(min=8, max=128))
    display_name = fields.Str(required=True, validate=validate.Length(min=1, max=80))


class LoginSchema(Schema):
    email = fields.Email(required=True)
    password = fields.Str(required=True, load_only=True, validate=validate.Length(min=1, max=128))

