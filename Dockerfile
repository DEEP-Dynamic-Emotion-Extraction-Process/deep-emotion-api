# Dockerfile

# 1. Imagem Base: Começamos com uma imagem oficial do Python, versão 3.11 slim.
FROM python:3.11-slim

# 2. Variáveis de Ambiente:
#    - PYTHONUNBUFFERED: Garante que os logs apareçam em tempo real.
#    - PYTHONDONTWRITEBYTECODE: Evita a criação de arquivos .pyc.
ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

# 3. Diretório de Trabalho: Define o diretório padrão dentro do contêiner.
WORKDIR /app

# 4. Dependências do Sistema: Instala as bibliotecas que o OpenCV precisa.
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# 5. Dependências do Python:
#    - Copia apenas o requirements.txt primeiro para aproveitar o cache do Docker.
#    - Instala as bibliotecas Python.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 6. Copiar o Código da Aplicação: Copia todo o resto do código do projeto.
COPY . .

# 7. Expor a Porta: Informa ao Docker que a aplicação web irá rodar na porta 5000.
EXPOSE 5000

# O comando para iniciar a aplicação (CMD) será definido no docker-compose.yml,
# pois teremos comandos diferentes para a API e para o Worker.