# app/services/auth_service.py

from app.models import User
from app.extensions import db
from flask_jwt_extended import create_access_token
from datetime import timedelta

# Criamos exceções customizadas para um melhor controle de erros
class RegistrationError(Exception):
    pass

class LoginError(Exception):
    pass

def register_user(username, email, password):
    """
    Serviço para registrar um novo usuário.
    Contém a lógica de negócio para validação.
    """
    # 1. Lógica de Negócio: Verificar se o usuário ou email já existem
    if User.query.filter_by(username=username).first():
        raise RegistrationError("Nome de usuário já existe.")
    if User.query.filter_by(email=email).first():
        raise RegistrationError("Email já cadastrado.")

    # 2. Interação com o Model: Criar a nova instância
    new_user = User(username=username, email=email)
    new_user.set_password(password) # Usa o método do modelo para hashear a senha

    # 3. Persistência: Salvar no banco de dados
    try:
        db.session.add(new_user)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        # Idealmente, logar o erro 'e' aqui
        raise RegistrationError("Erro ao salvar usuário no banco de dados.")

    return new_user

def login_user(email, password):
    """
    Serviço para autenticar um usuário e retornar um token JWT.
    """
    # 1. Lógica de Negócio: Encontrar o usuário e verificar a senha
    user = User.query.filter_by(email=email).first()

    if not user or not user.check_password(password):
        raise LoginError("Credenciais inválidas. Verifique seu email e senha.")

    # 2. Geração do Token: Se as credenciais estiverem corretas
    # O 'identity' pode ser o ID do usuário ou o objeto completo, o ID é mais comum
    access_token = create_access_token(
        identity=user.id,
        expires_delta=timedelta(hours=1) # Define a duração do token
    )
    
    return access_token

def get_user_by_id(user_id):
    """Busca um usuário pelo seu ID."""
    return User.query.get(user_id)