# app/api/video_controller.py

import uuid
import os
import traceback
from flask import request, jsonify, Blueprint, current_app, send_from_directory, url_for
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from marshmallow import ValidationError

from app import services
from app.schemas import VideoSchema, VideoDetailSchema, VideoUpdateSchema
from app.tasks import process_video

video_bp = Blueprint('video_api', __name__, url_prefix='/videos')

@video_bp.route('/', methods=['GET'])
@jwt_required()
def get_user_videos():
    user_id = get_jwt_identity()
    videos = services.get_videos_by_user(user_id)
    video_schema = VideoSchema(many=True)
    return jsonify(video_schema.dump(videos)), 200

@video_bp.route('/<string:video_id>', methods=['GET'])
@jwt_required()
def get_video_details(video_id):
    user_id = get_jwt_identity()
    video = services.get_video_by_id(video_id)

    if not video or video.user_id != user_id:
        return jsonify({"error": "Vídeo não encontrado ou acesso não permitido."}), 404

    video_dump = VideoDetailSchema().dump(video)
    
    # --- LÓGICA DE DECISÃO CORRIGIDA ---
    storage_type = current_app.config.get('STORAGE_TYPE', 's3')
    if storage_type == 's3':
        video_dump['video_url'] = services.s3_generate_presigned_get_url(video.s3_key)
    else:
        filename = os.path.basename(video.s3_key)
        video_dump['video_url'] = url_for('api_v2.video_api.stream_video', filename=filename, _external=True)

    return jsonify(video_dump), 200

@video_bp.route('/upload', methods=['POST'])
@jwt_required()
def upload_video():
    storage_type = current_app.config.get('STORAGE_TYPE', 's3')
    if storage_type == 'local':
        return upload_local_video()
    else:
        return initialize_s3_upload()
    
@video_bp.route('/<string:video_id>', methods=['PATCH'])
@jwt_required()
def update_video(video_id):
    user_id = get_jwt_identity()
    json_data = request.get_json()
    if not json_data:
        return jsonify({"error": "Nenhum dado de entrada fornecido"}), 400

    try:
        data = VideoUpdateSchema().load(json_data)
    except ValidationError as err:
        return jsonify(err.messages), 422

    try:
        updated_video = services.update_video_details(video_id, user_id, data)
        return jsonify(VideoSchema().dump(updated_video)), 200
    except services.VideoServiceError as e:
        error_message = str(e)
        if "Acesso não permitido" in error_message or "Vídeo não encontrado" in error_message:
            return jsonify({"error": "Vídeo não encontrado ou acesso não permitido."}), 404
        return jsonify({"error": error_message}), 500
    except Exception:
        traceback.print_exc()
        return jsonify({"error": "Ocorreu um erro inesperado."}), 500

def initialize_s3_upload():
    user_id = get_jwt_identity()
    json_data = request.get_json()
    filename = json_data.get('filename')

    if not filename:
        return jsonify({"error": "O nome do arquivo é obrigatório."}), 400

    file_ext = filename.split('.')[-1] if '.' in filename else ''
    s3_key = f"uploads/{user_id}/{uuid.uuid4()}.{file_ext}"
    upload_url = services.generate_presigned_upload_url(s3_key)

    if not upload_url:
        return jsonify({"error": "Não foi possível iniciar o upload."}), 500
    
    return jsonify({"upload_url": upload_url, "s3_key": s3_key}), 200

def upload_local_video():
    user_id = get_jwt_identity()
    if 'file' not in request.files:
        return jsonify({"error": "Nenhum arquivo enviado."}), 400
    
    file = request.files['file']
    title = request.form.get('title')

    if not title or file.filename == '':
        return jsonify({"error": "Título e arquivo são obrigatórios."}), 400

    filename = secure_filename(file.filename)
    file_ext = filename.split('.')[-1] if '.' in filename else ''
    
    local_filename = f"{uuid.uuid4()}.{file_ext}"
    
    video_path = os.path.join(current_app.config['LOCAL_STORAGE_PATH'], 'videos', local_filename)
    os.makedirs(os.path.dirname(video_path), exist_ok=True)
    
    try:
        file.save(video_path)
        
        video_record_key = f"uploads/{user_id}/{local_filename}"
        video = services.create_video_record(user_id, title, video_record_key)
        process_video.delay(video.id)
        
        video_schema = VideoSchema()
        return jsonify(video_schema.dump(video)), 202
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": "Falha ao processar o upload local."}), 500

@video_bp.route('/upload/finalize', methods=['POST'])
@jwt_required()
def finalize_upload():
    storage_type = current_app.config.get('STORAGE_TYPE', 's3')
    if storage_type == 'local':
        return jsonify({"message": "Endpoint não aplicável para o modo de armazenamento local."}), 400
        
    user_id = get_jwt_identity()
    json_data = request.get_json()
    s3_key = json_data.get('s3_key')
    title = json_data.get('title')

    if not s3_key or not title:
        return jsonify({"error": "s3_key e title são obrigatórios."}), 400

    try:
        video = services.create_video_record(user_id, title, s3_key)
        process_video.delay(video.id)
        video_schema = VideoSchema()
        return jsonify(video_schema.dump(video)), 202
    except services.VideoServiceError as e:
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": "Ocorreu um erro inesperado ao finalizar o upload."}), 500
    
@video_bp.route('/stream/<path:filename>')
def stream_video(filename):
    """
    Serve o ficheiro de vídeo diretamente da pasta de uploads.
    Isto é usado pelo player de vídeo no frontend para o modo local.
    """
    videos_folder = os.path.join(current_app.config['LOCAL_STORAGE_PATH'], 'videos')
    return send_from_directory(videos_folder, filename)