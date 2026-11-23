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
    },
    "Espanha (Barcelona-Catalunha)": {
        "pista": "Circuito de Barcelona-Catalunha",
        "pais": "Espanha",
        "voltas_padrao": 66,
        "pontos": [
            (0.12, 0.80), (0.88, 0.80), (0.92, 0.42), (0.62, 0.18),
            (0.28, 0.20), (0.14, 0.44), (0.46, 0.56), (0.18, 0.64),
        ],
    },
    "Áustria (Red Bull Ring)": {
        "pista": "Red Bull Ring",
        "pais": "Áustria",
        "voltas_padrao": 71,
        "pontos": [
            (0.12, 0.82), (0.90, 0.78), (0.72, 0.28), (0.32, 0.18),
            (0.16, 0.50),
        ],
    },
    "Grã-Bretanha (Silverstone)": {
        "pista": "Circuito de Silverstone",
        "pais": "Reino Unido",
        "voltas_padrao": 52,
        "pontos": [
            (0.12, 0.78), (0.74, 0.78), (0.92, 0.48), (0.62, 0.18),
            (0.28, 0.22), (0.54, 0.46), (0.18, 0.54),
        ],
    },
    "Bélgica (Spa-Francorchamps)": {
        "pista": "Circuito de Spa-Francorchamps",
        "pais": "Bélgica",
        "voltas_padrao": 44,
        "pontos": [
            (0.12, 0.82), (0.48, 0.62), (0.32, 0.24), (0.76, 0.14),
            (0.92, 0.46), (0.66, 0.80), (0.32, 0.70),
        ],
    },
    "Hungria": {
        "pista": "Hungaroring",
        "pais": "Hungria",
        "voltas_padrao": 70,
        "pontos": [
            (0.14, 0.82), (0.82, 0.82), (0.92, 0.48), (0.64, 0.18),
            (0.30, 0.22), (0.46, 0.54), (0.16, 0.54),
        ],
    },
    "Países Baixos (Zandvoort)": {
        "pista": "Circuito de Zandvoort",
        "pais": "Países Baixos",
        "voltas_padrao": 72,
        "pontos": [
            (0.12, 0.80), (0.84, 0.78), (0.92, 0.40), (0.56, 0.16),
            (0.20, 0.26), (0.44, 0.52), (0.14, 0.58),
        ],
    },
    "Itália (Monza)": {
        "pista": "Circuito de Monza",
        "pais": "Itália",
        "voltas_padrao": 53,
        "pontos": [
            (0.08, 0.72), (0.92, 0.72), (0.88, 0.28), (0.44, 0.28),
            (0.28, 0.50), (0.10, 0.44),
        ],
    },
    "Espanha (Madri - IFEMA)": {
        "pista": "Circuito de Madring (IFEMA)",
        "pais": "Espanha",
        "voltas_padrao": 57,
        "pontos": [
            (0.12, 0.82), (0.88, 0.82), (0.92, 0.42), (0.58, 0.16),
            (0.32, 0.28), (0.52, 0.54), (0.16, 0.56),
        ],
    },
    "Azerbaijão (Baku)": {
        "pista": "Circuito Urbano de Baku",
        "pais": "Azerbaijão",
        "voltas_padrao": 51,
        "pontos": [
            (0.10, 0.82), (0.92, 0.82), (0.88, 0.24), (0.56, 0.16),
            (0.40, 0.40), (0.14, 0.36),
        ],
    },
    "Barém (Sepang - Malásia)": {
        "pista": "Circuito Internacional de Sepang",
        "pais": "Malásia",
        "voltas_padrao": 56,
        "pontos": [
            (0.12, 0.82), (0.88, 0.80), (0.92, 0.36), (0.56, 0.16),
            (0.22, 0.24), (0.48, 0.52), (0.16, 0.56),
        ],
    },
    "Singapura": {
        "pista": "Circuito Urbano de Marina Bay",
        "pais": "Singapura",
        "voltas_padrao": 62,
        "pontos": [
            (0.14, 0.82), (0.86, 0.82), (0.92, 0.46), (0.64, 0.18),
            (0.34, 0.20), (0.48, 0.48), (0.16, 0.54),
        ],
    },
    "Estados Unidos (Austin)": {
        "pista": "Circuito das Américas",
        "pais": "Estados Unidos",
        "voltas_padrao": 56,
        "pontos": [
            (0.12, 0.82), (0.84, 0.80), (0.90, 0.36), (0.54, 0.16),
            (0.24, 0.28), (0.50, 0.54), (0.16, 0.58),
        ],
    },
    "México": {
        "pista": "Autódromo Hermanos Rodríguez",
        "pais": "México",
        "voltas_padrao": 71,
        "pontos": [
            (0.10, 0.78), (0.92, 0.78), (0.88, 0.28), (0.52, 0.18),
            (0.24, 0.32), (0.46, 0.54), (0.14, 0.54),
        ],
    },
    "Brasil (Interlagos)": {
        "pista": "Autódromo José Carlos Pace",
        "pais": "Brasil",
        "voltas_padrao": 71,
        "pontos": [
            (0.16, 0.84), (0.76, 0.84), (0.86, 0.70), (0.72, 0.58),
            (0.82, 0.42), (0.74, 0.24), (0.54, 0.16), (0.40, 0.28),
            (0.26, 0.20), (0.14, 0.34), (0.16, 0.58), (0.16, 0.74),
        ],
    },
    "Las Vegas": {
        "pista": "Circuito Urbano de Las Vegas",
        "pais": "Estados Unidos",
        "voltas_padrao": 50,
        "pontos": [
            (0.14, 0.88), (0.88, 0.88), (0.88, 0.14), (0.32, 0.14),
            (0.32, 0.54), (0.14, 0.54),
        ],
    },
    "Catar": {
        "pista": "Circuito Internacional de Lusail",
        "pais": "Catar",
        "voltas_padrao": 57,
        "pontos": [
            (0.12, 0.82), (0.90, 0.82), (0.92, 0.38), (0.58, 0.16),
            (0.22, 0.22), (0.44, 0.52), (0.16, 0.56),
        ],
    },
    "Abu Dhabi": {
        "pista": "Circuito de Yas Marina",
        "pais": "Emirados Árabes Unidos",
        "voltas_padrao": 58,
        "pontos": [
            (0.12, 0.82), (0.88, 0.82), (0.92, 0.42), (0.58, 0.16),
            (0.26, 0.24), (0.48, 0.54), (0.16, 0.56),
        ],
    },
}

