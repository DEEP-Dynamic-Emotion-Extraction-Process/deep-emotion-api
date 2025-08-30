# app/api/video_controller.py

import uuid
from flask import request, jsonify, Blueprint
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError

from app import services
from app.schemas import VideoSchema, VideoDetailSchema
from app.tasks import process_video

video_bp = Blueprint('video_api', __name__, url_prefix='/videos')

@video_bp.route('/', methods=['GET'])
@jwt_required() # Protege a rota, exigindo um token JWT válido
def get_user_videos():
    """Retorna a lista de vídeos para o usuário autenticado."""
    user_id = get_jwt_identity() # Extrai o ID do usuário do token JWT
    videos = services.get_videos_by_user(user_id)
    video_schema = VideoSchema(many=True) # 'many=True' para serializar uma lista
    return jsonify(video_schema.dump(videos)), 200

@video_bp.route('/<string:video_id>', methods=['GET'])
@jwt_required()
def get_video_details(video_id):
    """Retorna os detalhes de um vídeo específico, incluindo os frames."""
    user_id = get_jwt_identity()
    video = services.get_video_by_id(video_id)

    if not video or video.user_id != user_id:
        return jsonify({"error": "Vídeo não encontrado ou acesso não permitido."}), 404

    video_detail_schema = VideoDetailSchema()
    return jsonify(video_detail_schema.dump(video)), 200

@video_bp.route('/upload/initialize', methods=['POST'])
@jwt_required()
def initialize_upload():
    """
    Inicia o processo de upload. Gera e retorna uma URL pré-assinada do S3
    para o cliente fazer o upload direto.
    """
    user_id = get_jwt_identity()
    json_data = request.get_json()
    filename = json_data.get('filename')

    if not filename:
        return jsonify({"error": "O nome do arquivo é obrigatório."}), 400

    # Cria uma chave única para o objeto no S3 para evitar conflitos
    file_ext = filename.split('.')[-1]
    s3_key = f"uploads/{user_id}/{uuid.uuid4()}.{file_ext}"

    upload_url = services.generate_presigned_upload_url(s3_key)

    if not upload_url:
        return jsonify({"error": "Não foi possível iniciar o upload."}), 500

    return jsonify({
        "upload_url": upload_url,
        "s3_key": s3_key
    }), 200

@video_bp.route('/upload/finalize', methods=['POST'])
@jwt_required()
def finalize_upload():
    """
    Finaliza o processo de upload após o cliente enviar o arquivo para o S3.
    Cria o registro no DB e dispara a tarefa de processamento assíncrono.
    """
    user_id = get_jwt_identity()
    json_data = request.get_json()
    s3_key = json_data.get('s3_key')
    title = json_data.get('title')

    if not s3_key or not title:
        return jsonify({"error": "s3_key e title são obrigatórios."}), 400

    try:
        # 1. Cria o registro do vídeo no banco com status 'PENDING'
        video = services.create_video_record(user_id, title, s3_key)

        # 2. Dispara a tarefa Celery em segundo plano
        process_video.delay(video.id)

        # 3. Retorna a resposta imediatamente para o cliente
        video_schema = VideoSchema()
        return jsonify(video_schema.dump(video)), 202 # 202 Accepted
    except services.VideoServiceError as e:
        return jsonify({"error": str(e)}), 500