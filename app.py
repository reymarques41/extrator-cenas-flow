"""
App web para extrair cenas de vídeo e baixar as imagens.
Rode localmente com: streamlit run app.py
Ou hospede de graça em streamlit.io (veja instruções abaixo).

Requisitos (crie um arquivo requirements.txt com estas linhas):
    streamlit
    opencv-python-headless
    scenedetect[opencv]
    numpy
"""

import streamlit as st
import tempfile
import os
import zipfile
import subprocess
import cv2
from scenedetect import open_video, SceneManager
from scenedetect.detectors import ContentDetector

st.set_page_config(page_title="Extrator de Cenas de Vídeo", page_icon="🎬")
st.title("🎬 Extrator de Cenas de Vídeo")
st.write(
    "Envie um vídeo e receba uma imagem representativa de cada cena, "
    "prontas para baixar em um .zip."
)

threshold = st.slider(
    "Sensibilidade (menor = detecta mais mudanças)",
    min_value=1.0, max_value=30.0, value=4.0, step=1.0
)

intervalo_segundos = st.slider(
    "Intervalo (segundos) caso poucas cenas sejam detectadas",
    min_value=1.0, max_value=10.0, value=2.0, step=0.5
)

arquivo_video = st.file_uploader(
    "Selecione o vídeo", type=["mp4", "mov", "avi", "mkv"]
)


def salvar_frames_intervalo(video_path, pasta_saida, intervalo_segundos):
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 25
    passo = max(1, int(fps * intervalo_segundos))
    idx, contador = 0, 1
    caminhos = []
    while True:
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ok, frame = cap.read()
        if not ok:
            break
        nome = os.path.join(pasta_saida, f"frame_{contador:03d}.jpg")
        cv2.imwrite(nome, frame)
        caminhos.append(nome)
        contador += 1
        idx += passo
    cap.release()
    return caminhos


def extrair_cenas(video_path, pasta_saida, threshold, intervalo_segundos):
    """Retorna lista de dicts: {caminho_imagem, inicio_seg, fim_seg}."""
    os.makedirs(pasta_saida, exist_ok=True)
    video = open_video(video_path)
    scene_manager = SceneManager()
    scene_manager.add_detector(ContentDetector(threshold=threshold))
    scene_manager.detect_scenes(video)
    scenes = scene_manager.get_scene_list()

    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 25
    resultado = []
    if len(scenes) < 3:
        # fallback: intervalos fixos, cada "cena" dura intervalo_segundos
        idx, contador = 0, 1
        passo = max(1, int(fps * intervalo_segundos))
        duracao_total = cap.get(cv2.CAP_PROP_FRAME_COUNT) / fps if fps else 0

   