PILOTOS_BASE_2026 = [
    {"sigla": "NOR", "nome": "Lando Norris", "equipe": "McLaren", "cor": "#FF8000"},
    {"sigla": "PIA", "nome": "Oscar Piastri", "equipe": "McLaren", "cor": "#FF8000"},
    {"sigla": "LEC", "nome": "Charles Leclerc", "equipe": "Ferrari", "cor": "#E8002D"},
    {"sigla": "HAM", "nome": "Lewis Hamilton", "equipe": "Ferrari", "cor": "#E8002D"},
    {"sigla": "RUS", "nome": "George Russell", "equipe": "Mercedes", "cor": "#27F4D2"},
    {"sigla": "ANT", "nome": "Andrea Kimi Antonelli", "equipe": "Mercedes", "cor": "#27F4D2"},
    {"sigla": "VER", "nome": "Max Verstappen", "equipe": "Red Bull Racing", "cor": "#3671C6"},
    {"sigla": "HAD", "nome": "Isack Hadjar", "equipe": "Red Bull Racing", "cor": "#3671C6"},
    {"sigla": "BOR", "nome": "Gabriel Bortoleto", "equipe": "Audi", "cor": "#F50537"},
    {"sigla": "HUL", "nome": "Nico Hülkenberg", "equipe": "Audi", "cor": "#F50537"},
    {"sigla": "ALO", "nome": "Fernando Alonso", "equipe": "Aston Martin", "cor": "#229971"},
    {"sigla": "STR", "nome": "Lance Stroll", "equipe": "Aston Martin", "cor": "#229971"},
    {"sigla": "ALB", "nome": "Alexander Albon", "equipe": "Williams", "cor": "#64C4FF"},
    {"sigla": "SAI", "nome": "Carlos Sainz", "equipe": "Williams", "cor": "#64C4FF"},
    {"sigla": "GAS", "nome": "Pierre Gasly", "equipe": "Alpine", "cor": "#FF87BC"},
    {"sigla": "COL", "nome": "Franco Colapinto", "equipe": "Alpine", "cor": "#FF87BC"},
    {"sigla": "LAW", "nome": "Liam Lawson", "equipe": "Racing Bulls", "cor": "#6692FF"},
    {"sigla": "LIN", "nome": "Arvid Lindblad", "equipe": "Racing Bulls", "cor": "#6692FF"},
    {"sigla": "PER", "nome": "Sergio Pérez", "equipe": "Cadillac", "cor": "#D4AF37"},
    {"sigla": "BOT", "nome": "Valtteri Bottas", "equipe": "Cadillac", "cor": "#D4AF37"},
]

