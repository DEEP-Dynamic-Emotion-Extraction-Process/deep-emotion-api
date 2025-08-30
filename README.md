# DeepEmotion API 🤖🎥

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-3.0-black.svg)
![Celery](https://img.shields.io/badge/Celery-5.4-green.svg)
![Docker](https://img.shields.io/badge/Docker-20.10+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

API robusta para análise assíncrona de emoções em vídeos. A aplicação permite que usuários façam upload de vídeos, que são processados em segundo plano para extrair e analisar as emoções frame a frame usando um modelo de machine learning.

---

## ✨ Funcionalidades

* **Autenticação de Usuários:** Sistema completo de registro e login com tokens de acesso **JWT**.
* **Upload Eficiente de Arquivos:** Utiliza **URLs Pré-Assinadas do S3** para que o cliente envie vídeos diretamente para a nuvem, sem sobrecarregar a API.
* **Processamento Assíncrono:** Tarefas de longa duração (processamento de vídeo e análise de IA) são executadas em background com **Celery**, garantindo que a API permaneça rápida e responsiva.
* **Análise de Emoções:** Extrai frames de vídeos e utiliza um modelo TensorFlow/Keras para classificar emoções.
* **Arquitetura Escalável:** Construído com uma arquitetura em camadas (Controllers, Services, Models) e containerizado com **Docker**, pronto para ambientes de desenvolvimento e produção.

---

## 🏛️ Arquitetura

O projeto utiliza uma arquitetura de microsserviços desacoplada, orquestrada pelo Docker Compose.

```
                  [Cliente (WebApp Node.js)]
                           |
                           | HTTPS (API Calls)
                           V
[API (Flask + Gunicorn)] <-----> [Banco de Dados (AWS RDS)]
      |        ^
      | Task   |
      | Queue  | Results
      V        |
  [Redis] <----+------------------ [Worker (Celery)]
      ^                                     |
      |                                     | Download do Vídeo / Modelo
      +-------------------------------------+
                                            |
                                            V
                                     [AWS S3 Buckets]
                                     (Vídeos e Modelos)
```

---

## 🛠️ Stack de Tecnologias

* **Backend:** Flask, Gunicorn
* **Banco de Dados:** MySQL (via AWS RDS), SQLAlchemy (ORM), Flask-Migrate
* **Tarefas Assíncronas:** Celery, Redis
* **Autenticação:** Flask-JWT-Extended
* **Validação/Serialização:** Flask-Marshmallow
* **Processamento de Vídeo/IA:** OpenCV, TensorFlow, Numpy
* **Cloud:** AWS S3
* **Containerização:** Docker, Docker Compose

---

## 🚀 Como Executar Localmente

### Pré-requisitos
* [Git](https://git-scm.com/)
* [Python 3.11+](https://www.python.org/)
* [Docker](https://www.docker.com/products/docker-desktop/)
* [Docker Compose](https://docs.docker.com/compose/install/)

### 1. Clonar o Repositório
```bash
git clone https://github.com/DEEP-Dynamic-Emotion-Extraction-Process/api.git
cd api
```

### 2. Configurar o Ambiente
O projeto utiliza um arquivo `.env` para gerenciar as variáveis de ambiente. Crie o seu a partir do esqueleto fornecido.

```bash
# Copie o arquivo de exemplo
cp .env.example .env
```
**Agora, abra o arquivo `.env` e preencha todas as variáveis**, como as chaves da AWS, a URL do banco de dados e as chaves secretas.

> **Importante:** Para o `CELERY_BROKER_URL`, o host deve ser `redis`, pois é o nome do serviço no `docker-compose.yml`.

### 3. Subir os Contêineres
Com o Docker em execução, use o Docker Compose para construir as imagens e iniciar todos os serviços (API, Worker e Redis) com um único comando.

```bash
docker-compose up --build
```
* A flag `--build` é necessária na primeira vez ou sempre que você alterar o `Dockerfile` ou `requirements.txt`.
* Aguarde até que os logs indiquem que os serviços estão rodando e prontos.

### 4. Executar as Migrações do Banco de Dados
Com os contêineres em execução, abra **um novo terminal** e execute o comando abaixo para criar as tabelas no seu banco de dados.

```bash
docker-compose exec api flask db upgrade
```
* `docker-compose exec api`: Executa um comando dentro do contêiner `api`.
* `flask db upgrade`: Aplica as migrações do banco de dados.

Sua API agora está rodando e acessível em `http://localhost:5000`.

---

## 📖 Uso da API

A API está versionada e todos os endpoints estão sob o prefixo `/api/v2`.

| Endpoint | Método | Protegido? | Descrição |
|---|---|---|---|
| `/auth/register` | `POST` | Não | Registra um novo usuário. |
| `/auth/login` | `POST` | Não | Autentica um usuário e retorna um token JWT. |
| `/videos/upload/initialize` | `POST` | **Sim** | Inicia o fluxo de upload, retornando uma URL do S3. |
| `/videos/upload/finalize` | `POST` | **Sim** | Finaliza o upload e dispara o processamento. |
| `/videos/` | `GET` | **Sim** | Lista todos os vídeos do usuário autenticado. |
| `/videos/<video_id>` | `GET` | **Sim** | Retorna os detalhes e a análise de um vídeo específico. |