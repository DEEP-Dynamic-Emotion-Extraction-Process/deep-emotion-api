# app/services/s3_service.py

import boto3
import os
from botocore.exceptions import ClientError
from flask import current_app

def get_s3_client():
    """Cria e retorna um cliente S3 configurado."""
    return boto3.client(
        's3',
        aws_access_key_id=current_app.config['AWS_ACCESS_KEY_ID'],
        aws_secret_access_key=current_app.config['AWS_SECRET_ACCESS_KEY'],
        region_name=current_app.config['AWS_REGION']
    )

def generate_presigned_upload_url(object_name, expiration=3600):
    """
    Gera uma URL pré-assinada para o cliente fazer upload de um VÍDEO.
    """
    s3_client = get_s3_client()
    bucket_name = current_app.config['S3_VIDEOS_BUCKET']
    
    try:
        response = s3_client.generate_presigned_url(
            'put_object',
            Params={'Bucket': bucket_name, 'Key': object_name},
            ExpiresIn=expiration
        )
    except ClientError as e:
        print(f"Erro ao gerar URL pré-assinada: {e}")
        return None
    
    return response

def download_file_from_s3(bucket_name, object_name, destination_path):
    """
    Função genérica para baixar um arquivo de um bucket S3 específico.
    """
    s3_client = get_s3_client()

    try:
        s3_client.download_file(bucket_name, object_name, destination_path)
        print(f"Arquivo {object_name} do bucket {bucket_name} baixado para {destination_path}.")
        return True
    except ClientError as e:
        print(f"Erro ao baixar o arquivo {object_name} do bucket {bucket_name}: {e}")
        return False

def download_video_from_s3(video_s3_key, destination_path):
    """Baixa um VÍDEO do bucket de vídeos."""
    bucket_name = current_app.config['S3_VIDEOS_BUCKET']
    return download_file_from_s3(bucket_name, video_s3_key, destination_path)

def download_model_from_s3(model_s3_key, destination_path):
    """Baixa o MODELO de IA do bucket de modelos."""
    if not os.path.exists(destination_path):
        print(f"Baixando modelo {model_s3_key} do S3...")
        bucket_name = current_app.config['S3_MODELS_BUCKET']
        return download_file_from_s3(bucket_name, model_s3_key, destination_path)
    print(f"Modelo {destination_path} já existe localmente.")
    return True