PILOTOS_HAAS_OPCOES = {
    "Bearman + Rafael Câmara": [
        {"sigla": "BEA", "nome": "Oliver Bearman", "equipe": "Haas", "cor": "#B6BABD"},
        {"sigla": "CAM", "nome": "Rafael Câmara", "equipe": "Haas", "cor": "#B6BABD"},
    ],
    "Ocon + Bearman": [
        {"sigla": "OCO", "nome": "Esteban Ocon", "equipe": "Haas", "cor": "#B6BABD"},
        {"sigla": "BEA", "nome": "Oliver Bearman", "equipe": "Haas", "cor": "#B6BABD"},
    ],
}


def extrair_pontos_da_imagem(arquivo_imagem, num_pontos_controle=48):
    """Lê uma imagem de circuito enviada pelo usuário e extrai o contorno fechado normalizado."""
    pil_img = Image.open(arquivo_imagem).convert("RGB")
    img_np = np.array(pil_img)
    cinza = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
    cinza = cv2.GaussianBlur(cinza, (5, 5), 0)

    bordas = np.concatenate([cinza[0, :], cinza[-1, :], cinza[:, 0], cinza[:, -1]])
    fundo_claro = np.mean(bordas) > 127

    tipo_thresh = cv2.THRESH_BINARY_INV if fundo_claro else cv2.THRESH_BINARY
    _, mascara = cv2.threshold(cinza, 0, 255, tipo_thresh + cv2.THRESH_OTSU)

    kernel = np.ones((5, 5), np.uint8)
    mascara = cv2.morphologyEx(mascara, cv2.MORPH_CLOSE, kernel)

    contornos, _ = cv2.findContours(mascara, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    if not contornos:
        return None

    maior_contorno = max(contornos, key=cv2.contourArea)
    if cv2.contourArea(maior_contorno) < 200:
        return None

    pts = maior_contorno.reshape(-1, 2).astype(np.float64)
    h, w = cinza.shape
    pts[:, 0] /= max(w, 1)
    pts[:, 1] /= max(h, 1)

    segmentos = np.linalg.norm(np.diff(pts, axis=0, append=pts[:1]), axis=1)
    dist_acum = np.concatenate([[0.0], np.cumsum(segmentos)])
    perimetro = dist_acum[-1]
    if perimetro <= 0:
        return None

    alvos = np.linspace(0.0, perimetro, num_pontos_controle, endpoint=False)
    xs = np.interp(alvos, dist_acum, np.append(pts[:, 0], pts[0, 0]))
    ys = np.interp(alvos, dist_acum, np.append(pts[:, 1], pts[0, 1]))

    return list(zip(xs.tolist(), ys.tolist()))


def montar_grid_22(opcao_haas: str):
    grid = [dict(p) for p in PILOTOS_BASE_2026]
    grid.extend(dict(p) for p in PILOTOS_HAAS_OPCOES[opcao_haas])
    return grid


def _spline_fechada(pontos_norm, amostras_por_trecho=40):
    pts = np.asarray(pontos_norm, dtype=np.float64)
    n = len(pts)
    curva = []

    for i in range(n):
        p0 = pts[(i - 1) % n]
        p1 = pts[i]
        p2 = pts[(i + 1) % n]
        p3 = pts[(i + 2) % n]

        for step in range(amostras_por_trecho):
            t = step / amostras_por_trecho
            t2 = t * t
            t3 = t2 * t

            pos = 0.5 * (
                (2.0 * p1)
                + (-p0 + p2) * t
                + (2.0 * p0 - 5.0 * p1 + 4.0 * p2 - p3) * t2
                + (-p0 + 3.0 * p1 - 3.0 * p2 + p3) * t3
            )
            curva.append(pos)

    curva = np.asarray(curva, dtype=np.float64)

    min_xy = curva.min(axis=0)
    max_xy = curva.max(axis=0)
    span_xy = np.maximum(max_xy - min_xy, 1e-6)

    # Área bem alargada para acomodar curvas longas (5-6 km) com respiro
    alvo_min = np.array([65.0, 310.0])
    alvo_max = np.array([1015.0, 1580.0])
    alvo_span = alvo_max - alvo_min

    escala = min(alvo_span[0] / span_xy[0], alvo_span[1] / span_xy[1])
    curva_escalada = (curva - min_xy) * escala

    centro_atual = 0.5 * (curva_escalada.min(axis=0) + curva_escalada.max(axis=0))
    centro_alvo = 0.5 * (alvo_min + alvo_max)
    curva_final = curva_escalada + (centro_alvo - centro_atual)

    return curva_final


def _reamostrar_pista(curva_px, num_pontos=700):
    segmentos = np.linalg.norm(np.diff(curva_px, axis=0, append=curva_px[:1]), axis=1)
    dist_acum = np.concatenate([[0.0], np.cumsum(segmentos)])
    perimetro = dist_acum[-1]

    alvos = np.linspace(0.0, perimetro, num_pontos, endpoint=False)
    x_interp = np.interp(alvos, dist_acum, np.append(curva_px[:, 0], curva_px[0, 0]))
    y_interp = np.interp(alvos, dist_acum, np.append(curva_px[:, 1], curva_px[0, 1]))
    return np.column_stack([x_interp, y_interp])


def _carregar_fonte(tamanho):
    candidatos = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ]
    for caminho in candidatos:
        if os.path.exists(caminho):
            return ImageFont.truetype(caminho, tamanho)
    return ImageFont.load_default()


