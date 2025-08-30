# app/api/auth_controller.py

from flask import request, jsonify, Blueprint
from marshmallow import ValidationError

from app import services
from app.schemas import UserSchema, UserRegistrationSchema

# Cria um Blueprint. Blueprints são como "mini-aplicações" que podemos registrar na app principal.
auth_bp = Blueprint('auth_api', __name__, url_prefix='/auth')

@auth_bp.route('/register', methods=['POST'])
def register():
    """Endpoint para registrar um novo usuário."""
    json_data = request.get_json()
    if not json_data:
        return jsonify({"error": "Nenhum dado de entrada fornecido"}), 400

    # Validação dos dados de entrada com o schema
    try:
        data = UserRegistrationSchema().load(json_data)
    except ValidationError as err:
        return jsonify(err.messages), 422 # 422 Unprocessable Entity

    try:
        # Chama o serviço para executar a lógica de negócio
        new_user = services.register_user(
            username=data['username'],
            email=data['email'],
            password=data['password']
        )
        # Serializa a resposta
        user_schema = UserSchema()
        return jsonify(user_schema.dump(new_user)), 201 # 201 Created
    except services.RegistrationError as e:
        return jsonify({"error": str(e)}), 409 # 409 Conflict (usuário já existe)
    except Exception as e:
        # Logar o erro 'e'
        return jsonify({"error": "Ocorreu um erro inesperado."}), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    """Endpoint para autenticar um usuário e retornar um token JWT."""
    json_data = request.get_json()
    if not json_data:
        return jsonify({"error": "Nenhum dado de entrada fornecido"}), 400

    email = json_data.get('email')
    password = json_data.get('password')

    if not email or not password:
        return jsonify({"error": "Email e senha são obrigatórios."}), 400

    try:
        # Chama o serviço para autenticar e gerar o token
        access_token = services.login_user(email, password)
        return jsonify(access_token=access_token), 200
    except services.LoginError as e:
        return jsonify({"error": str(e)}), 401 # 401 Unauthorized
    except Exception as e:
        # Logar o erro 'e'
        return jsonify({"error": "Ocorreu um erro inesperado."}), 500