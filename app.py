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
            (0.77, 0.84), (0.80, 0.64), (0.83, 0.44), (0.77, 0.31), (0.84, 0.22),
            (0.78, 0.14), (0.60, 0.12), (0.40, 0.12), (0.22, 0.14), (0.16, 0.24),
            (0.25, 0.34), (0.42, 0.39), (0.56, 0.43), (0.60, 0.52), (0.52, 0.58),
            (0.42, 0.56), (0.35, 0.65), (0.44, 0.73), (0.24, 0.76), (0.19, 0.84),
            (0.35, 0.91), (0.60, 0.91), (0.74, 0.89),
        ],
    },
    "Austrália (Melbourne)": {
        "titulo": "GP DA AUSTRALIA - MELBOURNE",
        "voltas_padrao": 58,
        "pontos_norm": [(0.18, 0.80), (0.58, 0.80), (0.86, 0.66), (0.82, 0.34), (0.56, 0.18), (0.40, 0.36), (0.22, 0.26), (0.12, 0.52)],
    },
    "China (Xangai)": {
        "titulo": "GP DA CHINA - XANGAI",
        "voltas_padrao": 56,
        "pontos_norm": [(0.18, 0.82), (0.62, 0.82), (0.72, 0.68), (0.64, 0.52), (0.46, 0.48), (0.35, 0.60), (0.42, 0.38), (0.72, 0.28), (0.86, 0.18), (0.74, 0.14), (0.38, 0.16), (0.15, 0.24), (0.13, 0.46), (0.24, 0.60)],
    },
    "Japão (Suzuka)": {
        "titulo": "GP DO JAPAO - SUZUKA",
        "voltas_padrao": 53,
        "pontos_norm": [(0.15, 0.78), (0.58, 0.74), (0.76, 0.42), (0.48, 0.20), (0.24, 0.32), (0.46, 0.52), (0.86, 0.44), (0.80, 0.80)],
    },
    "Miami": {
        "titulo": "GP DE MIAMI",
        "voltas_padrao": 57,
        "pontos_norm": [(0.15, 0.82), (0.80, 0.82), (0.88, 0.52), (0.60, 0.42), (0.80, 0.22), (0.32, 0.18), (0.16, 0.44), (0.38, 0.64)],
    },
    "Canadá (Montreal)": {
        "titulo": "GP DO CANADA - MONTREAL",
        "voltas_padrao": 70,
        "pontos_norm": [(0.12, 0.68), (0.88, 0.68), (0.85, 0.34), (0.50, 0.26), (0.32, 0.44), (0.14, 0.36)],
    },
    "Mônaco": {
        "titulo": "GP DE MONACO",
        "voltas_padrao": 78,
        "pontos_norm": [(0.20, 0.82), (0.82, 0.82), (0.88, 0.50), (0.62, 0.20), (0.44, 0.40), (0.24, 0.18), (0.12, 0.46)],
    },
    "Espanha (Barcelona-Catalunha)": {
        "titulo": "GP DA ESPANHA - BARCELONA",
        "voltas_padrao": 66,
        "pontos_norm": [(0.15, 0.80), (0.85, 0.80), (0.88, 0.42), (0.62, 0.20), (0.30, 0.22), (0.16, 0.44), (0.46, 0.56), (0.20, 0.64)],
    },
    "Áustria (Red Bull Ring)": {
        "titulo": "GP DA AUSTRIA - RED BULL RING",
        "voltas_padrao": 71,
        "pontos_norm": [(0.15, 0.82), (0.86, 0.78), (0.70, 0.30), (0.34, 0.20), (0.18, 0.50)],
    },
    "Grã-Bretanha (Silverstone)": {
        "titulo": "GP DA GRA-BRETANHA - SILVERSTONE",
        "voltas_padrao": 52,
        "pontos_norm": [(0.15, 0.78), (0.72, 0.78), (0.88, 0.48), (0.62, 0.20), (0.30, 0.24), (0.54, 0.46), (0.20, 0.54)],
    },
    "Bélgica (Spa-Francorchamps)": {
        "titulo": "GP DA BELGICA - SPA-FRANCORCHAMPS",
        "voltas_padrao": 44,
        "pontos_norm": [(0.15, 0.82), (0.48, 0.62), (0.34, 0.26), (0.74, 0.16), (0.88, 0.46), (0.66, 0.80), (0.34, 0.70)],
    },
    "Hungria": {
        "titulo": "GP DA HUNGRIA - BUDAPESTE",
        "voltas_padrao": 70,
        "pontos_norm": [(0.16, 0.82), (0.80, 0.82), (0.88, 0.48), (0.64, 0.20), (0.32, 0.24), (0.46, 0.54), (0.18, 0.54)],
    },
    "Países Baixos (Zandvoort)": {
        "titulo": "GP DOS PAISES BAIXOS - ZANDVOORT",
        "voltas_padrao": 72,
        "pontos_norm": [(0.15, 0.80), (0.82, 0.78), (0.88, 0.40), (0.56, 0.18), (0.22, 0.28), (0.44, 0.52), (0.16, 0.58)],
    },
    "Itália (Monza)": {
        "titulo": "GP DA ITALIA - MONZA",
        "voltas_padrao": 53,
        "pontos_norm": [(0.12, 0.72), (0.88, 0.72), (0.85, 0.30), (0.44, 0.30), (0.30, 0.50), (0.14, 0.44)],
    },
    "Espanha (Madri - IFEMA)": {
        "titulo": "GP DE MADRI - IFEMA",
        "voltas_padrao": 57,
        "pontos_norm": [(0.15, 0.82), (0.84, 0.82), (0.88, 0.42), (0.58, 0.18), (0.34, 0.30), (0.52, 0.54), (0.18, 0.56)],
    },
    "Azerbaijão (Baku)": {
        "titulo": "GP DO AZERBAIJAO - BAKU",
        "voltas_padrao": 51,
        "pontos_norm": [(0.14, 0.82), (0.88, 0.82), (0.85, 0.26), (0.56, 0.18), (0.40, 0.40), (0.16, 0.36)],
    },
    "Barém (Sepang - Malásia)": {
        "titulo": "GP DE SEPANG",
        "voltas_padrao": 56,
        "pontos_norm": [(0.15, 0.82), (0.84, 0.80), (0.88, 0.36), (0.56, 0.18), (0.24, 0.26), (0.48, 0.52), (0.18, 0.56)],
    },
    "Singapura": {
        "titulo": "GP DE SINGAPURA - MARINA BAY",
        "voltas_padrao": 62,
        "pontos_norm": [(0.16, 0.82), (0.82, 0.82), (0.88, 0.46), (0.64, 0.20), (0.36, 0.22), (0.48, 0.48), (0.18, 0.54)],
    },
    "Estados Unidos (Austin)": {
        "titulo": "GP DOS ESTADOS UNIDOS - AUSTIN",
        "voltas_padrao": 56,
        "pontos_norm": [(0.15, 0.82), (0.82, 0.80), (0.86, 0.36), (0.54, 0.18), (0.26, 0.30), (0.50, 0.54), (0.18, 0.58)],
    },
    "México": {
        "titulo": "GP DO MEXICO",
        "voltas_padrao": 71,
        "pontos_norm": [(0.14, 0.78), (0.88, 0.78), (0.85, 0.30), (0.52, 0.20), (0.26, 0.34), (0.46, 0.54), (0.16, 0.54)],
    },
    "Las Vegas": {
        "titulo": "GP DE LAS VEGAS",
        "voltas_padrao": 50,
        "pontos_norm": [(0.16, 0.86), (0.84, 0.86), (0.84, 0.16), (0.34, 0.16), (0.34, 0.54), (0.16, 0.54)],
    },
    "Catar": {
        "titulo": "GP DO CATAR - LUSAIL",
        "voltas_padrao": 57,
        "pontos_norm": [(0.15, 0.82), (0.86, 0.82), (0.88, 0.38), (0.58, 0.18), (0.24, 0.24), (0.44, 0.52), (0.18, 0.56)],
    },
    "Abu Dhabi": {
        "titulo": "GP DE ABU DHABI - YAS MARINA",
        "voltas_padrao": 58,
        "pontos_norm": [(0.15, 0.82), (0.84, 0.82), (0.88, 0.42), (0.58, 0.18), (0.28, 0.26), (0.48, 0.54), (0.18, 0.56)],
    },
}