def gerar_frames(
    circuito_nome: str,
    info_circuito: dict,
    grid: list,
    voltas_simuladas: int,
    duracao_seg: int,
    fps: int,
    clima: str,
    vencedor_sigla: str,
):
    amostras = 15 if len(info_circuito["pontos"]) > 20 else 40
    curva_bruta = _spline_fechada(info_circuito["pontos"], amostras_por_trecho=amostras)
    pista_pts = _reamostrar_pista(curva_bruta, num_pontos=700)
    n_pts = len(pista_pts)

    total_frames = max(1, int(duracao_seg * fps))
    num_carros = len(grid)

    velocidades = []
    for idx, piloto in enumerate(grid):
        base = 1.0 + (num_carros - idx) * 0.0025 + ((idx * 7) % 5 - 2) * 0.0012
        if piloto["sigla"] == vencedor_sigla:
            base += 0.018
        if clima == "Chuva":
            base *= 0.90
        velocidades.append(base)

    fonte_titulo = _carregar_fonte(46)
    fonte_sub = _carregar_fonte(28)
    fonte_carro = _carregar_fonte(20)
    fonte_top = _carregar_fonte(24)

    cor_fundo = (12, 16, 24) if clima == "Seco" else (14, 22, 34)
    cor_asfalto = (46, 50, 58) if clima == "Seco" else (36, 44, 56)

    lista_pts = [(float(x), float(y)) for x, y in pista_pts]
    frames = []

    for f_idx in range(total_frames):
        progresso = f_idx / total_frames
        img = Image.new("RGB", (LARGURA, ALTURA), cor_fundo)
        draw = ImageDraw.Draw(img)

        draw.rectangle([48, 52, LARGURA - 48, 225], fill=(22, 28, 40), outline=(65, 78, 102), width=2)
        draw.text((76, 72), circuito_nome.upper(), fill=(255, 255, 255), font=fonte_titulo)
        volta_atual = min(voltas_simuladas, max(1, int(progresso * voltas_simuladas) + 1))
        draw.text(
            (76, 138),
            f"{info_circuito['pista']}  |  Clima: {clima}  |  Volta {volta_atual}/{voltas_simuladas}",
            fill=(185, 198, 220),
            font=fonte_sub,
        )

        # Zebras alternadas proporcionais ao traçado alargado
        for i in range(0, n_pts, 8):
            x, y = lista_pts[i]
            cor_zebra = (225, 45, 45) if (i // 8) % 2 == 0 else (240, 240, 240)
            draw.ellipse([x - 24, y - 24, x + 24, y + 24], fill=cor_zebra)

        # Asfalto da pista com largura equilibrada para curvas sinuosas
        draw.polygon(lista_pts, outline=cor_asfalto)
        draw.line(lista_pts + [lista_pts[0]], fill=cor_asfalto, width=36)
        draw.line(lista_pts + [lista_pts[0]], fill=(72, 78, 90), width=3)

        # Linha de largada / chegada
        x0, y0 = lista_pts[0]
        x1, y1 = lista_pts[1]
        dx, dy = x1 - x0, y1 - y0
        norm = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / norm, dx / norm
        draw.line(
            [(x0 - nx * 22
