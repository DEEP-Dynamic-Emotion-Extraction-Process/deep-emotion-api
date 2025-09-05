# app/api/video_controller.py

import uuid
import os
import traceback
from flask import request, jsonify, Blueprint, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename

from app import services
from app.schemas import VideoSchema, VideoDetailSchema
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

    video_detail_schema = VideoDetailSchema()
    return jsonify(video_detail_schema.dump(video)), 200

@video_bp.route('/upload', methods=['POST'])
@jwt_required()
def upload_video():
    storage_type = current_app.config.get('STORAGE_TYPE', 's3')
    if storage_type == 'local':
        return upload_local_video()
    else:
        return initialize_s3_upload()

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