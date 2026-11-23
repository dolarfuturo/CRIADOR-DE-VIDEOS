import math
import tempfile
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import streamlit as st

try:
    from moviepy import VideoClip
except ImportError:
    from moviepy.editor import VideoClip

try:
    RESAMPLE_BICUBIC = Image.Resampling.BICUBIC
except AttributeError:
    RESAMPLE_BICUBIC = Image.BICUBIC

PILOTOS_DB = {
    "VER": {"nome": "Verstappen", "cor": (30, 65, 175), "detalhe": (235, 30, 45)},
    "NOR": {"nome": "Norris", "cor": (255, 135, 0), "detalhe": (25, 25, 25)},
    "LEC": {"nome": "Leclerc", "cor": (220, 20, 30), "detalhe": (255, 220, 0)},
    "HAM": {"nome": "Hamilton", "cor": (0, 210, 190), "detalhe": (30, 30, 30)},
    "PIA": {"nome": "Piastri", "cor": (255, 135, 0), "detalhe": (240, 240, 240)},
    "RUS": {"nome": "Russell", "cor": (0, 180, 165), "detalhe": (220, 220, 220)},
    "ALO": {"nome": "Alonso", "cor": (0, 111, 98), "detalhe": (190, 215, 0)},
    "SAI": {"nome": "Sainz", "cor": (0, 90, 220), "detalhe": (255, 255, 255)},
}

PONTOS_INTERLAGOS = [
    (0.77, 0.84), (0.80, 0.64), (0.83, 0.44), (0.77, 0.31),
    (0.84, 0.22), (0.78, 0.14), (0.60, 0.12), (0.40, 0.12),
    (0.22, 0.14), (0.16, 0.24), (0.25, 0.34), (0.42, 0.39),
    (0.56, 0.43), (0.60, 0.52), (0.52, 0.58), (0.42, 0.56),
    (0.35, 0.65), (0.44, 0.73), (0.24, 0.76), (0.19, 0.84),
    (0.35, 0.91), (0.60, 0.91), (0.74, 0.89),
]

CLIMAS_DB = {
    "seco": {"label": "SECO", "grama": (46, 115, 48), "asfalto": (58, 60, 66), "chuva": False},
    "chuva": {"label": "CHUVA", "grama": (34, 85, 38), "asfalto": (38, 42, 50), "chuva": True},
}

MAP_W, MAP_H = 8000, 7200
W, H = 1080, 1920
IDX_CHEGADA = 240
LARGURA_PISTA = 170
TEMPO_LUZES = 2.4


def _fonte(tamanho):
    for caminho in [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "DejaVuSans-Bold.ttf",
        "arial.ttf",
    ]:
        try:
            return ImageFont.truetype(caminho, tamanho)
        except Exception:
            pass
    return ImageFont.load_default()


FONT_TAG = _fonte(26)
FONT_PLACAR_TITULO = _fonte(26)
FONT_PLACAR = _fonte(25)
FONT_LEGENDA = _fonte(30)
FONT_BANNER = _fonte(28)
FONT_PISTA_LABEL = _fonte(24)


def _spline_fechada(ancoras, passos=180):
    pts = []
    n = len(ancoras)
    for i in range(n):
        p0 = ancoras[(i - 1) % n]
        p1 = ancoras[i]
        p2 = ancoras[(i + 1) % n]
        p3 = ancoras[(i + 2) % n]
        for s in range(passos):
            t = s / passos
            t2, t3 = t * t, t * t * t
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


def _reamostrar_pista(pts_brutos, num_pts=4600):
    arr = np.array(pts_brutos, dtype=np.float64)
    dists = np.linalg.norm(np.roll(arr, -1, axis=0) - arr, axis=1)
    cum = np.concatenate(([0.0], np.cumsum(dists)))
    alvos = np.linspace(0.0, cum[-1], num_pts, endpoint=False)
    xs = np.interp(alvos, cum, np.append(arr[:, 0], arr[0, 0]))
    ys = np.interp(alvos, cum, np.append(arr[:, 1], arr[0, 1]))
    return list(zip(xs, ys))