PILOTOS_BASE_2026 = [
    {"sigla": "NOR", "nome": "Lando Norris", "equipe": "McLaren", "cor_hex": "#FF8000"},
    {"sigla": "PIA", "nome": "Oscar Piastri", "equipe": "McLaren", "cor_hex": "#FF8000"},
    {"sigla": "LEC", "nome": "Charles Leclerc", "equipe": "Ferrari", "cor_hex": "#E8002D"},
    {"sigla": "HAM", "nome": "Lewis Hamilton", "equipe": "Ferrari", "cor_hex": "#E8002D"},
    {"sigla": "RUS", "nome": "George Russell", "equipe": "Mercedes", "cor_hex": "#27F4D2"},
    {"sigla": "ANT", "nome": "Andrea Kimi Antonelli", "equipe": "Mercedes", "cor_hex": "#27F4D2"},
    {"sigla": "VER", "nome": "Max Verstappen", "equipe": "Red Bull Racing", "cor_hex": "#3671C6"},
    {"sigla": "HAD", "nome": "Isack Hadjar", "equipe": "Red Bull Racing", "cor_hex": "#3671C6"},
    {"sigla": "BOR", "nome": "Gabriel Bortoleto", "equipe": "Audi", "cor_hex": "#F50537"},
    {"sigla": "HUL", "nome": "Nico Hülkenberg", "equipe": "Audi", "cor_hex": "#F50537"},
    {"sigla": "ALO", "nome": "Fernando Alonso", "equipe": "Aston Martin", "cor_hex": "#229971"},
    {"sigla": "STR", "nome": "Lance Stroll", "equipe": "Aston Martin", "cor_hex": "#229971"},
    {"sigla": "ALB", "nome": "Alexander Albon", "equipe": "Williams", "cor_hex": "#64C4FF"},
    {"sigla": "SAI", "nome": "Carlos Sainz", "equipe": "Williams", "cor_hex": "#64C4FF"},
    {"sigla": "GAS", "nome": "Pierre Gasly", "equipe": "Alpine", "cor_hex": "#FF87BC"},
    {"sigla": "COL", "nome": "Franco Colapinto", "equipe": "Alpine", "cor_hex": "#FF87BC"},
    {"sigla": "LAW", "nome": "Liam Lawson", "equipe": "Racing Bulls", "cor_hex": "#6692FF"},
    {"sigla": "LIN", "nome": "Arvid Lindblad", "equipe": "Racing Bulls", "cor_hex": "#6692FF"},
    {"sigla": "PER", "nome": "Sergio Pérez", "equipe": "Cadillac", "cor_hex": "#D4AF37"},
    {"sigla": "BOT", "nome": "Valtteri Bottas", "equipe": "Cadillac", "cor_hex": "#D4AF37"},
]

