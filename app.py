import tempfile
import streamlit as st

st.set_page_config(page_title="Estúdio F1 2D - Interlagos", layout="centered")
st.title("Estúdio de Corrida 2D — Interlagos")
st.caption("Escolha a quantidade de voltas e o roteiro da corrida, gere o MP4 e baixe.")

try:
    from simulador import CIRCUITOS_DB, CLIMAS_DB, PILOTOS_DB
except Exception as erro_import:
    st.error("Erro ao importar os dados de simulador.py.")
    st.exception(erro_import)
    st.stop()

pilotos_lista = list(PILOTOS_DB.keys())

circuito = st.selectbox(
    "Circuito",
    options=list(CIRCUITOS_DB.keys()),
    format_func=lambda k: CIRCUITOS_DB[k]["titulo"],
)

clima = st.selectbox(
    "Clima",
    options=list(CLIMAS_DB.keys()),
    format_func=lambda k: CLIMAS_DB[k]["label"],
)

voltas_gp = CIRCUITOS_DB[circuito]["voltas_gp_real"]
modo_voltas = st.radio(
    "Quantidade de voltas",
    options=["Personalizada (Reels / Teste)", f"GP Completo ({voltas_gp} voltas)"],
    horizontal=True,
)

if modo_voltas.startswith("GP Completo"):
    voltas = voltas_gp
    st.info(f"Simulação configurada para o total oficial do GP: {voltas} voltas.")
else:
    voltas = st.number_input(
        f"Escolha quantas voltas simular (1 a {voltas_gp})",
        min_value=1,
        max_value=voltas_gp,
        value=2,
        step=1,
    )

vencedor = st.selectbox(
    "Vencedor escolhido",
    options=pilotos_lista,
    index=pilotos_lista.index("VER") if "VER" in pilotos_lista else 0,
)

grid_texto = st.text_input(
    "Grid inicial (siglas separadas por vírgula)",
    value="NOR, VER, LEC, PIA, HAM, RUS, ALO, SAI",
)
grid_inicial = [
    p.strip().upper()
    for p in grid_texto.split(",")
    if p.strip().upper() in PILOTOS_DB
]
if len(grid_inicial) < 2:
    grid_inicial = pilotos_lista

st.subheader("Ultrapassagens programadas")
ultra_preset = st.multiselect(
    "Selecione lances de ultrapassagem",
    options=[
        ("VER", "NOR", 0.30, "VER passa NOR (30%)"),
        ("HAM", "LEC", 0.50, "HAM passa LEC (50%)"),
        ("HAM", "PIA", 0.68, "HAM passa PIA (68%)"),
        ("VER", "HAM", 0.82, "VER assume a ponta em HAM (82%)"),
    ],
    default=[
        ("VER", "NOR", 0.30, "VER passa NOR (30%)"),
        ("HAM", "LEC", 0.50, "HAM passa LEC (50%)"),
        ("VER", "HAM", 0.82, "VER assume a ponta em HAM (82%)"),
    ],
    format_func=lambda item: item[3],
)
ultrapassagens = [(a, b, m) for a, b, m, _ in ultra_preset]

col1, col2 = st.columns(2)
with col1:
    duracao = st.slider("Duração do vídeo (s)", min_value=8, max_value=90, value=24, step=2)
with col2:
    fps = st.select_slider("FPS", options=[12, 15, 24], value=24)

if st.button("Gerar vídeo da corrida", type="primary"):
    try:
        from simulador import gerar_video_corrida

        with st.spinner(f"Gerando {int(voltas)} volta(s) em {CIRCUITOS_DB[circuito]['titulo']}..."):
            with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
                caminho_mp4 = tmp.name

            gerar_video_corrida(
                caminho_saida=caminho_mp4,
                circuito_key=circuito,
                clima_key=clima,
                voltas_alvo=int(voltas),
                duracao=int(duracao),
                fps=int(fps),
                grid_inicial=grid_inicial,
                vencedor_alvo=vencedor,
                ultrapassagens=ultrapassagens,
            )

            with open(caminho_mp4, "rb") as f:
                video_bytes = f.read()

        st.success("Vídeo gerado com sucesso!")
        st.video(video_bytes)
        st.download_button(
            label="Baixar MP4",
            data=video_bytes,
            file_name=f"{circuito}_{int(voltas)}v_{clima}_{vencedor}.mp4",
            mime="video/mp4",
        )
    except Exception as erro_geracao:
        st.error("Ocorreu um erro ao gerar o vídeo:")
        st.exception(erro_geracao)
