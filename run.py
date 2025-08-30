# run.py

import os
from app import create_app

from dotenv import load_dotenv
load_dotenv()

# Obtém a configuração do ambiente ou usa 'development' como padrão
config_name = os.getenv('FLASK_CONFIG', 'development')

app = create_app(config_name)

if __name__ == '__main__':
    app.run()