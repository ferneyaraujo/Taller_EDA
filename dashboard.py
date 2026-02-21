import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from collections import Counter

# ── Configuración de la página ────────────────────────────────────────────────
st.set_page_config(
    page_title="Netflix – Análisis Exploratorio de Datos",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Estilos globales ──────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
        /* Fondo claro */
        .stApp { background-color: #f7f8fa; }

        /* Barra lateral */
        section[data-testid="stSidebar"] {
            background-color: #ffffff;
            border-right: 1px solid #e0e0e0;
        }

        /* Métricas */
        div[data-testid="stMetric"] {
            background-color: #ffffff;
            border: 1px solid #e3e6ea;
            border-radius: 8px;
            padding: 16px 20px;
        }

        /* Títulos de sección */
        h2, h3 { color: #1a1a2e; font-family: 'Segoe UI', sans-serif; }

        /* Separador personalizado */
        hr { border: none; border-top: 1px solid #dde1e7; margin: 1rem 0; }

        /* Tarjetas informativas */
        .info-card {
            background: #ffffff;
            border-left: 4px solid #c0392b;
            border-radius: 6px;
            padding: 12px 16px;
            margin-bottom: 12px;
            font-size: 0.9rem;
            color: #333;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Paleta de colores neutral y profesional ───────────────────────────────────
PALETTE = [
    "#c0392b", "#2c3e50", "#7f8c8d", "#1a6b8a",
    "#8e6dbf", "#2980b9", "#e67e22", "#27ae60",
    "#d35400", "#16a085",
]

# ── Carga y preparación de datos ─────────────────────────────────────────────
@st.cache_data
def cargar_datos():
    df = pd.read_csv("netflix_titles.csv")

    # Imputación (reproduciendo el EDA)
    df["director"] = df["director"].fillna("Desconocido")
    df["cast"] = df["cast"].fillna("Desconocido")
    df["country"] = df["country"].fillna("Otros")
    df.dropna(subset=["date_added", "rating", "duration"], inplace=True)

    # Columna año de incorporación a Netflix
    df["year_added"] = (
        pd.to_datetime(df["date_added"], format="%B %d, %Y", errors="coerce")
        .dt.year.astype("Int64")
    )

    # Diferencia de años
    df["años_diferencia"] = df["year_added"] - df["release_year"]

    # Duración numérica para películas
    df["duracion_min"] = (
        df["duration"]
        .str.extract(r"(\d+)\s*min")[0]
        .astype(float)
    )

    return df

df = cargar_datos()

# ── Barra lateral ─────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## Filtros")
    st.markdown("---")

    tipo_contenido = st.multiselect(
        "Tipo de contenido",
        options=df["type"].unique().tolist(),
        default=df["type"].unique().tolist(),
    )

    años_disponibles = sorted(df["release_year"].dropna().unique().tolist())
    rango_años = st.slider(
        "Año de lanzamiento",
        min_value=int(min(años_disponibles)),
        max_value=int(max(años_disponibles)),
        value=(2000, int(max(años_disponibles))),
    )

    paises_top = (
        df["country"]
        .str.split(",")
        .explode()
        .str.strip()
        .value_counts()
        .head(30)
        .index.tolist()
    )
    paises_selec = st.multiselect(
        "Paises (análisis geográfico)",
        options=paises_top,
        default=paises_top[:10],
    )

    top_n_generos = st.slider("Numero de generos a mostrar", 5, 20, 10)
    top_n_autores = st.slider("Numero de directores a mostrar", 5, 20, 10)

    st.markdown("---")
    st.markdown(
        "<small style='color:#888'>Datos: Netflix Titles Dataset</small>",
        unsafe_allow_html=True,
    )

# ── Filtro base ───────────────────────────────────────────────────────────────
df_filtrado = df[
    df["type"].isin(tipo_contenido)
    & df["release_year"].between(rango_años[0], rango_años[1])
]

# ── Encabezado ────────────────────────────────────────────────────────────────
st.markdown("# Analisis Exploratorio de Datos – Catalogo Netflix")
st.markdown(
    "Este panel resume el analisis exploratorio del catalogo de Netflix, "
    "respondiendo preguntas clave sobre generos, directores, distribuciones "
    "geograficas y temporales."
)
st.markdown("---")

# ── Metricas resumen ──────────────────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total de titulos", f"{len(df_filtrado):,}")
col2.metric("Peliculas", f"{(df_filtrado['type'] == 'Movie').sum():,}")
col3.metric("Series de TV", f"{(df_filtrado['type'] == 'TV Show').sum():,}")
col4.metric(
    "Paises con produccion",
    df_filtrado["country"].str.split(",").explode().str.strip().nunique(),
)

st.markdown("---")

# ══════════════════════════════════════════════════════════════════════════════
# SECCION 1 – Generos mas populares por pais
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("## 1. Generos mas populares por pais")
st.markdown(
    "Se expande la columna `listed_in` (que contiene multiples generos por "
    "titulo) y se cruza con la columna `country` para identificar cuales generos "
    "predominan en cada pais seleccionado."
)

# Expandir paises y generos
df_exp_pais = df_filtrado.copy()
df_exp_pais["country_list"] = df_exp_pais["country"].str.split(",")
df_exp_pais = df_exp_pais.explode("country_list")
df_exp_pais["country_list"] = df_exp_pais["country_list"].str.strip()
df_exp_pais["genre_list"] = df_exp_pais["listed_in"].str.split(",")
df_exp_pais = df_exp_pais.explode("genre_list")
df_exp_pais["genre_list"] = df_exp_pais["genre_list"].str.strip()

if paises_selec:
    df_pais_filt = df_exp_pais[df_exp_pais["country_list"].isin(paises_selec)]
    heatmap_data = (
        df_pais_filt.groupby(["country_list", "genre_list"])
        .size()
        .reset_index(name="cantidad")
    )

    # Top géneros globales para eje
    top_generos_global = (
        heatmap_data.groupby("genre_list")["cantidad"]
        .sum()
        .nlargest(top_n_generos)
        .index.tolist()
    )
    heatmap_data = heatmap_data[heatmap_data["genre_list"].isin(top_generos_global)]
    pivot = heatmap_data.pivot_table(
        index="country_list", columns="genre_list", values="cantidad", fill_value=0
    )

    fig1 = go.Figure(
        data=go.Heatmap(
            z=pivot.values,
            x=pivot.columns.tolist(),
            y=pivot.index.tolist(),
            colorscale=[
                [0, "#f7f8fa"],
                [0.4, "#f5a9a0"],
                [1, "#c0392b"],
            ],
            showscale=True,
            colorbar=dict(title="Cantidad"),
        )
    )
    fig1.update_layout(
        title="Distribucion de generos por pais (mapa de calor)",
        xaxis_title="Genero",
        yaxis_title="Pais",
        plot_bgcolor="#ffffff",
        paper_bgcolor="#ffffff",
        font=dict(family="Segoe UI", size=12, color="#333"),
        margin=dict(l=20, r=20, t=50, b=20),
        xaxis=dict(tickangle=-35),
        height=480,
    )
    st.plotly_chart(fig1, use_container_width=True)
else:
    st.info("Selecciona al menos un pais en el panel lateral.")

st.markdown("---")

# ══════════════════════════════════════════════════════════════════════════════
# SECCION 2 – Generos mas populares por rating
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("## 2. Generos mas populares por clasificacion de audiencia")
st.markdown(
    "Se muestra la concentracion de generos segun la clasificacion de audiencia "
    "(`rating`). El grafico permite identificar que tipo de contenido predomina "
    "en cada categoria de clasificacion."
)

df_exp_gen = df_filtrado.copy()
df_exp_gen["genre_list"] = df_exp_gen["listed_in"].str.split(",")
df_exp_gen = df_exp_gen.explode("genre_list")
df_exp_gen["genre_list"] = df_exp_gen["genre_list"].str.strip()

generos_freq = (
    df_exp_gen["genre_list"].value_counts().head(top_n_generos).index.tolist()
)
ratings_disponibles = sorted(df_filtrado["rating"].dropna().unique().tolist())
ratings_sel = st.multiselect(
    "Clasificaciones a incluir",
    options=ratings_disponibles,
    default=ratings_disponibles[:8],
    key="ratings_sel",
)

df_gen_rating = df_exp_gen[
    df_exp_gen["genre_list"].isin(generos_freq)
    & df_exp_gen["rating"].isin(ratings_sel)
]
gen_rat = (
    df_gen_rating.groupby(["rating", "genre_list"])
    .size()
    .reset_index(name="cantidad")
)

fig2 = px.bar(
    gen_rat,
    x="rating",
    y="cantidad",
    color="genre_list",
    barmode="stack",
    labels={"rating": "Clasificacion", "cantidad": "Cantidad", "genre_list": "Genero"},
    title="Generos por clasificacion de audiencia",
    color_discrete_sequence=PALETTE,
)
fig2.update_layout(
    plot_bgcolor="#ffffff",
    paper_bgcolor="#ffffff",
    font=dict(family="Segoe UI", size=12, color="#333"),
    legend=dict(title="Genero", orientation="h", y=-0.35),
    margin=dict(l=20, r=20, t=50, b=20),
    height=460,
    xaxis_title="Clasificacion de audiencia",
    yaxis_title="Cantidad de titulos",
)
st.plotly_chart(fig2, use_container_width=True)

st.markdown("---")

# ══════════════════════════════════════════════════════════════════════════════
# SECCION 3 – Directores por año de lanzamiento
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("## 3. Directores con mas titulos por año de lanzamiento")
st.markdown(
    "Se identifican los directores con mayor produccion en el periodo "
    "seleccionado. El grafico muestra la evolucion anual de sus lanzamientos "
    "en el catalogo de Netflix."
)

df_dir = df_filtrado[df_filtrado["director"] != "Desconocido"].copy()
top_directores = (
    df_dir["director"].value_counts().head(top_n_autores).index.tolist()
)
df_dir_top = df_dir[df_dir["director"].isin(top_directores)]
dir_anio = (
    df_dir_top.groupby(["release_year", "director"])
    .size()
    .reset_index(name="titulos")
)

fig3 = px.line(
    dir_anio,
    x="release_year",
    y="titulos",
    color="director",
    markers=True,
    labels={
        "release_year": "Año de lanzamiento",
        "titulos": "Numero de titulos",
        "director": "Director",
    },
    title=f"Titulos por año de lanzamiento – Top {top_n_autores} directores",
    color_discrete_sequence=PALETTE,
)
fig3.update_layout(
    plot_bgcolor="#ffffff",
    paper_bgcolor="#ffffff",
    font=dict(family="Segoe UI", size=12, color="#333"),
    legend=dict(title="Director", orientation="h", y=-0.4),
    margin=dict(l=20, r=20, t=50, b=20),
    height=460,
    xaxis_title="Año de lanzamiento",
    yaxis_title="Numero de titulos",
)
st.plotly_chart(fig3, use_container_width=True)

# Tabla resumen debajo
with st.expander("Ver tabla de directores con mas titulos"):
    tabla_dir = (
        df_dir["director"]
        .value_counts()
        .reset_index()
        .rename(columns={"director": "Director", "count": "Titulos"})
        .head(top_n_autores)
    )
    st.dataframe(tabla_dir, use_container_width=True, hide_index=True)

st.markdown("---")

# ══════════════════════════════════════════════════════════════════════════════
# SECCION 3b – Directores por clasificacion de audiencia
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("## 3b. Relacion entre director y clasificacion de audiencia")
st.markdown(
    "Para los directores con mayor numero de titulos en el catalogo, se muestra "
    "la distribucion de clasificaciones de audiencia (`rating`) asignadas a sus "
    "producciones. Permite identificar si un director tiene preferencia o "
    "especializacion en determinado segmento de publico."
)

# Reutilizamos df_dir y top_directores ya calculados arriba
df_dir_rating = df_dir[df_dir["director"].isin(top_directores)].copy()

col_3b_a, col_3b_b = st.columns([3, 2])

with col_3b_a:
    dir_rat_count = (
        df_dir_rating.groupby(["director", "rating"])
        .size()
        .reset_index(name="titulos")
    )
    # Ordenar directores por total de titulos (mayor arriba)
    orden_dir = (
        dir_rat_count.groupby("director")["titulos"]
        .sum()
        .sort_values(ascending=False)
        .index.tolist()
    )

    fig3b = px.bar(
        dir_rat_count,
        x="titulos",
        y="director",
        color="rating",
        orientation="h",
        barmode="stack",
        category_orders={"director": orden_dir},
        labels={
            "titulos": "Numero de titulos",
            "director": "Director",
            "rating": "Clasificacion",
        },
        title=f"Clasificaciones por director – Top {top_n_autores}",
        color_discrete_sequence=PALETTE,
    )
    fig3b.update_layout(
        plot_bgcolor="#ffffff",
        paper_bgcolor="#ffffff",
        font=dict(family="Segoe UI", size=12, color="#333"),
        legend=dict(title="Clasificacion", orientation="h", y=-0.3),
        margin=dict(l=20, r=20, t=50, b=20),
        height=max(380, len(top_directores) * 36),
        xaxis_title="Numero de titulos",
        yaxis_title="Director",
    )
    st.plotly_chart(fig3b, use_container_width=True)

with col_3b_b:
    # Mapa de calor director × rating
    pivot_dr = (
        df_dir_rating.groupby(["director", "rating"])
        .size()
        .unstack(fill_value=0)
    )
    # Mantener solo ratings con al menos un título
    pivot_dr = pivot_dr.loc[:, pivot_dr.sum() > 0]
    pivot_dr = pivot_dr.loc[orden_dir]  # Mismo orden que el bar

    fig3b_heat = go.Figure(
        data=go.Heatmap(
            z=pivot_dr.values,
            x=pivot_dr.columns.tolist(),
            y=pivot_dr.index.tolist(),
            colorscale=[
                [0, "#f7f8fa"],
                [0.4, "#f5a9a0"],
                [1, "#c0392b"],
            ],
            showscale=True,
            colorbar=dict(title="Titulos"),
            text=pivot_dr.values,
            texttemplate="%{text}",
            textfont=dict(size=10),
        )
    )
    fig3b_heat.update_layout(
        title="Matriz director × clasificacion",
        plot_bgcolor="#ffffff",
        paper_bgcolor="#ffffff",
        font=dict(family="Segoe UI", size=11, color="#333"),
        margin=dict(l=20, r=20, t=50, b=20),
        height=max(380, len(top_directores) * 36),
        xaxis_title="Clasificacion",
        yaxis_title="Director",
        xaxis=dict(tickangle=-30),
    )
    st.plotly_chart(fig3b_heat, use_container_width=True)

st.markdown("---")

# ══════════════════════════════════════════════════════════════════════════════
# SECCION 4 – Duracion por pais
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("## 4. Duracion promedio de peliculas por pais")
st.markdown(
    "Se calcula la duracion promedio (en minutos) de las peliculas producidas "
    "en cada pais. Se toman unicamente los titulos de tipo Movie con duracion "
    "numerica disponible."
)

df_movies = df_filtrado[df_filtrado["type"] == "Movie"].copy()
df_movies = df_movies.dropna(subset=["duracion_min"])
df_movies_pais = df_movies.copy()
df_movies_pais["country_list"] = df_movies_pais["country"].str.split(",")
df_movies_pais = df_movies_pais.explode("country_list")
df_movies_pais["country_list"] = df_movies_pais["country_list"].str.strip()

if paises_selec:
    df_mp_filt = df_movies_pais[df_movies_pais["country_list"].isin(paises_selec)]
else:
    top20_paises = (
        df_movies_pais["country_list"].value_counts().head(20).index.tolist()
    )
    df_mp_filt = df_movies_pais[df_movies_pais["country_list"].isin(top20_paises)]

dur_pais = (
    df_mp_filt.groupby("country_list")["duracion_min"]
    .agg(promedio="mean", mediana="median", cantidad="count")
    .reset_index()
    .rename(columns={"country_list": "Pais"})
    .sort_values("promedio", ascending=True)
)

metrica_dur = st.radio(
    "Metrica a visualizar",
    ["promedio", "mediana"],
    horizontal=True,
    key="metrica_dur",
)

fig4 = px.bar(
    dur_pais,
    x=metrica_dur,
    y="Pais",
    orientation="h",
    text=dur_pais[metrica_dur].round(1),
    labels={metrica_dur: "Duracion (minutos)", "Pais": "Pais"},
    title=f"Duracion {metrica_dur} de peliculas por pais (minutos)",
    color=metrica_dur,
    color_continuous_scale=["#f5a9a0", "#c0392b"],
)
fig4.update_traces(textposition="outside")
fig4.update_layout(
    plot_bgcolor="#ffffff",
    paper_bgcolor="#ffffff",
    font=dict(family="Segoe UI", size=12, color="#333"),
    coloraxis_showscale=False,
    margin=dict(l=20, r=40, t=50, b=20),
    height=max(380, len(dur_pais) * 32),
    xaxis_title="Duracion (minutos)",
    yaxis_title="Pais",
)
st.plotly_chart(fig4, use_container_width=True)

st.markdown("---")

# ══════════════════════════════════════════════════════════════════════════════
# SECCION 5 – Tiempo entre lanzamiento e incorporacion a Netflix
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("## 5. Tiempo transcurrido entre lanzamiento e incorporacion a Netflix")
st.markdown(
    "Se calcula la diferencia entre el año en que el titulo fue lanzado "
    "(`release_year`) y el año en que fue incorporado al catalogo de Netflix "
    "(`date_added`). Un valor positivo indica que el contenido fue agregado "
    "despues de su estreno; un valor negativo podria indicar pre-estrenos."
)

df_tiempo = df_filtrado.dropna(subset=["años_diferencia"]).copy()
df_tiempo = df_tiempo[df_tiempo["años_diferencia"].between(-2, 30)]

col_a, col_b = st.columns(2)

with col_a:
    fig5a = px.histogram(
        df_tiempo,
        x="años_diferencia",
        color="type",
        nbins=32,
        barmode="overlay",
        opacity=0.8,
        labels={"años_diferencia": "Años de diferencia", "type": "Tipo"},
        title="Distribucion de tiempo entre lanzamiento e incorporacion",
        color_discrete_map={"Movie": "#c0392b", "TV Show": "#2c3e50"},
    )
    fig5a.update_layout(
        plot_bgcolor="#ffffff",
        paper_bgcolor="#ffffff",
        font=dict(family="Segoe UI", size=12, color="#333"),
        legend=dict(title="Tipo", orientation="h", y=-0.25),
        margin=dict(l=20, r=20, t=50, b=20),
        height=400,
        xaxis_title="Años transcurridos",
        yaxis_title="Numero de titulos",
    )
    st.plotly_chart(fig5a, use_container_width=True)

with col_b:
    resumen_tipo = (
        df_tiempo.groupby("type")["años_diferencia"]
        .agg(["mean", "median", "std"])
        .reset_index()
        .rename(
            columns={
                "type": "Tipo",
                "mean": "Promedio",
                "median": "Mediana",
                "std": "Desv. Estandar",
            }
        )
    )
    resumen_tipo[["Promedio", "Mediana", "Desv. Estandar"]] = resumen_tipo[
        ["Promedio", "Mediana", "Desv. Estandar"]
    ].round(2)

    fig5b = go.Figure()
    for t, color in zip(
        df_tiempo["type"].unique(), ["#c0392b", "#2c3e50"]
    ):
        subset = df_tiempo[df_tiempo["type"] == t]["años_diferencia"]
        fig5b.add_trace(
            go.Box(
                y=subset,
                name=t,
                marker_color=color,
                boxmean="sd",
                line=dict(width=1.5),
            )
        )
    fig5b.update_layout(
        title="Dispersion del tiempo por tipo de contenido",
        plot_bgcolor="#ffffff",
        paper_bgcolor="#ffffff",
        font=dict(family="Segoe UI", size=12, color="#333"),
        legend=dict(title="Tipo"),
        margin=dict(l=20, r=20, t=50, b=20),
        height=400,
        yaxis_title="Años transcurridos",
    )
    st.plotly_chart(fig5b, use_container_width=True)

# Estadísticas clave debajo
st.markdown("#### Estadisticas de tiempo transcurrido")
st.dataframe(resumen_tipo, use_container_width=True, hide_index=True)

# Evolucion temporal
df_evol = (
    df_tiempo.groupby(["year_added", "type"])["años_diferencia"]
    .mean()
    .reset_index()
    .dropna()
)
df_evol["year_added"] = df_evol["year_added"].astype(int)

fig5c = px.line(
    df_evol,
    x="year_added",
    y="años_diferencia",
    color="type",
    markers=True,
    labels={
        "year_added": "Año de incorporacion a Netflix",
        "años_diferencia": "Diferencia promedio (años)",
        "type": "Tipo",
    },
    title="Evolucion de la diferencia promedio por año de incorporacion",
    color_discrete_map={"Movie": "#c0392b", "TV Show": "#2c3e50"},
)
fig5c.update_layout(
    plot_bgcolor="#ffffff",
    paper_bgcolor="#ffffff",
    font=dict(family="Segoe UI", size=12, color="#333"),
    legend=dict(title="Tipo", orientation="h", y=-0.25),
    margin=dict(l=20, r=20, t=50, b=20),
    height=380,
    xaxis_title="Año de incorporacion",
    yaxis_title="Diferencia promedio (años)",
)
st.plotly_chart(fig5c, use_container_width=True)

st.markdown("---")

# ── Pie de pagina ─────────────────────────────────────────────────────────────
st.markdown(
    "<div style='text-align:center; color:#888; font-size:0.82rem; padding:8px 0'>"
    "Taller EDA – Maestria en Analitica de Datos &nbsp;|&nbsp; "
    "David Merlano – Andrea Rodriguez - Julian Murillo - Ferney Araujo &nbsp;|&nbsp; "
    "Modelos Analiticos – Daniel Romero - 2026"
    "</div>",
    unsafe_allow_html=True,
)
