# app/services/__init__.py

from .auth_service import (
    register_user,
    login_user,
    get_user_by_id,
    RegistrationError,
    LoginError
)

from .s3_service import (
    generate_presigned_upload_url,
    s3_generate_presigned_get_url, # <-- ALTERADO
    download_video_from_s3,
    download_model_from_s3
)

from .video_service import (
    create_video_record,
    get_video_by_id,
    get_videos_by_user,
    update_video_status,
    save_analysis_results,
    update_video_details,
    VideoServiceError
)

__all__ = [
    'register_user',
    'login_user',
    'get_user_by_id',
    'RegistrationError',
    'LoginError',
    'generate_presigned_upload_url',
    's3_generate_presigned_get_url',
    'download_video_from_s3',
    'download_model_from_s3',
    'create_video_record',
    'get_video_by_id',
    'get_videos_by_user',
    'update_video_status',
    'save_analysis_results',
    'update_video_details',
    'VideoServiceError',
]