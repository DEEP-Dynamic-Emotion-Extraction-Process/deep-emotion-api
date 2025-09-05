# app/schemas/video_schema.py
from app.extensions import ma
from app.models import Video, VideoStatus
from marshmallow import fields, validate # <-- ADICIONE 'validate' AQUI
from .frame_schema import FrameSchema

class VideoSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Video
        load_instance = True
        include_fk = True

    id = ma.auto_field(dump_only=True)
    status = fields.Enum(VideoStatus, by_value=True, dump_only=True)
    uploaded_at = ma.auto_field(dump_only=True)
    processed_at = ma.auto_field(dump_only=True)

class VideoDetailSchema(VideoSchema):
    frames = fields.Nested(FrameSchema, many=True, dump_only=True)

class VideoUpdateSchema(ma.Schema):
    title = fields.String(required=True, validate=validate.Length(min=1, max=255))