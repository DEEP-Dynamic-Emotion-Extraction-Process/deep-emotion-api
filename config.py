# config.py

import os
from datetime import timedelta
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

class Config:
    """Configurações base."""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'uma-chave-secreta-muito-dificil-de-adivinhar'
    
    # Configurações do SQLAlchemy
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'mysql+pymysql://user:password@localhost/deep_v2'

    # Configurações do JWT (JSON Web Token)
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'outra-chave-secreta-para-jwt'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)

    # Configurações do Celery
    CELERY = dict(
        broker_url=os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0"),
        result_backend=os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379/0"),
        task_ignore_result=True,
    )

    # Configurações da AWS
    AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
    AWS_REGION = os.environ.get('AWS_REGION') or 'us-east-1'
    
    # Bucket para os vídeos enviados pelos usuários
    S3_VIDEOS_BUCKET = os.environ.get('S3_VIDEOS_BUCKET')
    
    # Bucket para os modelos de Machine Learning
    S3_MODELS_BUCKET = os.environ.get('S3_MODELS_BUCKET')

class DevelopmentConfig(Config):
    """Configurações para o ambiente de desenvolvimento."""
    DEBUG = True
    SQLALCHEMY_ECHO = False # Mude para True para ver as queries SQL geradas

class ProductionConfig(Config):
    """Configurações para o ambiente de produção."""
    DEBUG = False
    # Adicione outras configurações de produção aqui (ex: logging, etc.)

class TestingConfig(Config):
    """Configurações para o ambiente de testes."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:' # Usa um banco de dados em memória para testes
    CELERY['broker_url'] = 'memory://' # Usa um broker em memória para testes
    CELERY['result_backend'] = 'rpc://'

# Dicionário para facilitar a seleção da configuração
config_by_name = dict(
    development=DevelopmentConfig,
    production=ProductionConfig,
    testing=TestingConfig
)