# app/services/video_service.py

from app.extensions import db
from app.models import Video, Frame, VideoStatus, EmotionEnum
from datetime import datetime

class VideoServiceError(Exception):
    pass

def create_video_record(user_id, title, s3_key):
    """
    Cria um registro inicial para um vídeo no banco de dados.
    Chamado logo após o cliente confirmar o upload para o S3.
    """
    try:
        new_video = Video(
            user_id=user_id,
            title=title,
            s3_key=s3_key,
            status=VideoStatus.PENDING
        )
        db.session.add(new_video)
        db.session.commit()
        return new_video
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao criar registro do vídeo: {e}")
        raise VideoServiceError("Não foi possível criar o registro do vídeo.")

def get_video_by_id(video_id):
    """Busca um vídeo pelo seu ID."""
    return Video.query.get(video_id)

def get_videos_by_user(user_id):
    """Busca todos os vídeos de um usuário específico."""
    return Video.query.filter_by(user_id=user_id).order_by(Video.uploaded_at.desc()).all()

def update_video_status(video_id, new_status):
    """Atualiza o status de um vídeo (ex: de PENDING para PROCESSING)."""
    video = get_video_by_id(video_id)
    if not video:
        raise VideoServiceError("Vídeo não encontrado.")
    
    video.status = new_status
    db.session.commit()
    return video

def save_analysis_results(video_id, analysis_data):
    """
    Salva os resultados completos da análise no banco de dados.
    Esta é a etapa final da tarefa Celery.
    """
    video = get_video_by_id(video_id)
    if not video:
        raise VideoServiceError("Vídeo não encontrado.")
    
    try:
        video.frame_count = analysis_data.get('total_frames_analyzed', 0)
        video.duration_seconds = analysis_data.get('duration_seconds', 0.0)
        video.processed_at = datetime.utcnow()
        video.status = VideoStatus.COMPLETED

        frames_to_add = []
        for frame_data in analysis_data.get('frames', []):
            frame = Frame(
                video_id=video.id,
                frame_number=frame_data['frame_number'],
                video_timestamp_sec=frame_data['timestamp'],
                emotion=EmotionEnum[frame_data['emotion'].upper()],
                confidence=frame_data['confidence']
            )
            frames_to_add.append(frame)
        
        if frames_to_add:
            db.session.bulk_save_objects(frames_to_add)

        db.session.commit()
        return video
    except Exception as e:
        db.session.rollback()
        video.status = VideoStatus.FAILED
        db.session.commit()
        print(f"Erro ao salvar resultados da análise: {e}")
        raise VideoServiceError("Falha ao salvar os resultados da análise.")

# --- ADICIONE ESTA NOVA FUNÇÃO ---
def update_video_details(video_id, user_id, data):
    """
    Atualiza os detalhes de um vídeo, como o título.
    Verifica se o vídeo pertence ao usuário.
    """
    video = get_video_by_id(video_id)
    if not video:
        raise VideoServiceError("Vídeo não encontrado.")
    
    if str(video.user_id) != str(user_id):
        raise VideoServiceError("Acesso não permitido.")

    try:
        if 'title' in data:
            video.title = data['title']
        
        db.session.commit()
        return video
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao atualizar detalhes do vídeo: {e}")
        raise VideoServiceError("Não foi possível atualizar os detalhes do vídeo.")