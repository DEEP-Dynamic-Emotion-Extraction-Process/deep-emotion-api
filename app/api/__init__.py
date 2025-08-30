# app/api/__init__.py

from flask import Blueprint

# Importa os blueprints dos controllers
from .auth_controller import auth_bp
from .video_controller import video_bp

# Cria um blueprint principal para a API
api_v1_bp = Blueprint('api_v1', __name__, url_prefix='/api/v1')

# Registra os blueprints específicos dentro do blueprint principal
api_v1_bp.register_blueprint(auth_bp)
api_v1_bp.register_blueprint(video_bp)

# Este 'api_v1_bp' será importado e registrado na aplicação principal
# no arquivo app/__init__.py