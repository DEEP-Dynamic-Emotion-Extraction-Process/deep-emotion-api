# app/services/s3_service.py

import boto3
import os
import shutil
from botocore.exceptions import ClientError
from flask import current_app, url_for

# --- Funções Locais ---

def local_generate_presigned_upload_url(object_name, **kwargs):
    """Para o modo local, retorna uma URL de upload direto para a API."""
    # Retorna o endpoint que vamos criar para receber o arquivo
    return url_for('api_v2.video_api.upload_local_video', _external=True)

def local_download_file(bucket_name, object_name, destination_path):
    """Copia um arquivo do armazenamento local para o destino."""
    # O "bucket_name" se torna o diretório base (ex: 'videos' ou 'models')
    source_path = os.path.join(current_app.config['LOCAL_STORAGE_PATH'], bucket_name, os.path.basename(object_name))
    if not os.path.exists(source_path):
        print(f"Arquivo local não encontrado em: {source_path}")
        return False
    try:
        os.makedirs(os.path.dirname(destination_path), exist_ok=True)
        shutil.copy(source_path, destination_path)
        print(f"Arquivo {source_path} copiado para {destination_path}.")
        return True
    except Exception as e:
        print(f"Erro ao copiar arquivo local: {e}")
        return False

# --- Funções S3 (As que você já tinha) ---

def s3_get_client():
    """Cria e retorna um cliente S3 configurado."""
    return boto3.client(
        's3',
        aws_access_key_id=current_app.config['AWS_ACCESS_KEY_ID'],
        aws_secret_access_key=current_app.config['AWS_SECRET_ACCESS_KEY'],
        region_name=current_app.config['AWS_REGION']
    )

def s3_generate_presigned_upload_url(object_name, expiration=3600):
    """Gera uma URL pré-assinada para o cliente fazer upload de um VÍDEO."""
    s3_client = s3_get_client()
    bucket_name = current_app.config['S3_VIDEOS_BUCKET']
    try:
        response = s3_client.generate_presigned_url(
            'put_object',
            Params={'Bucket': bucket_name, 'Key': object_name},
            ExpiresIn=expiration
        )
        return response
    except ClientError as e:
        print(f"Erro ao gerar URL pré-assinada: {e}")
        return None

def s3_download_file(bucket_name, object_name, destination_path):
    """Função genérica para baixar um arquivo de um bucket S3."""
    s3_client = s3_get_client()
    try:
        s3_client.download_file(bucket_name, object_name, destination_path)
        print(f"Arquivo {object_name} do S3 baixado para {destination_path}.")
        return True
    except ClientError as e:
        print(f"Erro ao baixar arquivo do S3: {e}")
        return False

# --- Dispatchers (Decidem qual função usar) ---

def generate_presigned_upload_url(object_name, expiration=3600):
    storage_type = current_app.config.get('STORAGE_TYPE', 's3')
    if storage_type == 'local':
        return local_generate_presigned_upload_url(object_name)
    else:
        return s3_generate_presigned_upload_url(object_name, expiration)

def download_video_from_s3(video_s3_key, destination_path):
    storage_type = current_app.config.get('STORAGE_TYPE', 's3')
    if storage_type == 'local':
        # Em modo local, o "bucket" é o subdiretório 'videos'
        return local_download_file('videos', video_s3_key, destination_path)
    else:
        bucket_name = current_app.config['S3_VIDEOS_BUCKET']
        return s3_download_file(bucket_name, video_s3_key, destination_path)

def download_model_from_s3(model_s3_key, destination_path):
    storage_type = current_app.config.get('STORAGE_TYPE', 's3')
    if storage_type == 'local':
        # Coloque seu modelo em /uploads/models/modelo_emocoes.h5
        if not os.path.exists(destination_path):
             print(f"Baixando modelo {model_s3_key} do armazenamento local...")
             return local_download_file('models', model_s3_key, destination_path)
    else:
        if not os.path.exists(destination_path):
            print(f"Baixando modelo {model_s3_key} do S3...")
            bucket_name = current_app.config['S3_MODELS_BUCKET']
            return s3_download_file(bucket_name, model_s3_key, destination_path)

    print(f"Modelo {destination_path} já existe localmente.")
    return True