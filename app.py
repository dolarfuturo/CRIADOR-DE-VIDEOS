import math
import os
import tempfile
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import streamlit as st

try:
    from moviepy import ImageSequenceClip
except ImportError:
    from moviepy.editor import ImageSequenceClip


st.set_page_config(page_title="Simulador F1 2D Dinâmico (MP4)", layout="centered")

W, H = 1080, 1920
MAP_W, MAP_H = 4400, 3960


def _carregar_fonte(tamanho):
    candidatos = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ]
    for caminho in candidatos:
        if os.path.exists(caminho):
            return ImageFont.truetype(caminho, tamanho)
    return ImageFont.load_default()


font_tag = _carregar_fonte(22)
font_placar_titulo = _carregar_fonte(23)
font_placar = _carregar_fonte(20)
font_legenda = _carregar_fonte(28)
font_banner = _carregar_fonte(26)
font_pista_label = _carregar_fonte(20)


def _hex_para_rgb(cor_hex):
    cor_hex = cor_hex.lstrip("#")
    return tuple(int(cor_hex[i : i + 2], 16) for i in (0, 2, 4))


def _cor_detalhe_por_equipe(equipe):
    detalhes = {
        "McLaren": (25, 25, 25),
        "Ferrari": (255, 220, 0),
        "Mercedes": (220, 220, 220),
        "Red Bull Racing": (235, 30, 45),
        "Audi": (255, 255, 255),
        "Aston Martin": (190, 215, 0),
        "Williams": (255, 255, 255),
        "Alpine": (25, 45, 95),
        "Racing Bulls": (255, 255, 255),
        "Cadillac": (25, 25, 30),
        "Haas": (220, 30, 40),
    }
    return detalhes.get(equipe, (240, 240, 240))


CIRCUITOS_2026 = {
    "Brasil (Interlagos)": {
        "titulo": "GP DE SAO PAULO - INTERLAGOS",
        "voltas_padrao": 71,
        "pontos_norm": [
            (0.77, 0.84),
            (0.80, 0.64),
            (0.83, 0.44),
            (0.77, 0.31),
            (0.84, 0.22),
            (0.78, 0.14),
            (0.60, 0.12),
            (0.40, 0.12),
            (0.22, 0.14),
            (0.16, 0.24),
            (0.25, 0.34),
            (0.42, 0.39),
            (0.56, 0.43),
            (0.60, 0.52),
            (0.52, 0.58),
            (0.42, 0.56),
            (0.35, 0.65),
            (0.44, 0.73),
            (0.24, 0.76),
            (0.19, 0.84),
            (0.35, 0.91),
            (0.60, 0.91),
            (0.74, 0.89),
        ],
    },
    "Austrália (Melbourne)": {
        "titulo": "GP DA AUSTRALIA - MELBOURNE",
        "voltas_padrao": 58,
        "pontos_norm": [
            (0.18, 0.80),
            (0.58, 0.80),
            (0.86, 0.66),
            (0.82, 0.34),
            (0.56, 0.18),
            (0.40, 0.36),
            (0.22, 0.26),
            (0.12, 0.52),
        ],
    },
    "China (Xangai)": {
        "titulo": "GP DA CHINA - XANGAI",
        "voltas_padrao": 56,
        "pontos_norm": [
            (0.18, 0.82),
            (0.62, 0.82),
            (0.72, 0.68),
            (0.64, 0.52),
            (0.46, 0.48),
            (0.35, 0.60),
            (0.42, 0.38),
            (0.72, 0.28),
            (0.86, 0.18),
            (0.74, 0.14),
            (0.38, 0.16),
            (0.15, 0.24),
            (0.13, 0.46),
            (0.24, 0.60),
        ],
    },
    "Japão (Suzuka)": {
        "titulo": "GP DO JAPAO - SUZUKA",
        "voltas_padrao": 53,
        "pontos_norm": [
            (0.15, 0.78),
            (0.58, 0.74),
            (0.76, 0.42),
            (0.48, 0.20),
            (0.24, 0.32),
            (0.46, 0.52),
            (0.86, 0.44),
            (0.80, 0.80),
        ],
    },
    "Miami": {
        "titulo": "GP DE MIAMI",
        "voltas_padrao": 57,
        "pontos_norm": [
            (0.15, 0.82),
            (0.80, 0.82),
            (0.88, 0.52),
            (0.60, 0.42),
            (0.80, 0.22),
            (0.32, 0.18),
            (0.16, 0.44),
            (0.38, 0.64),
        ],
    },
    "Canadá (Montreal)": {
        "titulo": "GP DO CANADA - MONTREAL",
        "voltas_padrao": 70,
        "pontos_norm": [
            (0.12, 0.68),
            (0.88, 0.68),
            (0.85, 0.34),
            (0.50, 0.26),
            (0.32, 0.44),
            (0.14, 0.36),
        ],
    },
    "Mônaco": {
        "titulo": "GP DE MONACO",
        "voltas_padrao": 78,
        "pontos_norm": [
            (0.20, 0.82),
            (0.82, 0.82),
            (0.88, 0.50),
            (0.62, 0.20),
            (0.44, 0.40),
            (0.24, 0.18),
            (0.12, 0.46),
        ],
    
