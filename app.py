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
    "Sensibilidade (maior = detecta só mudanças fortes de cena)",
    min_value=10.0, max_value=60.0, value=27.0, step=1.0
)

duracao_minima_cena = st.slider(
    "Duração mínima de uma cena (segundos) — ignora mudanças rápidas (ex: fala, gestos)",
    min_value=1.0, max_value=15.0, value=3.0, step=0.5
)

intervalo_segundos = st.slider(
    "Intervalo (segundos) caso poucas cenas sejam detectadas",
    min_value=1.0, max_value=10.0, value=2.0, step=0.5
)

arquivo_video = st.file_uploader(
    "Selecione o vídeo", type=["mp4", "mov", "avi", "mkv"]
)


def extrair_cenas(video_path, pasta_saida, threshold, intervalo_segundos, duracao_minima_cena=3.0):
    """Retorna lista de dicts: {caminho_imagem, inicio_seg, fim_seg}."""
    os.makedirs(pasta_saida, exist_ok=True)
    video = open_video(video_path)
    fps_video = video.frame_rate or 25
    min_scene_len_frames = max(1, int(duracao_minima_cena * fps_video))
    scene_manager = SceneManager()
    scene_manager.add_detector(
        ContentDetector(threshold=threshold, min_scene_len=min_scene_len_frames)
    )
    scene_manager.detect_scenes(video)
    scenes = scene_manager.get_scene_list()

    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 25
    resultado = []

    if len(scenes) < 3:
        idx, contador = 0, 1
        passo = max(1, int(fps * intervalo_segundos))
        duracao_total = cap.get(cv2.CAP_PROP_FRAME_COUNT) / fps if fps else 0
        while True:
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ok, frame = cap.read()
            if not ok:
                break
            nome = os.path.join(pasta_saida, f"frame_{contador:03d}.jpg")
            cv2.imwrite(nome, frame)
            inicio = idx / fps
            fim = min(inicio + intervalo_segundos, duracao_total)
            resultado.append({"caminho_imagem": nome, "inicio_seg": inicio, "fim_seg": fim})
            contador += 1
            idx += passo
        cap.release()
        return resultado

    for i, (start, end) in enumerate(scenes, start=1):
        frame_num = start.get_frames()
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
        ok, frame = cap.read()
        if ok:
            nome = os.path.join(pasta_saida, f"cena_{i:03d}.jpg")
            cv2.imwrite(nome, frame)
            resultado.append({
                "caminho_imagem": nome,
                "inicio_seg": start.get_seconds(),
                "fim_seg": end.get_seconds(),
            })
    cap.release()
    return resultado


if arquivo_video is not None:
    if st.button("Extrair cenas"):
        with st.spinner("Processando vídeo..."):
            with tempfile.TemporaryDirectory() as tmp_dir:
                video_path = os.path.join(tmp_dir, arquivo_video.name)
                with open(video_path, "wb") as f:
                    f.write(arquivo_video.read())

                pasta_saida = os.path.join(tmp_dir, "cenas")
                cenas = extrair_cenas(video_path, pasta_saida, threshold, intervalo_segundos)

                if not cenas:
                    st.error("Nenhum frame foi extraído. Tente outro vídeo.")
                else:
                    st.success(f"{len(cenas)} cena(s) extraída(s)!")

                    for i, cena in enumerate(cenas, start=1):
                        st.image(cena["caminho_imagem"], caption=f"Cena {i:02d} ({cena['inicio_seg']:.1f}s – {cena['fim_seg']:.1f}s)")

                    zip_path = os.path.join(tmp_dir, "cenas.zip")
                    with zipfile.ZipFile(zip_path, "w") as zipf:
                        for cena in cenas:
                            zipf.write(cena["caminho_imagem"], os.path.basename(cena["caminho_imagem"]))

                    with open(zip_path, "rb") as f:
                        st.download_button(
                            "⬇️ Baixar todas as imagens (.zip)",
                            data=f,
                            file_name="cenas.zip",
                            mime="application/zip",
                        )
