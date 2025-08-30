# app/schemas/log_schema.py
from app.extensions import ma
from app.models import Log, LogLevel
from marshmallow import fields

class LogSchema(ma.SQLAlchemyAutoSchema):
    """
    Schema para serializar os dados de logs.
    """
    class Meta:
        model = Log
        load_instance = True
        include_fk = True

    level = fields.Enum(LogLevel, by_value=True)
    created_at = ma.auto_field(dump_only=True)