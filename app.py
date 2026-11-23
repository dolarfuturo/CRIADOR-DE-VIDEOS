import math
import os
import tempfile
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import streamlit as st

try:
    from moviepy import ImageSequenceClip
except ImportError:
    from moviepy.editor import ImageSequenceClip


st.set_page_config(page_title="Simulador F1 2D MP4", layout="centered")

LARGURA = 1080
ALTURA = 1920

CIRCUITOS_2026 = {
    "Austrália (Melbourne)": {
        "pista": "Albert Park",
        "pais": "Austrália",
        "voltas_padrao": 58,
        "pontos": [
            (0.14, 0.82), (0.62, 0.82), (0.90, 0.64), (0.86, 0.30),
            (0.56, 0.16), (0.38, 0.36), (0.20, 0.24), (0.10, 0.52),
        ],
    },
    "China (Xangai)": {
        "pista": "Circuito Internacional de Xangai",
        "pais": "China",
        "voltas_padrao": 56,
        "pontos": [
            (0.14, 0.82), (0.64, 0.82), (0.74, 0.68), (0.66, 0.52),
            (0.46, 0.48), (0.34, 0.60), (0.42, 0.38), (0.74, 0.28),
            (0.90, 0.18), (0.76, 0.12), (0.36, 0.14), (0.12, 0.22),
            (0.10, 0.46), (0.22, 0.60),
        ],
    },
    "Japão (Suzuka)": {
        "pista": "Circuito de Suzuka",
        "pais": "Japão",
        "voltas_padrao": 53,
        "pontos": [
            (0.12, 0.78), (0.60, 0.74), (0.78, 0.42), (0.48, 0.18),
            (0.22, 0.30), (0.46, 0.52), (0.90, 0.44), (0.84, 0.80),
        ],
    },
    "Miami": {
        "pista": "Autódromo Internacional de Miami",
        "pais": "Estados Unidos",
        "voltas_padrao": 57,
        "pontos": [
            (0.12, 0.84), (0.82, 0.84), (0.92, 0.52), (0.60, 0.42),
            (0.82, 0.20), (0.30, 0.16), (0.14, 0.44), (0.38, 0.64),
        ],
    },
    "Canadá (Montreal)": {
        "pista": "Circuito Gilles Villeneuve",
        "pais": "Canadá",
        "voltas_padrao": 70,
        "pontos": [
            (0.08, 0.68), (0.92, 0.68), (0.88, 0.32), (0.50, 0.24),
            (0.30, 0.44), (0.10, 0.34),
        ],
    },
    "Mônaco": {
        "pista": "Circuito de Mônaco",
        "pais": "Mônaco",
        "voltas_padrao": 78,
        "pontos": [
            (0.18, 0.82), (0.84, 0.82), (0.90, 0.50), (0.62, 0.18),
            (0.44, 0.40), (0.22, 0.16), (0.10, 0.46),
        ],
        
