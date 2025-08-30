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

from app import services

# Constantes de processamento
TARGET_FPS = 24
MAX_VIDEO_DURATION_SECONDS = 30
MODEL_S3_KEY = 'models/modelo_emocoes.h5' 
MODEL_LOCAL_PATH = 'models/modelo_emocoes.h5'
CLASS_NAMES = ['angry', 'disgust', 'fear', 'happy', 'neutral', 'sad', 'surprise']
model = None

def load_model():
    """Carrega o modelo de IA, baixando-o do S3 se necessário."""
    global model
    if model is None:
        try:
            # Garante que o diretório local para o modelo exista
            os.makedirs(os.path.dirname(MODEL_LOCAL_PATH), exist_ok=True)
            # Baixa o modelo do bucket S3 correto
            services.download_model_from_s3(MODEL_S3_KEY, MODEL_LOCAL_PATH)
            
            if not os.path.exists(MODEL_LOCAL_PATH):
                raise FileNotFoundError(f"Arquivo do modelo não encontrado em: {MODEL_LOCAL_PATH}")
            
            model = tf.keras.models.load_model(MODEL_LOCAL_PATH)
            print("Modelo de IA carregado com sucesso.")
        except Exception as e:
            print(f"ERRO CRÍTICO AO CARREGAR O MODELO: {e}")
            model = None
    return model

def predict_emotion(img_path, model_instance):
    """Refatoração da sua função de predição de emoção."""
    if model_instance is None: 
        return "disabled", 0.0
    try:
        img = tf.keras.preprocessing.image.load_img(img_path, target_size=(48, 48))
        img_array = tf.keras.preprocessing.image.img_to_array(img) / 255.0
        img_array = np.expand_dims(img_array, axis=0)
        
        predictions = model_instance.predict(img_array)
        pred_idx = np.argmax(predictions[0])
        return CLASS_NAMES[pred_idx], float(predictions[0][pred_idx])
    except Exception as e:
        print(f"Erro ao predizer emoção para {img_path}: {e}")
        return "error", 0.0

@shared_task(bind=True, ignore_result=True)
def process_video(self, video_id):
    """
    Tarefa Celery para processar um vídeo: baixar, extrair frames, analisar e salvar resultados.
    """
    print(f"Iniciando processamento para o vídeo ID: {video_id}")
    
    ml_model = load_model()
    temp_dir = tempfile.mkdtemp()
    
    try:
        # 1. Obter metadados do vídeo e atualizar o status para 'PROCESSANDO'
        video = services.get_video_by_id(video_id)
        if not video:
            print(f"Vídeo com ID {video_id} não encontrado. Abortando tarefa.")
            return
        services.update_video_status(video_id, 'PROCESSING')

        # 2. Baixar o vídeo do S3 para um diretório temporário
        local_video_path = os.path.join(temp_dir, os.path.basename(video.s3_key))
        if not services.download_video_from_s3(video.s3_key, local_video_path):
            raise IOError("Falha ao baixar vídeo do S3.")

        # 3. Lógica de processamento com OpenCV
        cap = cv2.VideoCapture(local_video_path)
        if not cap.isOpened(): 
            raise IOError("Não foi possível abrir o arquivo de vídeo.")
        
        video_fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / video_fps if video_fps > 0 else 0
        
        if duration > MAX_VIDEO_DURATION_SECONDS:
            raise ValueError(f"Vídeo excede a duração máxima de {MAX_VIDEO_DURATION_SECONDS}s.")

        frame_interval = int(video_fps / TARGET_FPS) if video_fps > TARGET_FPS else 1
        
        # 4. Extração e Análise dos Frames
        frame_results = []
        c_frame, saved_count = 0, 0
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret: 
                break
            
            if c_frame % frame_interval == 0:
                frame_path = os.path.join(temp_dir, f"frame_{saved_count:04d}.jpg")
                cv2.imwrite(frame_path, frame)
                
                emotion, confidence = predict_emotion(frame_path, ml_model)
                if emotion not in ["error", "disabled"]:
                    frame_results.append({
                        'frame_number': saved_count,
                        'timestamp': cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0,
                        'emotion': emotion,
                        'confidence': confidence
                    })
                saved_count += 1
            c_frame += 1
        cap.release()

        # 5. Salvar os resultados no banco de dados usando o video_service
        analysis_data = {
            'total_frames_analyzed': len(frame_results),
            'duration_seconds': duration,
            'frames': frame_results
        }
        services.save_analysis_results(video_id, analysis_data)
        print(f"Processamento para o vídeo ID: {video_id} concluído com sucesso.")

    except Exception as e:
        print(f"ERRO ao processar vídeo {video_id}: {e}")
        # Se algo der errado, marca o vídeo como 'FAILED'
        services.update_video_status(video_id, 'FAILED')
    finally:
        # 6. Limpeza: remove o diretório temporário e todo o seu conteúdo
        print(f"Limpando diretório temporário: {temp_dir}")
        shutil.rmtree(temp_dir)