PILOTOS_HAAS_OPCOES = {
    "Bearman + Rafael Câmara": [
        {"sigla": "BEA", "nome": "Oliver Bearman", "equipe": "Haas", "cor_hex": "#B6BABD"},
        {"sigla": "CAM", "nome": "Rafael Câmara", "equipe": "Haas", "cor_hex": "#B6BABD"},
    ],
    "Ocon + Bearman": [
        {"sigla": "OCO", "nome": "Esteban Ocon", "equipe": "Haas", "cor_hex": "#B6BABD"},
        {"sigla": "BEA", "nome": "Oliver Bearman", "equipe": "Haas", "cor_hex": "#B6BABD"},
    ],
}

CLIMAS_DB = {
    "Seco": {"label": "SECO", "grama": (46, 115, 48), "asfalto": (58, 60, 66), "chuva": False},
    "Chuva": {"label": "CHUVA", "grama": (34, 85, 38), "asfalto": (38, 42, 50), "chuva": True},
}


def montar_grid_22(opcao_haas: str):
    grid = [dict(p) for p in PILOTOS_BASE_2026]
    grid.extend(dict(p) for p in PILOTOS_HAAS_OPCOES[opcao_haas])
    return grid


def spline_catmull_rom_fechada(ancoras, passos_por_segmento=120):
    pts = []
    n = len(ancoras)
    for i in range(n):
        p0 = ancoras[(i - 1) % n]
        p1 = ancoras[i]
        p2 = ancoras[(i + 1) % n]
        p3 = ancoras[(i + 2) % n]
        for s in range(passos_por_segmento):
            t = s / passos_por_segmento
            t2 = t * t
            t3 = t2 * t
            x = 0.5 * (
                (2 * p1[0])
                + (-p0[0] + p2[0]) * t
                + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2
                + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3
            )
            y = 0.5 * (
                (2 * p1[1])
                + (-p0[1] + p2[1]) * t
                + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2
                + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3
            )
            pts.append((x, y))
    return pts


