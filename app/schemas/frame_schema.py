# app/schemas/frame_schema.py
from app.extensions import ma
from app.models import Frame
from marshmallow import post_dump

# Importe a lista de rótulos para garantir a ordem correta
from app.tasks.process_video_task import EMOTION_LABELS

class FrameSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Frame
        load_instance = True
        include_fk = True
        exclude = () # Vamos gerir os campos de emoção manualmente abaixo

    @post_dump
    def format_frame_output(self, data, **kwargs):
        """
        Este método é executado após a serialização inicial.
        Ele garante que as listas de emoções e confianças são
        retornadas na ordem correta e consistente.
        """
        # Pega e remove o dicionário de emoções original da resposta
        raw_emotions_dict = data.pop("emotions", None)

        if raw_emotions_dict and isinstance(raw_emotions_dict, dict):
            # --- LÓGICA DE ORDENAÇÃO ---
            # Garante que a lista de emoções seja sempre a mesma que EMOTION_LABELS
            data['emotions'] = EMOTION_LABELS
            # Cria a lista de confianças na mesma ordem,
            # buscando cada valor no dicionário.
            data['confidences'] = [raw_emotions_dict.get(emotion, 0) for emotion in EMOTION_LABELS]
        else:
            # Se não houver dados, retorna listas vazias na ordem correta
            data['emotions'] = EMOTION_LABELS
            data['confidences'] = [0] * len(EMOTION_LABELS)
        
        return data