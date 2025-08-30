# app/schemas/video_schema.py
from app.extensions import ma
from app.models import Video, VideoStatus
from marshmallow import fields
from .frame_schema import FrameSchema

class VideoSchema(ma.SQLAlchemyAutoSchema):
    """
    Schema principal para vídeos, usado em listagens e respostas gerais.
    """
    class Meta:
        model = Video
        load_instance = True
        include_fk = True # Inclui user_id

    id = ma.auto_field(dump_only=True)
    status = fields.Enum(VideoStatus, by_value=True, dump_only=True)
    uploaded_at = ma.auto_field(dump_only=True)
    processed_at = ma.auto_field(dump_only=True)
    # Exemplo de campo customizado que poderia gerar uma URL de download temporária
    # video_url = fields.Method("get_download_url", dump_only=True)

    # def get_download_url(self, obj):
    #     # Aqui você chamaria um serviço para gerar uma presigned URL do S3
    #     return f"https://seu-bucket.s3.amazonaws.com/{obj.s3_key}?presigned_url_aqui"


class VideoDetailSchema(VideoSchema):
    """
    Schema detalhado para um único vídeo, incluindo todos os seus frames.
    """
    # 'Nested' permite aninhar outros schemas. 'many=True' indica uma lista.
    frames = fields.Nested(FrameSchema, many=True, dump_only=True)

class VideoUpdateSchema(ma.Schema):
    """
    Schema para validar os dados na finalização do upload.
    Apenas o título pode ser enviado pelo cliente.
    """
    title = fields.String(required=True, validate=validate.Length(min=1, max=255))