def reamostrar_distancia_uniforme(pts_brutos, num_pontos_uniformes=3200):
    arr = np.array(pts_brutos, dtype=np.float64)
    arr_next = np.roll(arr, -1, axis=0)
    dists = np.linalg.norm(arr_next - arr, axis=1)
    cum_dist = np.concatenate(([0.0], np.cumsum(dists)))
    perimetro_total = cum_dist[-1]

    alvos = np.linspace(0.0, perimetro_total, num_pontos_uniformes, endpoint=False)
    xs = np.interp(alvos, cum_dist, np.append(arr[:, 0], arr[0, 0]))
    ys = np.interp(alvos, cum_dist, np.append(arr[:, 1], arr[0, 1]))
    return list(zip(xs, ys))


def calcular_velocidades_kmh(pontos_pista, dados_clima):
    arr = np.array(pontos_pista, dtype=np.float64)
    n = len(arr)
    vel_kmh = np.zeros(n, dtype=np.float64)
    vel_max = 304.0 if not dados_clima["chuva"] else 262.0
    vel_min = 114.0 if not dados_clima["chuva"] else 94.0

    for i in range(n):
        p_prev = arr[(i - 18) % n]
        p_curr = arr[i]
        p_next = arr[(i + 18) % n]

        v1 = p_curr - p_prev
        v2 = p_next - p_curr
        n1 = np.linalg.norm(v1)
        n2 = np.linalg.norm(v2)
        if n1 < 1e-6 or n2 < 1e-6:
            vel_kmh[i] = vel_max
            continue

        cos_ang = np.clip(np.dot(v1, v2) / (n1 * n2), -1.0, 1.0)
        deflexao = np.arccos(cos_ang)
        fator_reta = np.clip(1.0 - (deflexao / 1.4), 0.0, 1.0)
        vel_kmh[i] = vel_min + (vel_max - vel_min) * (fator_reta ** 1.3)

    kernel = np.ones(11) / 11.0
    return np.convolve(np.pad(vel_kmh, 5, mode="wrap"), kernel, mode="valid")


