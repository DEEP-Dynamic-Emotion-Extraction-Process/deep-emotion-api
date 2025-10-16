# app/tasks/process_video_task.py

import os
import cv2
import tempfile
import shutil
import numpy as np
import tensorflow as tf
from celery import shared_task
from flask import current_app
from flask_socketio import SocketIO
from app import services

# Configuração do SocketIO para o worker Celery
socketio_celery = SocketIO(message_queue=os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0"))

# --- CONFIGURAÇÕES GLOBAIS DA TAREFA ---
TARGET_FPS = 24
MAX_VIDEO_DURATION_SECONDS = 30

# --- CONFIGURAÇÃO DO NOVO MODELO ÚNICO ---
# Aponta para o seu novo modelo único
MODEL_CONFIG = {
    's3_key': 'models/modelo_emocoes.h5',
    'local_path': 'models/modelo_emocoes.h5'
}
# A ordem dos rótulos foi ajustada para corresponder EXATAMENTE à saída do modelo
EMOTION_LABELS = ['angry', 'disgust', 'fear', 'happy', 'neutral', 'sad', 'surprised']
loaded_model = None

def load_model():
    """Carrega o modelo de IA único, fazendo o download se necessário."""
    global loaded_model
    if loaded_model:
        return loaded_model

    print("Iniciando o carregamento do modelo de IA...")
    try:
        local_path = MODEL_CONFIG['local_path']
        s3_key = MODEL_CONFIG['s3_key']

        os.makedirs(os.path.dirname(local_path), exist_ok=True)

        if not os.path.exists(local_path):
            print(f"Baixando modelo de: {s3_key}")
            services.download_model_from_s3(s3_key, local_path)

        if not os.path.exists(local_path):
            raise FileNotFoundError(f"Arquivo do modelo não encontrado em: {local_path}")

        loaded_model = tf.keras.models.load_model(local_path)
        print("Modelo carregado com sucesso.")
        return loaded_model
    except Exception as e:
        print(f"ERRO CRÍTICO AO CARREGAR O MODELO: {e}")
        return None

def predict_emotions(img_path, model_instance):
    """Executa a predição em uma imagem e retorna o array de confianças."""
    try:
        img = tf.keras.preprocessing.image.load_img(img_path, target_size=(48, 48), color_mode="grayscale")
        img_array = tf.keras.preprocessing.image.img_to_array(img) / 255.0
        img_array = np.expand_dims(img_array, axis=0)

        prediction = model_instance.predict(img_array)

        # --- ADIÇÃO CRUCIAL PARA DEBUG ---
        # Esta linha irá mostrar a saída bruta do modelo no log do seu worker.
        print(f"DEBUG: Saída do Modelo para {os.path.basename(img_path)} -> {prediction[0]}")
        # ------------------------------------

        # Retorna o array de predições, ex: [0.1, 0.02, 0.05, 0.7, 0.03, 0.08, 0.02]
        return prediction[0]
    except Exception as e:
        print(f"Erro ao predizer emoção para {img_path}: {e}")
        return None

@shared_task(bind=True, ignore_result=True)
def process_video(self, video_id):
    print(f"Iniciando processamento para o vídeo ID: {video_id}")

    model = load_model()
    if not model:
        print("Nenhum modelo de IA carregado. Abortando tarefa.")
        with current_app.app_context():
            services.update_video_status(video_id, 'FAILED')
        return

    temp_dir = tempfile.mkdtemp()
    local_video_path = os.path.join(temp_dir, 'video.mp4')

    try:
        with current_app.app_context():
            video = services.get_video_by_id(video_id)
            if not video:
                print(f"Vídeo com ID {video_id} não encontrado.")
                return

            socketio_celery.emit('processing_update', {'video_id': video_id, 'status': 'PROCESSING', 'progress': 5})
            services.update_video_status(video_id, 'PROCESSING')

            if not services.download_video_from_s3(video.s3_key, local_video_path):
                raise IOError(f"Falha ao baixar o vídeo: {video.s3_key}")

        # Extração de frames (lógica permanece a mesma)
        cap = cv2.VideoCapture(local_video_path)
        video_fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / video_fps if video_fps > 0 else 0

        if duration > MAX_VIDEO_DURATION_SECONDS:
            raise ValueError(f"Vídeo excede a duração máxima de {MAX_VIDEO_DURATION_SECONDS}s.")

        extracted_frames = []
        c_frame = 0
        frame_interval = int(video_fps / TARGET_FPS) if video_fps > TARGET_FPS else 1

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret: break

            if c_frame % frame_interval == 0:
                frame_path = os.path.join(temp_dir, f"frame_{c_frame:04d}.jpg")
                gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                cv2.imwrite(frame_path, gray_frame)
                extracted_frames.append({
                    'frame_number': c_frame,
                    'path': frame_path,
                    'timestamp': cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0,
                })
            c_frame += 1
        cap.release()

        # --- LÓGICA DE ANÁLISE SIMPLIFICADA ---
        classified_results = []
        total_frames_to_process = len(extracted_frames)

        for i, frame_info in enumerate(extracted_frames):
            confidences = predict_emotions(frame_info['path'], model)

            if confidences is not None:
                # Cria um dicionário mapeando cada emoção à sua confiança
                emotion_data = dict(zip(EMOTION_LABELS, [float(c) for c in confidences]))
                classified_results.append({
                    'frame_number': frame_info['frame_number'],
                    'timestamp': frame_info['timestamp'],
                    'emotions': emotion_data # Este é o dicionário que será salvo como JSON
                })

            # Emite o progresso para o frontend
            progress = 5 + int(((i + 1) / total_frames_to_process) * 90)
            socketio_celery.emit('processing_update', {'video_id': video_id, 'status': 'PROCESSING', 'progress': progress})

        with current_app.app_context():
            analysis_data = {
                'total_frames_analyzed': total_frames_to_process,
                'duration_seconds': duration,
                'frames': sorted(classified_results, key=lambda x: x['frame_number'])
            }
            services.save_analysis_results(video_id, analysis_data)

        socketio_celery.emit('processing_update', {'video_id': video_id, 'status': 'COMPLETED', 'progress': 100})
        print(f"Processamento para o vídeo ID: {video_id} concluído com sucesso.")

    except Exception as e:
        print(f"ERRO ao processar vídeo {video_id}: {e}")
        socketio_celery.emit('processing_update', {'video_id': video_id, 'status': 'FAILED', 'progress': 0})
        with current_app.app_context():
            services.update_video_status(video_id, 'FAILED')
    finally:
        print(f"Limpando diretório temporário: {temp_dir}")
        shutil.rmtree(temp_dir)