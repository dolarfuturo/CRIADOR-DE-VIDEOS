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
            (0.18, 0.78), (0.55, 0.78), (0.85, 0.65), (0.82, 0.35),
            (0.58, 0.22), (0.42, 0.38), (0.25, 0.30), (0.14, 0.52),
        ],
    },
    "China (Xangai)": {
        "pista": "Circuito Internacional de Xangai",
        "pais": "China",
        "voltas_padrao": 56,
        "pontos": [
            (0.18, 0.78), (0.56, 0.78), (0.66, 0.68), (0.62, 0.54),
            (0.48, 0.50), (0.38, 0.58), (0.44, 0.42), (0.68, 0.34),
            (0.84, 0.24), (0.76, 0.16), (0.42, 0.18), (0.16, 0.24),
            (0.14, 0.44), (0.24, 0.56),
        ],
    },
    "Japão (Suzuka)": {
        "pista": "Circuito de Suzuka",
        "pais": "Japão",
        "voltas_padrao": 53,
        "pontos": [
            (0.15, 0.75), (0.55, 0.72), (0.72, 0.45), (0.48, 0.24),
            (0.26, 0.34), (0.46, 0.52), (0.84, 0.46), (0.80, 0.76),
        ],
    },
    "Miami": {
        "pista": "Autódromo Internacional de Miami",
        "pais": "Estados Unidos",
        "voltas_padrao": 57,
        "pontos": [
            (0.15, 0.80), (0.75, 0.80), (0.86, 0.55), (0.62, 0.45),
            (0.78, 0.25), (0.35, 0.22), (0.20, 0.45), (0.38, 0.62),
        ],
    },
    "Canadá (Montreal)": {
        "pista": "Circuito Gilles Villeneuve",
        "pais": "Canadá",
        "voltas_padrao": 70,
        "pontos": [
            (0.12, 0.65), (0.88, 0.65), (0.85, 0.38), (0.52, 0.32),
            (0.35, 0.46), (0.15, 0.40),
        ],
    },
    "Mônaco": {
        "pista": "Circuito de Mônaco",
        "pais": "Mônaco",
        "voltas_padrao": 78,
        "pontos": [
            (0.22, 0.78), (0.78, 0.78), (0.84, 0.52), (0.62, 0.24),
            (0.45, 0.42), (0.26, 0.22), (0.14, 0.48),
        ],
    },
    "Espanha (Barcelona-Catalunha)": {
        "pista": "Circuito de Barcelona-Catalunha",
        "pais": "Espanha",
        "voltas_padrao": 66,
        "pontos": [
            (0.15, 0.76), (0.82, 0.76), (0.86, 0.45), (0.62, 0.25),
            (0.32, 0.26), (0.20, 0.46), (0.45, 0.56), (0.22, 0.62),
        ],
    },
    "Áustria (Red Bull Ring)": {
        "pista": "Red Bull Ring",
        "pais": "Áustria",
        "voltas_padrao": 71,
        "pontos": [
            (0.16, 0.78), (0.84, 0.74), (0.68, 0.36), (0.36, 0.26),
            (0.22, 0.52),
        ],
    },
    "Grã-Bretanha (Silverstone)": {
        "pista": "Circuito de Silverstone",
        "pais": "Reino Unido",
        "voltas_padrao": 52,
        "pontos": [
            (0.16, 0.74), (0.68, 0.74), (0.86, 0.52), (0.62, 0.26),
            (0.32, 0.28), (0.54, 0.48), (0.24, 0.54),
        ],
    },
    "Bélgica (Spa-Francorchamps)": {
        "pista": "Circuito de Spa-Francorchamps",
        "pais": "Bélgica",
        "voltas_padrao": 44,
        "pontos": [
            (0.16, 0.78), (0.48, 0.62), (0.36, 0.32), (0.72, 0.22),
            (0.86, 0.48), (0.64, 0.76), (0.36, 0.68),
        ],
    },
    "Hungria": {
        "pista": "Hungaroring",
        "pais": "Hungria",
        "voltas_padrao": 70,
        "pontos": [
            (0.18, 0.78), (0.76, 0.78), (0.86, 0.50), (0.64, 0.24),
            (0.34, 0.28), (0.46, 0.54), (0.20, 0.54),
        ],
    },
    "Países Baixos (Zandvoort)": {
        "pista": "Circuito de Zandvoort",
        "pais": "Países Baixos",
        "voltas_padrao": 72,
        "pontos": [
            (0.16, 0.76), (0.78, 0.74), (0.86, 0.44), (0.56, 0.24),
            (0.24, 0.32), (0.44, 0.52), (0.18, 0.58),
        ],
    },
    "Itália (Monza)": {
        "pista": "Circuito de Monza",
        "pais": "Itália",
        "voltas_padrao": 53,
        "pontos": [
            (0.12, 0.68), (0.88, 0.68), (0.84, 0.36), (0.46, 0.36),
            (0.32, 0.52), (0.14, 0.48),
        ],
    },
    "Espanha (Madri - IFEMA)": {
        "pista": "Circuito de Madring (IFEMA)",
        "pais": "Espanha",
        "voltas_padrao": 57,
        "pontos": [
            (0.16, 0.78), (0.82, 0.78), (0.86, 0.46), (0.58, 0.24),
            (0.36, 0.34), (0.52, 0.54), (0.22, 0.56),
        ],
    },
    "Azerbaijão (Baku)": {
        "pista": "Circuito Urbano de Baku",
        "pais": "Azerbaijão",
        "voltas_padrao": 51,
        "pontos": [
            (0.14, 0.78), (0.86, 0.78), (0.84, 0.32), (0.56, 0.24),
            (0.42, 0.44), (0.18, 0.42),
        ],
    },
    "Barém (Sepang - Malásia)": {
        "pista": "Circuito Internacional de Sepang",
        "pais": "Malásia",
        "voltas_padrao": 56,
        "pontos": [
            (0.16, 0.78), (0.82, 0.76), (0.86, 0.42), (0.56, 0.24),
            (0.26, 0.30), (0.48, 0.52), (0.20, 0.56),
        ],
    },
    "Singapura": {
        "pista": "Circuito Urbano de Marina Bay",
        "pais": "Singapura",
        "voltas_padrao": 62,
        "pontos": [
            (0.18, 0.78), (0.80, 0.78), (0.86, 0.50), (0.64, 0.24),
            (0.38, 0.26), (0.48, 0.50), (0.20, 0.54),
        ],
    },
    "Estados Unidos (Austin)": {
        "pista": "Circuito das Américas",
        "pais": "Estados Unidos",
        "voltas_padrao": 56,
        "pontos": [
            (0.16, 0.78), (0.78, 0.76), (0.84, 0.42), (0.54, 0.24),
            (0.28, 0.34), (0.50, 0.54), (0.22, 0.58),
        ],
    },
    "México": {
        "pista": "Autódromo Hermanos Rodríguez",
        "pais": "México",
        "voltas_padrao": 71,
        "pontos": [
            (0.14, 0.74), (0.86, 0.74), (0.82, 0.36), (0.52, 0.26),
            (0.28, 0.38), (0.46, 0.54), (0.18, 0.54),
        ],
    },
    "Brasil (Interlagos)": {
        "pista": "Autódromo José Carlos Pace",
        "pais": "Brasil",
        "voltas_padrao": 71,
        "pontos": [
            (0.18, 0.78), (0.76, 0.78), (0.82, 0.48), (0.52, 0.26),
            (0.26, 0.34), (0.42, 0.54), (0.20, 0.58),
        ],
    },
    "Las Vegas": {
        "pista": "Circuito Urbano de Las Vegas",
        "pais": "Estados Unidos",
        "voltas_padrao": 50,
        "pontos": [
            (0.18, 0.84), (0.82, 0.84), (0.82, 0.20), (0.36, 0.20),
            (0.36, 0.56), (0.18, 0.56),
        ],
    },
    "Catar": {
        "pista": "Circuito Internacional de Lusail",
        "pais": "Catar",
        "voltas_padrao": 57,
        "pontos": [
            (0.16, 0.78), (0.84, 0.78), (0.86, 0.44), (0.58, 0.24),
            (0.26, 0.28), (0.44, 0.52), (0.20, 0.56),
        ],
    },
    "Abu Dhabi": {
        "pista": "Circuito de Yas Marina",
        "pais": "Emirados Árabes Unidos",
        "voltas_padrao": 58,
        "pontos": [
            (0.16, 0.78), (0.82, 0.78), (0.86, 0.46), (0.58, 0.24),
            (0.30, 0.30), (0.48, 0.54), (0.22, 0.56),
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

    # Detecta automaticamente se o fundo é claro ou escuro pela borda da imagem
    bordas = np.concatenate([cinza[0, :], cinza[-1, :], cinza[:, 0], cinza[:, -1]])
    fundo_claro = np.mean(bordas) > 127

    tipo_thresh = cv2.THRESH_BINARY_INV if fundo_claro else cv2.THRESH_BINARY
    _, mascara = cv2.threshold(cinza, 0, 255, tipo_thresh + cv2.THRESH_OTSU)

    # Fecha pequenas falhas na linha da pista
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

    # Reamostra ao longo do perímetro para suavizar
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


def _spline_fechada(pontos_norm, amostras_por_trecho=45):
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

    alvo_min = np.array([120.0, 440.0])
    alvo_max = np.array([960.0, 1440.0])
    alvo_span = alvo_max - alvo_min

    escala = min(alvo_span[0] / span_xy[0], alvo_span[1] / span_xy[1])
    curva_escalada = (curva - min_xy) * escala

    centro_atual = 0.5 * (curva_escalada.min(axis=0) + curva_escalada.max(axis=0))
    centro_alvo = 0.5 * (alvo_min + alvo_max)
    curva_final = curva_escalada + (centro_alvo - centro_atual)

    return curva_final


def _reamostrar_pista(curva_px, num_pontos=600):
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
    pista_pts = _reamostrar_pista(curva_bruta, num_pontos=600)
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

        for i in range(0, n_pts, 6):
            x, y = lista_pts[i]
            cor_zebra = (225, 45, 45) if (i // 6) % 2 == 0 else (240, 240, 240)
            draw.ellipse([x - 32, y - 32, x + 32, y + 32], fill=cor_zebra)

        draw.polygon(lista_pts, outline=cor_asfalto)
        draw.line(lista_pts + [lista_pts[0]], fill=cor_asfalto, width=46)
        draw.line(lista_pts + [lista_pts[0]], fill=(72, 78, 90), width=4)

        x0, y0 = lista_pts[0]
        x1, y1 = lista_pts[1]
        dx, dy = x1 - x0, y1 - y0
        norm = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / norm, dx / norm
        draw.line(
            [(x0 - nx * 26, y0 - ny * 26), (x0 + nx * 26, y0 + ny * 26)],
            fill=(255, 255, 255),
            width=8,
        )

        posicoes_carros = []
        for idx, piloto in enumerate(grid):
            offset_grid = (num_carros - idx) * 4.5
            distancia_total = (progresso * voltas_simuladas * n_pts * velocidades[idx]) - offset_grid
            indice_pista = int(distancia_total) % n_pts

            lateral = ((idx % 3) - 1) * 7.5
            px, py = lista_pts[indice_pista]
            next_px, next_py = lista_pts[(indice_pista + 1) % n_pts]
            tdx, tdy = next_px - px, next_py - py
            tnorm = math.hypot(tdx, tdy) or 1.0
            cx = px + (-tdy / tnorm) * lateral
            cy = py + (tdx / tnorm) * lateral

            posicoes_carros.append((distancia_total, idx, piloto, cx, cy))

        for _, _, piloto, cx, cy in posicoes_carros:
            r = 13
            draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=piloto["cor"], outline=(255, 255, 255), width=2)
            draw.text((cx + 15, cy - 11), piloto["sigla"], fill=(255, 255, 255), font=fonte_carro)

        ranking = sorted(posicoes_carros, key=lambda item: item[0], reverse=True)
        draw.rectangle([48, 1510, LARGURA - 48, 1865], fill=(22, 28, 40), outline=(65, 78, 102), width=2)
        draw.text((76, 1528), "TOP 6 NA PISTA", fill=(255, 215, 64), font=fonte_top)

        for pos_idx, (_, _, piloto, _, _) in enumerate(ranking[:6], start=1):
            col = 0 if pos_idx <= 3 else 1
            linha = (pos_idx - 1) % 3
            rx = 76 + col * 465
            ry = 1575 + linha * 85
            draw.rectangle([rx, ry, rx + 435, ry + 68], fill=(32, 40, 56), outline=piloto["cor"], width=3)
            draw.text(
                (rx + 16, ry + 18),
                f"P{pos_idx}  {piloto['sigla']}  -  {piloto['equipe']}",
                fill=(255, 255, 255),
                font=fonte_top,
            )

        frames.append(np.asarray(img, dtype=np.uint8))

    return frames


st.title("Gerador de Corridas F1 2D (MP4)")
st.caption("Temporada 2026 • 23 circuitos • 22 carros • Renderização vertical 1080x1920")

circuito_nome = st.selectbox("Circuito", list(CIRCUITOS_2026.keys()))
info_circuito = dict(CIRCUITOS_2026[circuito_nome])

# Local para enviar a imagem do circuito e extrair o traçado automaticamente
imagem_circuito = st.file_uploader(
    "Ou envie uma imagem do circuito (PNG/JPG) para traçar automaticamente",
    type=["png", "jpg", "jpeg"],
)

if imagem_circuito is not None:
    pontos_extraidos = extrair_pontos_da_imagem(imagem_circuito)
    if pontos_extraidos:
        nome_custom = st.text_input("Nome do circuito enviado", value=circuito_nome)
        circuito_nome = nome_custom.strip() or circuito_nome
        info_circuito["pontos"] = pontos_extraidos
        info_circuito["pista"] = "Traçado extraído da imagem"
        st.success("Traçado lido da imagem com sucesso!")
    else:
        st.error("Não foi possível detectar o contorno fechado da pista nessa imagem. Tente uma imagem mais limpa.")

opcao_haas = st.selectbox("Dupla da Haas", list(PILOTOS_HAAS_OPCOES.keys()))
grid_22 = montar_grid_22(opcao_haas)

col1, col2 = st.columns(2)
with col1:
    voltas = st.number_input(
        "Voltas simuladas",
        min_value=1,
        max_value=80,
        value=min(15, info_circuito["voltas_padrao"]),
    )
    duracao = st.slider("Duração do vídeo (seg)", min_value=4, max_value=20, value=8)

with col2:
    clima = st.selectbox("Clima", ["Seco", "Chuva"])
    fps = st.selectbox("FPS", [15, 24, 30], index=0)

siglas_grid = [p["sigla"] for p in grid_22]
vencedor = st.selectbox("Vencedor simulado", siglas_grid, index=0)

if st.button("Gerar MP4", type="primary"):
    with st.spinner("Renderizando frames e montando o vídeo MP4..."):
        frames = gerar_frames(
            circuito_nome=circuito_nome,
            info_circuito=info_circuito,
            grid=grid_22,
            voltas_simuladas=int(voltas),
            duracao_seg=int(duracao),
            fps=int(fps),
            clima=clima,
            vencedor_sigla=vencedor,
        )

        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
            caminho_mp4 = tmp.name

        try:
            clip = ImageSequenceClip(frames, fps=int(fps))
            clip.write_videofile(
                caminho_mp4,
                codec="libx264",
                audio=False,
                logger=None,
            )
            clip.close()

            with open(caminho_mp4, "rb") as f:
                video_bytes = f.read()

            st.success("Vídeo gerado com sucesso!")
            st.video(video_bytes)
            st.download_button(
                label="Baixar MP4",
                data=video_bytes,
                file_name=f"f1_2026_{circuito_nome.lower().replace(' ', '_')}.mp4",
                mime="video/mp4",
            )
        finally:
            if os.path.exists(caminho_mp4):
                os.remove(caminho_mp4)
