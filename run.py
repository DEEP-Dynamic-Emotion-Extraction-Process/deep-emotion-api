import os
from app import create_app
from app.extensions import socketio # <-- ADICIONE ESTA LINHA

from dotenv import load_dotenv
load_dotenv()

config_name = os.getenv('FLASK_CONFIG', 'development')
app = create_app(config_name)

if __name__ == '__main__':
    # Use socketio.run() em vez de app.run()
    socketio.run(app, host='0.0.0.0', port=5000)