def desenhar_carro_f1(cor_principal, cor_detalhe):
    cw, ch = 64, 34
    sprite = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    d = ImageDraw.Draw(sprite)
    rodas = [(8, 2, 20, 8), (8, 26, 20, 32), (42, 3, 54, 9), (42, 25, 54, 31)]
    for r in rodas:
        d.rectangle(r, fill=(18, 18, 20))
    d.rectangle([2, 6, 9, 28], fill=cor_detalhe)
    d.rectangle([54, 5, 61, 29], fill=cor_detalhe)
    d.polygon([(9, 9), (38, 7), (56, 13), (56, 21), (38, 27), (9, 25)], fill=cor_principal)
    d.rectangle([18, 12, 35, 22], fill=cor_detalhe)
    d.ellipse((28, 13, 36, 21), fill=(255, 255, 255))
    return sprite


def construir_mapa_base(pontos_norm, dados_clima):
    margem_x, margem_y = 360, 330
    ancoras_px = [
        (margem_x + nx * (MAP_W - 2 * margem_x), margem_y + ny * (MAP_H - 2 * margem_y))
        for nx, ny in pontos_norm
    ]
    passos = 45 if len(ancoras_px) > 20 else 120
    pts_brutos = spline_catmull_rom_fechada(ancoras_px, passos_por_segmento=passos)
    pontos_pista = reamostrar_distancia_uniforme(pts_brutos, num_pontos_uniformes=3200)
    total_pts = len(pontos_pista)
    largura_pista = 128

    mapa_base = Image.new("RGB", (MAP_W, MAP_H), dados_clima["grama"])
    draw = ImageDraw.Draw(mapa_base)

    rng = np.random.default_rng(42)
    cor_grama_escura = tuple(max(0, c - 10) for c in dados_clima["grama"])
    gxs = rng.integers(0, MAP_W, size=5500)
    gys = rng.integers(0, MAP_H, size=5500)
    for gx, gy in zip(gxs, gys):
        draw.ellipse((int(gx), int(gy), int(gx) + 12, int(gy) + 12), fill=cor_grama_escura)

    for i in range(0, total_pts, 16):
        p1 = pontos_pista[i]
        p2 = pontos_pista[(i + 16) % total_pts]
        cor_zebra = (220, 35, 35) if (i // 16) % 2 == 0 else (240, 240, 240)
        r_z = (largura_pista + 18) // 2
        draw.line([p1, p2], fill=cor_zebra, width=largura_pista + 18)
        draw.ellipse((p1[0] - r_z, p1[1] - r_z, p1[0] + r_z, p1[1] + r_z), fill=cor_zebra)

    r_p = largura_pista // 2
    for p in pontos_pista:
        draw.ellipse((p[0] - r_p, p[1] - r_p, p[0] + r_p, p[1] + r_p), fill=dados_clima["asfalto"])

    inicio_pit = int(total_pts * 0.88)
    fim_pit = int(total_pts * 0.08)
    pit_indices = list(range(inicio_pit, total_pts)) + list(range(0, fim_pit))
    pit_pts, pit_borda_pts, boxes_pts = [], [], []

    for idx in pit_indices:
        p_cur = pontos_pista[idx]
        p_nxt = pontos_pista[(idx + 4) % total_pts]
        ang_r = math.atan2(p_nxt[1] - p_cur[1], p_nxt[0] - p_cur[0])
        perp_esq = ang_r - math.pi / 2

        pit_pts.append((p_cur[0] + math.cos(perp_esq) * 96, p_cur[1] + math.sin(perp_esq) * 96))
        pit_borda_pts.append((p_cur[0] + math.cos(perp_esq) * 56, p_cur[1] + math.sin(perp_esq) * 56))
        boxes_pts.append((p_cur[0] + math.cos(perp_esq) * 162, p_cur[1] + math.sin(perp_esq) * 162))

    largura_pit = 60
    r_pit = largura_pit // 2
    for pp in pit_pts:
        draw.ellipse((pp[0] - r_pit, pp[1] - r_pit, pp[0] + r_pit, pp[1] + r_pit), fill=dados_clima["asfalto"])

    for k in range(len(pit_borda_pts) - 1):
        cor_linha = (245, 200, 35) if k < len(pit_borda_pts) // 2 else (235, 235, 240)
        larg_linha = 5 if k < len(pit_borda_pts) // 2 else 3
        draw.line([pit_borda_pts[k], pit_borda_pts[k + 1]], fill=cor_linha, width=larg_linha)

    cor_boxes = (70, 76, 88)
    cor_teto_boxes = (110, 118, 132)
    passo_box = max(12, len(boxes_pts) // 9)
    for idx_b in range(10, max(11, len(boxes_pts) - 10), passo_box):
        bx, by = boxes_pts[idx_b]
        p_a = boxes_pts[idx_b - 6]
        p_b = boxes_pts[idx_b + 6]
        ang_b = math.atan2(p_b[1] - p_a[1], p_b[0] - p_a[0])
        w_box, h_box = 30, 15
        cantos = []
        for sx_c, sy_c in [(-w_box, -h_box), (w_box, -h_box), (w_box, h_box), (-w_box, h_box)]:
            rx = bx + math.cos(ang_b) * sx_c - math.sin(ang_b) * sy_c
            ry = by + math.sin(ang_b) * sx_c + math.cos(ang_b) * sy_c
            cantos.append((rx, ry))
        draw.polygon(cantos, fill=cor_boxes, outline=cor_teto_boxes)

    if len(pit_pts) > 15:
        p_lbl_pit = pit_pts[len(pit_pts) // 3]
        draw.text((p_lbl_pit[0] - 42, p_lbl_pit[1] - 12), "PIT LANE", font=font_pista_label, fill=(255, 225, 80))

    if len(boxes_pts) > 20:
        p_lbl_box = boxes_pts[len(boxes_pts) // 2]
        draw.text((p_lbl_box[0] - 32, p_lbl_box[1] - 12), "BOXES", font=font_pista_label, fill=(220, 230, 245))

    idx_chegada = int(total_pts * 0.05)
    p_chegada = pontos_pista[idx_chegada]
    p_next = pontos_pista[(idx_chegada + 6) % total_pts]
    ang_chegada = math.atan2(p_next[1] - p_chegada[1], p_next[0] - p_chegada[0])
    perp_ang = ang_chegada + math.pi / 2

    for row in range(-1, 2):
        for col in range(-5, 6):
            cor_q = (255, 255, 255) if (row + col) % 2 == 0 else (20, 20, 20)
            cx = p_chegada[0] + math.cos(ang_chegada) * (row * 10) + math.cos(perp_ang) * (col * 10)
            cy = p_chegada[1] + math.sin(ang_chegada) * (row * 10) + math.sin(perp_ang) * (col * 10)
            draw.ellipse((cx - 5, cy - 5, cx + 5, cy + 5), fill=cor_q)

    return mapa_base, pontos_pista, idx_chegada


def renderizar_frames_dinamicos(
    titulo_circuito: str,
    pontos_norm: list,
    grid_22: list,
    voltas_alvo: int,
    duracao: int,
    fps: int,
    clima_nome: str,
    vencedor_sigla: str,
):
    dados_clima = CLIMAS_DB[clima_nome]
    mapa_base, pontos_pista, idx_chegada = construir_mapa_base(pontos_norm, dados_clima)
    total_pts = len(pontos_pista)
    vel_pista_kmh = calcular_velocidades_kmh(pontos_pista, dados_clima)

    grid_ordenado = sorted(
        grid_22,
        key=lambda p: (0 if p["sigla"] == vencedor_sigla else 1),
    )

    tempo_luzes = min(2.4, duracao * 0.2)
    tempo_corrida_total = max(1.0, duracao - tempo_luzes)
    vel_media = ((total_pts * voltas_alvo) / tempo_corrida_total) * 0.78

    carros = []
    num_carros = len(grid_ordenado)
    for pos_g, info in enumerate(grid_ordenado):
        cor_rgb = _hex_para_rgb(info["cor_hex"])
        cor_det = _cor_detalhe_por_equipe(info["equipe"])
        bonus_vel = 12.0 if info["sigla"] == vencedor_sigla else ((num_carros - pos_g) * 0.45 - 4.0)

        carros.append({
            "sigla": info["sigla"],
            "cor": cor_rgb,
            "detalhe": cor_det,
            "grid": pos_g,
            "vel": max(vel_media * 0.75, vel_media + bonus_vel - (pos_g * 0.55)),
            "faixa_base": -20 if pos_g % 2 == 0 else 20,
            "sprite": desenhar_carro_f1(cor_rgb, cor_det),
            "offset_inicial": -24 - pos_g * 14,
        })

    total_frames = max(1, int(duracao * fps))
    historico_rasto = {c["sigla"]: [] for c in carros}
    ordem_anterior = None
    alerta_lance = None
    frames_alerta_restantes = 0
    frames = []

    for f_idx in range(total_frames):
        t = f_idx / fps
        t_corrida = max(0.0, t - tempo_luzes)
        estado_carros = []

        for c in carros:
            if t_corrida == 0:
                dist = 0.0
            else:
                arrancada = min(1.0, t_corrida / 1.8)
                dist = c["vel"] * t_corrida * (0.45 + 0.55 * arrancada)

            progresso_abs = c["offset_inicial"] + dist
            pos_idx = (idx_chegada + progresso_abs) % total_pts
            i0 = int(pos_idx)
            i1 = (i0 + 1) % total_pts
            frac = pos_idx - i0

            p0 = pontos_pista[i0]
            p1 = pontos_pista[i1]
            px = p0[0] + (p1[0] - p0[0]) * frac
            py = p0[1] + (p1[1] - p0[1]) * frac

            ang = math.atan2(p1[1] - p0[1], p1[0] - p0[0])
            perp = ang + math.pi / 2

            desloc = c["faixa_base"]
            if c["grid"] < 2 and t_corrida > 2.0:
                desloc = 24 * math.sin(t_corrida * 0.55 + c["grid"])

            cx = px + math.cos(perp) * desloc
            cy = py + math.sin(perp) * desloc
            kmh_atual = float(vel_pista_kmh[i0]) * (0.985 + (c["grid"] % 4) * 0.008)

            if t_corrida > 0:
                historico_rasto[c["sigla"]].append((cx, cy))
                historico_rasto[c["sigla"]] = historico_rasto[c["sigla"]][-22:]

            estado_carros.append({
                "sigla": c["sigla"],
                "cor": c["cor"],
                "x": cx,
                "y": cy,
                "ang_rad": ang,
                "ang_deg": -math.degrees(ang),
                "sprite": c["sprite"],
                "progresso_abs": progresso_abs,
                "kmh": kmh_atual,
            })

        ranking = sorted(estado_carros, key=lambda item: item["progresso_abs"], reverse=True)
        ordem_atual = [r["sigla"] for r in ranking]

        if ordem_anterior is not None and t_corrida > 0.5:
            for pos_nova, sigla_nova in enumerate(ordem_atual[:8]):
                pos_antiga = ordem_anterior.index(sigla_nova)
                if pos_nova < pos_antiga:
                    vitima = ordem_atual[pos_nova + 1] if pos_nova + 1 < len(ordem_atual) else ""
                    if vitima:
                        alerta_lance = f"ULTRAPASSAGEM: {sigla_nova} SOBRE {vitima} (P{pos_nova + 1})!"
                        frames_alerta_restantes = max(4, int(fps * 1.4))
                        break

        ordem_anterior = ordem_atual
        if frames_alerta_restantes > 0:
            frames_alerta_restantes -= 1
        else:
            alerta_lance = None

        lider = ranking[0]
        volta_atual = min(voltas_alvo, max(1, int(max(0, lider["progresso_abs"]) // total_pts) + 1))

        cam_x = float(np.mean([r["x"] for r in ranking[:3]]))
        cam_y = float(np.mean([r["y"] for r in ranking[:3]]))

        left = int(max(0, min(MAP_W - W, cam_x - W // 2)))
        top = int(max(0, min(MAP_H - H, cam_y - H // 2)))
        frame = mapa_base.crop((left, top, left + W, top + H)).convert("RGBA")

        overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        od = ImageDraw.Draw(overlay)

        for ec in estado_carros:
            trilha = historico_rasto[ec["sigla"]]
            if len(trilha) > 1:
                pts_tela = [(tx - left, ty - top) for tx, ty in trilha]
                od.line(pts_tela, fill=ec["cor"] + (165,), width=5)

        for ec in estado_carros:
            sx_centro = ec["x"] - left
            sy_centro = ec["y"] - top

            if -120 <= sx_centro <= W + 120 and -120 <= sy_centro <= H + 120:
                if dados_clima["chuva"] and t_corrida > 0.3:
                    for s_step in range(1, 5):
                        bx = sx_centro - math.cos(ec["ang_rad"]) * (24 + s_step * 12)
                        by = sy_centro - math.sin(ec["ang_rad"]) * (24 + s_step * 12)
                        raio_spray = 7 + s_step * 2
                        alpha_spray = max(20, 100 - s_step * 20)
                        od.ellipse(
                            (bx - raio_spray, by - raio_spray, bx + raio_spray, by + raio_spray),
                            fill=(220, 235, 250, alpha_spray),
                        )

                rot_sprite = ec["sprite"].rotate(ec["ang_deg"], expand=True, resample=Image.BICUBIC)
                frame.paste(
                    rot_sprite,
                    (int(sx_centro - rot_sprite.width // 2), int(sy_centro - rot_sprite.height // 2)),
                    rot_sprite,
                )

                tag_w, tag_h = 66, 28
                tx = int(sx_centro - tag_w // 2)
                ty = int(sy_centro - 48)
                od.rounded_rectangle(
                    [tx, ty, tx + tag_w, ty + tag_h],
                    radius=7,
                    fill=ec["cor"] + (235,),
                    outline=(255, 255, 255, 230),
                    width=2,
                )
                od.text((tx + 8, ty + 2), ec["sigla"], font=font_tag, fill=(255, 255, 255, 255))

        if dados_clima["chuva"]:
            rng_chuva = np.random.default_rng(int(t * 100))
            xs = rng_chuva.integers(0, W, size=85)
            ys = rng_chuva.integers(0, H, size=85)
            for rx, ry in zip(xs, ys):
                od.line([(int(rx), int(ry)), (int(rx - 8), int(ry + 26))], fill=(200, 225, 255, 105), width=2)

        od.rounded_rectangle([40, 45, 1040, 108], radius=16, fill=(15, 18, 25, 225))
        od.text(
            (65, 62),
            f"{titulo_circuito} - CLIMA: {dados_clima['label']}",
            font=font_banner,
            fill=(255, 255, 255, 255),
        )

        dist_lider = ranking[0]["progresso_abs"]
        vel_media_pts_seg = max((voltas_alvo * total_pts) / tempo_corrida_total, 1.0)

        od.rounded_rectangle([40, 128, 435, 455], radius=16, fill=(15, 18, 25, 220))
        od.text((60, 142), f"VOLTA {volta_atual}/{voltas_alvo}", font=font_placar_titulo, fill=(255, 220, 50, 255))
        for pos, r in enumerate(ranking[:8]):
            py_row = 182 + pos * 32
            if pos == 0:
                gap_txt = "LDR"
            else:
                gap_seg = max(0.05, (dist_lider - r["progresso_abs"]) / vel_media_pts_seg)
                gap_txt = f"+{gap_seg:.2f}s"
            od.rectangle([60, py_row + 4, 74, py_row + 22], fill=r["cor"] + (255,))
            od.text(
                (84, py_row),
                f"{
