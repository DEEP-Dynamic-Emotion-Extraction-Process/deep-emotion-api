# app/tasks/process_video_task.py

import os
import cv2
import time
import tempfile
import shutil
import numpy as np
import tensorflow as tf
from celery import shared_task
from flask import current_app
from flask_socketio import SocketIO
from app import services
from collections import Counter

socketio_celery = SocketIO(message_queue=os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0"))

TARGET_FPS = 24
MAX_VIDEO_DURATION_SECONDS = 30
CONFIDENCE_THRESHOLD = 0.90

MODELS_CONFIG = {
    'happy': {'s3_key': 'models/modelo_ovr_happy.h5', 'local_path': 'models/modelo_ovr_happy.h5'},
    'sad': {'s3_key': 'models/modelo_ovr_sad.h5', 'local_path': 'models/modelo_ovr_sad.h5'},
    'angry': {'s3_key': 'models/modelo_ovr_angry.h5', 'local_path': 'models/modelo_ovr_angry.h5'},
    'surprised': {'s3_key': 'models/modelo_ovr_surprised.h5', 'local_path': 'models/modelo_ovr_surprised.h5'},
    'neutral': {'s3_key': 'models/modelo_ovr_neutral.h5', 'local_path': 'models/modelo_ovr_neutral.h5'},
    'fear': {'s3_key': 'models/modelo_ovr_fear.h5', 'local_path': 'models/modelo_ovr_fear.h5'},
    'disgust': {'s3_key': 'models/modelo_ovr_disgust.h5', 'local_path': 'models/modelo_ovr_disgust.h5'},
}

CASCADE_ORDER = ['happy', 'sad', 'angry', 'surprised', 'neutral', 'fear', 'disgust']

loaded_models = {}

def load_models():
    global loaded_models
    if loaded_models:
        return loaded_models

    print("Iniciando o carregamento dos modelos de IA...")
    for emotion, config in MODELS_CONFIG.items():
        try:
            local_path = config['local_path']
            s3_key = config['s3_key']
            
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            
            if not os.path.exists(local_path):
                print(f"Baixando modelo para '{emotion}'...")
                services.download_model_from_s3(s3_key, local_path)
            
            if not os.path.exists(local_path):
                raise FileNotFoundError(f"Arquivo do modelo '{emotion}' não encontrado em: {local_path}")
            
            loaded_models[emotion] = tf.keras.models.load_model(local_path)
            print(f"Modelo para '{emotion}' carregado com sucesso.")
        except Exception as e:
            print(f"ERRO CRÍTICO AO CARREGAR O MODELO '{emotion}': {e}")
    return loaded_models

def predict_single_emotion_confidence(img_path, model_instance):
    try:
        img = tf.keras.preprocessing.image.load_img(img_path, target_size=(48, 48), color_mode="grayscale")
        img_array = tf.keras.preprocessing.image.img_to_array(img) / 255.0
        img_array = np.expand_dims(img_array, axis=0)
        
        prediction = model_instance.predict(img_array)
        confidence = float(prediction[0][0])
        return confidence
    except Exception as e:
        print(f"Erro ao predizer emoção para {img_path}: {e}")
        return 0.0

@shared_task(bind=True, ignore_result=True)
def process_video(self, video_id):
    print(f"Iniciando processamento em cascata para o vídeo ID: {video_id}")
    
    models = load_models()
    if not models:
        print("Nenhum modelo de IA carregado. Abortando tarefa.")
        with current_app.app_context():
            services.update_video_status(video_id, 'FAILED')
        return

    temp_dir = tempfile.mkdtemp()
    local_video_path = os.path.join(temp_dir, 'video_to_process.mp4')
    
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

        cap = cv2.VideoCapture(local_video_path)
        video_fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / video_fps if video_fps > 0 else 0
        
        if duration > MAX_VIDEO_DURATION_SECONDS:
            raise ValueError(f"Vídeo excede a duração máxima de {MAX_VIDEO_DURATION_SECONDS}s.")

        unclassified_frames = []
        c_frame = 0
        frame_interval = int(video_fps / TARGET_FPS) if video_fps > TARGET_FPS else 1
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret: break
            
            if c_frame % frame_interval == 0:
                frame_path = os.path.join(temp_dir, f"frame_{c_frame:04d}.jpg")
                gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                cv2.imwrite(frame_path, gray_frame)
                unclassified_frames.append({
                    'frame_number': c_frame,
                    'path': frame_path,
                    'timestamp': cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0,
                })
            c_frame += 1
        cap.release()

        classified_results = []
        total_initial_frames = len(unclassified_frames)

        for emotion in CASCADE_ORDER:
            print(f"Analisando {len(unclassified_frames)} frames restantes para a emoção: {emotion.upper()}")
            model = models.get(emotion)
            
            if not model:
                print(f"Modelo para '{emotion}' não encontrado. Pulando.")
                continue
            
            remaining_frames_after_pass = []
            
            for frame_info in unclassified_frames:
                confidence = predict_single_emotion_confidence(frame_info['path'], model)
                
                if confidence >= CONFIDENCE_THRESHOLD:
                    classified_results.append({
                        'frame_number': frame_info['frame_number'],
                        'timestamp': frame_info['timestamp'],
                        'emotion': emotion,
                        'confidence': confidence
                    })
                else:
                    remaining_frames_after_pass.append(frame_info)
            
            unclassified_frames = remaining_frames_after_pass
            
            progress = 5 + int(((total_initial_frames - len(unclassified_frames)) / total_initial_frames) * 90)
            socketio_celery.emit('processing_update', {'video_id': video_id, 'status': 'PROCESSING', 'progress': progress})

        for frame_info in unclassified_frames:
            classified_results.append({
                'frame_number': frame_info['frame_number'],
                'timestamp': frame_info['timestamp'],
                'emotion': 'unidentified',
                'confidence': 0.0
            })

        with current_app.app_context():
            analysis_data = {
                'total_frames_analyzed': total_initial_frames,
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