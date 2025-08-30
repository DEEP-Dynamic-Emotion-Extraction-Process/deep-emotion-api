# celery_worker.py

import os
from app import create_app, create_celery

# Seleciona a configuração baseada em uma variável de ambiente
config_name = os.getenv('FLASK_CONFIG', 'development')
app = create_app(config_name)

# Cria a instância do Celery associada à aplicação Flask
celery = create_celery(app)