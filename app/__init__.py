# app/__init__.py

from flask import Flask
from celery import Celery, Task

from config import config_by_name
from .extensions import db, ma, migrate, jwt, cors, socketio
from .api import api_v2_bp # Importa o blueprint principal da API

# Define o nome do nosso pacote de tarefas para o Celery
CELERY_TASK_LIST = [
    'app.tasks',
]

def create_celery(app):
    """
    Cria e configura a instância do Celery, conectando-a ao contexto da aplicação Flask.
    """
    class FlaskTask(Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery_app = Celery(app.import_name, task_cls=FlaskTask)
    celery_app.config_from_object(app.config["CELERY"])
    celery_app.autodiscover_tasks(CELERY_TASK_LIST)
    celery_app.set_default()
    return celery_app

def create_app(config_name='development'):
    """
    Application Factory: Cria e configura a instância da aplicação Flask.
    """
    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])

    db.init_app(app)
    ma.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": "*"}})
    
    # --- ALTERAÇÃO AQUI ---
    # Adicione a configuração da message_queue para o Socket.IO
    socketio.init_app(app, cors_allowed_origins="*", message_queue=app.config["CELERY"]["broker_url"])

    app.register_blueprint(api_v2_bp)

    return app