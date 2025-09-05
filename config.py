# config.py
import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Configurações base."""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'uma-chave-secreta-muito-dificil-de-adivinhar'
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'mysql+pymysql://user:password@localhost/deep_v2'

    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'outra-chave-secreta-para-jwt'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)

    CELERY = dict(
        broker_url=os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0"),
        result_backend=os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379/0"),
        task_ignore_result=True,
    )
    
    # --- NOVO: Configuração de Armazenamento ---
    STORAGE_TYPE = os.environ.get('STORAGE_TYPE', 's3')
    LOCAL_STORAGE_PATH = '/app/uploads'


    # Configurações da AWS (só serão usadas se STORAGE_TYPE for 's3')
    AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
    AWS_REGION = os.environ.get('AWS_REGION') or 'us-east-1'
    S3_VIDEOS_BUCKET = os.environ.get('S3_VIDEOS_BUCKET')
    S3_MODELS_BUCKET = os.environ.get('S3_MODELS_BUCKET')

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_ECHO = False

class ProductionConfig(Config):
    DEBUG = False

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

    CELERY = Config.CELERY.copy()
    CELERY['broker_url'] = 'memory://'
    CELERY['result_backend'] = 'rpc://'
    STORAGE_TYPE = 'local' # Força o modo local para testes

config_by_name = dict(
    development=DevelopmentConfig,
    production=ProductionConfig,
    testing=TestingConfig
)