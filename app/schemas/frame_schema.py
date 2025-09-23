# app/schemas/frame_schema.py
from app.extensions import ma
from app.models import Frame, EmotionEnum
from marshmallow import fields

class FrameSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Frame
        load_instance = True
        include_fk = True

    emotion = fields.Enum(EmotionEnum, by_value=True)