# app/schemas/frame_schema.py
from app.extensions import ma
from app.models import Frame, EmotionEnum
from marshmallow import fields

class FrameSchema(ma.SQLAlchemyAutoSchema):
    """
    Schema para serializar os dados de um frame de vídeo.
    """
    class Meta:
        model = Frame
        load_instance = True
        include_fk = True # Inclui as chaves estrangeiras (video_id) no output

    # Garante que o valor do Enum seja retornado como string (ex: "HAPPY")
    emotion = fields.Enum(EmotionEnum, by_value=True)