#!/bin/sh

# entrypoint.sh

# Aplica as migrações do banco de dados
echo "Aplicando migrações do banco de dados..."
flask db upgrade

# Inicia a aplicação principal com Gunicorn
echo "Iniciando o servidor Gunicorn..."
exec gunicorn --worker-class geventwebsocket.gunicorn.workers.GeventWebSocketWorker --bind 0.0.0.0:5000 run:app