def _construir_mapa_interlagos(clima_key):
    clima = CLIMAS_DB[clima_key]
    margem_x, margem_y = 650, 600
    ancoras = [
        (margem_x + nx * (MAP_W - 2 * margem_x), margem_y + ny * (MAP_H - 2 * margem_y))
        for nx, ny in PONTOS_INTERLAGOS
    ]
    pts = _reamostrar_pista(_spline_fechada(ancoras, passos=180), num_pts=4600)
    total_pts = len(pts)

    mapa = Image.new("RGB", (MAP_W, MAP_H), clima["grama"])
    draw = ImageDraw.Draw(mapa)

    rng = np.random.default_rng(42)
    cor_grama_escura = tuple(max(0, c - 10) for c in clima["grama"])
    for _ in range(13000):
        gx = int(rng.integers(0, MAP_W))
        gy = int(rng.integers(0, MAP_H))
        draw.ellipse((gx, gy, gx + 18, gy + 18), fill=cor_grama_escura)

    for i in range(0, total_pts, 18):
        p1 = pts[i]
        p2 = pts[(i + 18) % total_pts]
        cor_z = (220, 35, 35) if (i // 18) % 2 == 0 else (240, 240, 240)
        rz = (LARGURA_PISTA + 24) // 2
        draw.line([p1, p2], fill=cor_z, width=LARGURA_PISTA + 24)
        draw.ellipse((p1[0] - rz, p1[1] - rz, p1[0] + rz, p1[1] + rz), fill=cor_z)

    rp = LARGURA_PISTA // 2
    for p in pts:
        draw.ellipse((p[0] - rp, p[1] - rp, p[0] + rp, p[1] + rp), fill=clima["asfalto"])

    pit_indices = list(range(4180, total_pts)) + list(range(0, 360))
    pit_pts, pit_borda, boxes_pts = [], [], []
    for idx in pit_indices:
        p_cur = pts[idx]
        p_nxt = pts[(idx + 5) % total_pts]
        ang = math.atan2(p_nxt[1] - p_cur[1], p_nxt[0] - p_cur[0])
        perp_esq = ang - math.pi / 2
        pit_pts.append((p_cur[0] + math.cos(perp_esq) * 135, p_cur[1] + math.sin(perp_esq) * 135))
        pit_borda.append((p_cur[0] + math.cos(perp_esq) * 78, p_cur[1] + math.sin(perp_esq) * 78))
        boxes_pts.append((p_cur[0] + math.cos(perp_esq) * 230, p_cur[1] + math.sin(perp_esq) * 230))

    r_pit = 41
    for pp in pit_pts:
        draw.ellipse((pp[0] - r_pit, pp[1] - r_pit, pp[0] + r_pit, pp[1] + r_pit), fill=clima["asfalto"])

    for k in range(len(pit_borda) - 1):
        cor_l = (245, 200, 35) if k < len(pit_borda) // 2 else (235, 235, 240)
        larg_l = 6 if k < len(pit_borda) // 2 else 4
        draw.line([pit_borda[k], pit_borda[k + 1]], fill=cor_l, width=larg_l)

    for idx_b in range(15, len(boxes_pts) - 15, 26):
        bx, by = boxes_pts[idx_b]
        p_a, p_b = boxes_pts[idx_b - 10], boxes_pts[idx_b + 10]
        ang_b = math.atan2(p_b[1] - p_a[1], p_b[0] - p_a[0])
        w_box, h_box = 44, 22
        cantos = [
            (
                bx + math.cos(ang_b) * sx - math.sin(ang_b) * sy,
                by + math.sin(ang_b) * sx + math.cos(ang_b) * sy,
            )
            for sx, sy in [(-w_box, -h_box), (w_box, -h_box), (w_box, h_box), (-w_box, h_box)]
        ]
        draw.polygon(cantos, fill=(70, 76, 88), outline=(110, 118, 132))

    if len(pit_pts) > 20:
        lp = pit_pts[len(pit_pts) // 3]
        draw.text((lp[0] - 55, lp[1] - 14), "PIT LANE", font=FONT_PISTA_LABEL, fill=(255, 225, 80))
    if len(boxes_pts) > 30:
        lb = boxes_pts[len(boxes_pts) // 2]
        draw.text((lb[0] - 42, lb[1] - 14), "BOXES", font=FONT_PISTA_LABEL, fill=(220, 230, 245))

    p_chegada = pts[IDX_CHEGADA]
    p_next = pts[(IDX_CHEGADA + 8) % total_pts]
    ang_c = math.atan2(p_next[1] - p_chegada[1], p_next[0] - p_chegada[0])
    perp_c = ang_c + math.pi / 2
    for row in range(-1, 2):
        for col in range(-6, 7):
            cor_q = (255, 255, 255) if (row + col) % 2 == 0 else (20, 20, 20)
            cx = p_chegada[0] + math.cos(ang_c) * (row * 13) + math.cos(perp_c) * (col * 13)
            cy = p_chegada[1] + math.sin(ang_c) * (row * 13) + math.sin(perp_c) * (col * 13)
            draw.ellipse((cx - 6, cy - 6, cx + 6, cy + 6), fill=cor_q)

    return mapa, pts


def _sprite_carro(cor_principal, cor_detalhe):
    sprite = Image.new("RGBA", (74, 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(sprite)
    for r in [(10, 2, 24, 9), (10, 31, 24, 38), (48, 3, 62, 10), (48, 30, 62, 37)]:
        d.rectangle(r, fill=(18, 18, 20))
    d.rectangle([3, 7, 10, 33], fill=cor_detalhe)
    d.rectangle([62, 6, 70, 34], fill=cor_detalhe)
    d.polygon([(10, 11), (44, 9), (65, 16), (65, 24), (44, 31), (10, 29)], fill=cor_principal)
    d.rectangle([21, 14, 40, 26], fill=cor_detalhe)
    d.ellipse((32, 15, 41, 25), fill=(255, 255, 255))
    return sprite


def gerar_mp4(caminho_saida, clima_key, voltas_alvo, duracao, fps, grid_inicial, vencedor_alvo, ultrapassagens):
    clima = CLIMAS_DB[clima_key]
    mapa_base, pontos_pista = _construir_mapa_interlagos(clima_key)
    total_pts = len(pontos_pista)

    tempo_corrida = max(1.0, duracao - TEMPO_LUZES)
    dist_total = total_pts * voltas_alvo
    vel_media = (dist_total / tempo_corrida) * 0.82

    carros = []
    for pos_g, sigla in enumerate(grid_inicial):
        info = PILOTOS_DB[sigla]
        bonus = 12.0 if sigla == vencedor_alvo else 0.0
        carros.append({
            "sigla": sigla,
            "cor": info["cor"],
            "vel_base": vel_media + bonus - (pos_g * 0.65),
            "faixa_base": -26 if pos_g % 2 == 0 else 26,
            "sprite": _sprite_carro(info["cor"], info["detalhe"]),
            "offset_inicial": -32 - pos_g * 28,
        })

    def impulso_ultra(sigla, frac_c):
        ganho, desloc = 0.0, 0.0
        janela = 0.07
        for atacante, _, momento in ultrapassagens:
            if sigla == atacante:
                delta = frac_c - momento
                if -janela <= delta <= janela:
                    fase = (delta + janela) / (2 * janela)
                    sino = math.sin(fase * math.pi)
                    ganho += sino * (total_pts * 0.045)
                    desloc += math.sin(fase * 2 * math.pi) * 32.0
        return ganho, desloc

    def make_frame(t):
        t_c = max(0.0, t - TEMPO_LUZES)
        frac_c = min(1.0, t_c / tempo_corrida)
        estado = []

        for c in carros:
            if t_c == 0:
                dist, desloc_extra = 0.0, 0.0
            else:
                arrancada = min(1.0, t_c / 1.8)
                dist_base = c["vel_base"] * t_c * (0.45 + 0.55 * arrancada)
                ganho_u, desloc_extra = impulso_ultra(c["sigla"], frac_c)
                dist = dist_base + ganho_u
                if c["sigla"] == vencedor_alvo and frac_c > 0.80:
                    conv = (frac_c - 0.80) / 0.20
                    meta = dist_total * 0.96
                    if dist < meta:
                        dist = dist + (meta - dist) * (conv * 0.35)

            prog = c["offset_inicial"] + dist
            pos_idx = (IDX_CHEGADA + prog) % total_pts
            i0 = int(pos_idx)
            i1 = (i0 + 1) % total_pts
            frac = pos_idx - i0

            p0, p1 = pontos_pista[i0], pontos_pista[i1]
            px = p0[0] + (p1[0] - p0[0]) * frac
            py = p0[1] + (p1[1] - p0[1]) * frac
            ang = math.atan2(p1[1] - p0[1], p1[0] - p0[0])
            perp = ang + math.pi / 2
            desloc = c["faixa_base"] + desloc_extra

            estado.append({
                "sigla": c["sigla"],
                "cor": c["cor"],
                "x": px + math.cos(perp) * desloc,
                "y": py + math.sin(perp) * desloc,
                "ang_rad": ang,
                "ang_deg": -math.degrees(ang),
                "sprite": c["sprite"],
                "prog": prog,
            })

        ranking = sorted(estado, key=lambda item: item["prog"], reverse=True)
        volta_atual = min(voltas_alvo, max(1, int(max(0, ranking[0]["prog"]) // total_pts) + 1))

        cam_x = float(np.mean([r["x"] for r in ranking[:3]]))
        cam_y = float(np.mean([r["y"] for r in ranking[:3]]))
        left = int(max(0, min(MAP_W - W, cam_x - W // 2)))
        top = int(max(0, min(MAP_H - H, cam_y - H // 2)))

        frame = mapa_base.crop((left, top, left + W, top + H)).convert("RGBA")
        overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        od = ImageDraw.Draw(overlay)

        for ec in estado:
            sx = ec["x"] - left
            sy = ec["y"] - top
            if clima["chuva"] and t_c > 0.3:
                for s_step in range(1, 5):
                    bx = sx - math.cos(ec["ang_rad"]) * (30 + s_step * 15)
                    by = sy - math.sin(ec["ang_rad"]) * (30 + s_step * 15)
                    r_sp = 9 + s_step * 3
                    a_sp = max(20, 100 - s_step * 20)
                    od.ellipse((bx - r_sp, by - r_sp, bx + r_sp, by + r_sp), fill=(220, 235, 250, a_sp))

            rot = ec["sprite"].rotate(ec["ang_deg"], expand=True, resample=RESAMPLE_BICUBIC)
            frame.paste(rot, (int(sx - rot.width // 2), int(sy - rot.height // 2)), rot)

            tx, ty = int(sx - 37), int(sy - 58)
            od.rounded_rectangle([tx, ty, tx + 74, ty + 32], radius=8, fill=ec["cor"] + (235,), outline=(255, 255, 255, 230), width=2)
            od.text((tx + 9, ty + 2), ec["sigla"], font=FONT_TAG, fill=(255, 255, 255, 255))

        if clima["chuva"]:
            rng_f = np.random.default_rng(int(t * 100))
            for rx, ry in zip(rng_f.integers(0, W, size=85), rng_f.integers(0, H, size=85)):
                od.line([(int(rx), int(ry)), (int(rx - 8), int(ry + 26))], fill=(200, 225, 255, 105), width=2)

        od.rounded_rectangle([40, 45, 1040, 110], radius=16, fill=(15, 18, 25, 225))
        od.text((65, 62), f"GP DE SAO PAULO - INTERLAGOS - CLIMA: {clima['label']}", font=FONT_BANNER, fill=(255, 255, 255, 255))

        od.rounded_rectangle([40, 130, 320, 495], radius=16, fill=(15, 18, 25, 220))
        od.text((62, 146), f"VOLTA {volta_atual}/{voltas_alvo}", font=FONT_PLACAR_TITULO, fill=(255, 220, 50, 255))
        for pos, r in enumerate(ranking):
            py_row = 192 + pos * 36
            od.rectangle([62, py_row + 4, 78, py_row + 26], fill=r["cor"] + (255,))
            od.text((90, py_row), f"{pos + 1}. {r['sigla']}", font=FONT_PLACAR, fill=(245, 245, 245, 255))

        if t < 3.2:
            od.rounded_rectangle([350, 210, 920, 325], radius=20, fill=(15, 15, 20, 235))
            luzes = min(5, int((t / 1.9) * 5) + 1) if t < TEMPO_LUZES else 0
            for lz in range(5):
                lx = 415 + lz * 110
                cor_l = (240, 25, 25, 255) if lz < luzes else (55, 55, 60, 255)
                od.ellipse((lx - 28, 268 - 28, lx + 28, 268 + 28), fill=cor_l)

        od.rounded_rectangle([50, 1580, 1030, 1735], radius=22, fill=(10, 12, 18, 225))
        if t < TEMPO_LUZES:
            m1, m2 = f"INTERLAGOS ({voltas_alvo} VOLTAS)", f"LARGADA AUTORIZADA ({clima['label']})!"
        elif frac_c > 0.85:
            m1, m2 = f"RETA FINAL! {vencedor_alvo} NA PONTA!", "DISPUTA ATE A BANDEIRADA!"
        else:
            m1, m2 = f"VOLTA {volta_atual}/{voltas_alvo} EM {clima['label']}!", "ULTRAPASSAGENS NO MIOLO DE INTERLAGOS!"

        od.text((85, 1605), m1, font=FONT_LEGENDA, fill=(255, 225, 60, 255))
        od.text((85, 1660), m2, font=FONT_LEGENDA, fill=(255, 255, 255, 255))

        return np.array(Image.alpha_composite(frame, overlay).convert("RGB"))

    clip = VideoClip(make_frame, duration=duracao)
    clip.write_videofile(caminho_saida, fps=fps, codec="libx264", audio=False, logger=None)
    clip.close()
    return caminho_saida


st.set_page_config(page_title="Interlagos 2D Reels", layout="centered")
st.title("Gerador de Corrida 2D — Interlagos")
st.caption("Sem upload de vídeo • Vertical 1080x1920 • Sem áudio")

pilotos = list(PILOTOS_DB.keys())
clima = st.selectbox("Clima", options=list(CLIMAS_DB.keys()), format_func=lambda k: CLIMAS_DB[k]["label"])
voltas = st.number_input("Quantidade de voltas (GP = 71)", min_value=1, max_value=71, value=2, step=1)
vencedor = st.selectbox("Vencedor", options=pilotos, index=pilotos.index("VER"))
grid_txt = st.text_input("Grid inicial", value="NOR, VER, LEC, PIA, HAM, RUS, ALO, SAI")
grid = [x.strip().upper() for x in grid_txt.split(",") if x.strip().upper() in PILOTOS_DB]
if len(grid) < 2:
    grid = pilotos

ultra_sel = st.multiselect(
    "Ultrapassagens",
    options=[
        ("VER", "NOR", 0.30, "VER passa NOR (30%)"),
        ("HAM", "LEC", 0.50, "HAM passa LEC (50%)"),
        ("HAM", "PIA", 0.68, "HAM passa PIA (68%)"),
        ("VER", "HAM", 0.82, "VER assume a ponta (82%)"),
    ],
    default=[
        ("VER", "NOR", 0.30, "VER passa NOR (30%)"),
        ("HAM", "LEC", 0.50, "HAM passa LEC (50%)"),
        ("VER", "HAM", 0.82, "VER assume a ponta (82%)"),
    ],
    format_func=lambda i: i[3],
)
ultras = [(a, b, m) for a, b, m, _ in ultra_sel]

col1, col2 = st.columns(2)
with col1:
    duracao = st.slider("Duração (s)", min_value=8, max_value=90, value=20, step=2)
with col2:
    fps = st.select_slider("FPS", options=[12, 15, 24], value=24)

if st.button("Gerar MP4", type="primary"):
    try:
        with st.spinner("Gerando vídeo..."):
            with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
                out_path = tmp.name
            gerar_mp4(out_path, clima, int(voltas), int(duracao), int(fps), grid, vencedor, ultras)
            with open(out_path, "rb") as f:
                mp4_bytes = f.read()
        st.success("Pronto!")
        st.video(mp4_bytes)
        st.download_button("Baixar MP4", data=mp4_bytes, file_name=f"interlagos_{int(voltas)}v_{clima}_{vencedor}.mp4", mime="video/mp4")
    except Exception as e:
        st.error("Erro durante a geração:")
        st.exception(e)
