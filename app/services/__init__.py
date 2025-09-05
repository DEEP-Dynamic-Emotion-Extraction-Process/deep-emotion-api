# app/services/__init__.py

# Importações do serviço de autenticação
from .auth_service import (
    register_user,
    login_user,
    RegistrationError,
    LoginError
)

# Importações do serviço de armazenamento (antigo S3)
from .s3_service import (
    generate_presigned_upload_url,
    download_video_from_s3, # <-- Corrigido
    download_model_from_s3
)

# Importações do serviço de vídeo
from .video_service import (
    create_video_record,
    get_video_by_id,
    get_videos_by_user,
    update_video_status,
    save_analysis_results,
    VideoServiceError
)

# Define a "API pública" do pacote de serviços
__all__ = [
    # auth_service
    'register_user',
    'login_user',
    'RegistrationError',
    'LoginError',
    # s3_service (storage_service)
    'generate_presigned_upload_url',
    'download_video_from_s3', # <-- Corrigido
    'download_model_from_s3',
    # video_service
    'create_video_record',
    'get_video_by_id',
    'get_videos_by_user',
    'update_video_status',
    'save_analysis_results',
    'VideoServiceError',
]