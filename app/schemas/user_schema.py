# app/schemas/user_schema.py
from app.extensions import ma
from app.models import User
from marshmallow import fields, validate

class UserSchema(ma.SQLAlchemyAutoSchema):
    """
    Schema para serializar os dados do usuário (respostas da API).
    """
    class Meta:
        model = User
        # Exclui o campo de hash da senha para NUNCA ser exposto
        exclude = ("password_hash",)
        load_instance = True

    id = ma.auto_field(dump_only=True) # Apenas para serialização (saída)
    created_at = ma.auto_field(dump_only=True)
    updated_at = ma.auto_field(dump_only=True)

class UserRegistrationSchema(ma.Schema):
    """
    Schema para validar os dados de entrada no registro de um novo usuário.
    """
    username = fields.String(required=True, validate=validate.Length(min=3, max=50))
    email = fields.Email(required=True, validate=validate.Length(max=100))
    # 'load_only=True' significa que este campo é usado para entrada, mas nunca para saída.
    password = fields.String(required=True, load_only=True, validate=validate.Length(min=8))