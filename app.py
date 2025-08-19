import os
import cv2
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
import time
from collections import Counter
import numpy as np
import tensorflow as tf
from tensorflow.keras.preprocessing import image

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'mp4', 'mov', 'avi', 'mkv'}
MAX_VIDEO_DURATION_SECONDS = 30
TARGET_FPS = 24

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
CORS(app)

try:
    MODEL_PATH = 'models/modelo_emocoes.h5'
    model = tf.keras.models.load_model(MODEL_PATH)
    CLASS_NAMES = ['angry', 'disgust', 'fear', 'happy', 'neutral', 'sad', 'surprise']
    print(f"Modelo {MODEL_PATH} carregado com sucesso.")
except Exception as e:
    model = None
    print(f"ERRO CRÍTICO: Não foi possível carregar o modelo '{MODEL_PATH}': {e}")
    print("A análise de emoções estará desativada.")

def predict_emotion(img_path):
    if model is None:
        return "disabled", 0.0

    try:
        img = image.load_img(img_path, target_size=(48, 48))
        img_array = image.img_to_array(img)
        img_array = img_array / 255.0  
        img_array = np.expand_dims(img_array, axis=0)  

        predictions = model.predict(img_array)
        pred_class_index = np.argmax(predictions[0])
        confidence = predictions[0][pred_class_index]
        
        return CLASS_NAMES[pred_class_index], float(confidence)
    except Exception as e:
        print(f"Erro ao predizer a emoção para {img_path}: {e}")
        return "error", 0.0

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_video_duration(filepath):
    try:
        cap = cv2.VideoCapture(filepath)
        if not cap.isOpened(): return -1
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
        duration = frame_count / fps if fps > 0 else 0
        cap.release()
        return duration
    except: return -1

@app.route('/upload', methods=['POST'])
def upload_video():
    if 'file' not in request.files:
        return jsonify({"error": "Nenhum arquivo enviado"}), 400
    
    file = request.files['file']
    if file.filename == '' or not allowed_file(file.filename):
        return jsonify({"error": "Arquivo inválido ou não permitido"}), 400

    filename = secure_filename(file.filename)
    unique_folder_name = f"{int(time.time())}_{os.path.splitext(filename)[0]}"
    output_folder_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_folder_name)
    os.makedirs(output_folder_path, exist_ok=True)
    video_path = os.path.join(output_folder_path, filename)
    file.save(video_path)
    
    duration = get_video_duration(video_path)
    if duration > MAX_VIDEO_DURATION_SECONDS:
        os.remove(video_path)
        os.rmdir(output_folder_path)
        return jsonify({"error": f"O vídeo excede o limite de {MAX_VIDEO_DURATION_SECONDS}s."}), 413

    cap = cv2.VideoCapture(video_path)
    video_fps = cap.get(cv2.CAP_PROP_FPS)
    frame_interval = int(video_fps / TARGET_FPS) if video_fps > TARGET_FPS else 1
    frame_count = 0
    saved_frame_count = 0
    frame_paths = []

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret: break
        
        if frame_count % frame_interval == 0:
            frame_filename = os.path.join(output_folder_path, f"frame_{saved_frame_count:04d}.jpg")
            cv2.imwrite(frame_filename, frame)
            frame_paths.append(frame_filename)
            saved_frame_count += 1
        frame_count += 1
    cap.release()
    
    emotion_predictions = []
    if model is not None:
        for f_path in frame_paths:
            emotion, confidence = predict_emotion(f_path)
            if emotion != "error":
                emotion_predictions.append(emotion)
    
    if emotion_predictions:
        emotion_counts = Counter(emotion_predictions)
        dominant_emotion = emotion_counts.most_common(1)[0][0] 
    else:
        emotion_counts = {}
        dominant_emotion = "N/A"

    return jsonify({
        "message": "Processamento concluído com sucesso!",
        "analysis": {
            "dominant_emotion": dominant_emotion,
            "emotion_counts": dict(emotion_counts),
            "total_frames_analyzed": len(emotion_predictions)
        },
        "paths": {
            "video": video_path,
            "frames": output_folder_path
        }
    }), 200

if __name__ == '__main__':
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    app.run(debug=True, port=5000)