from pathlib import Path
from typing import Optional, Tuple
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import time

ROOT = Path(__file__).resolve().parents[3]
SENSORS_CANDIDATES = [
    ROOT / "db" / "data_samples" / "sensors.csv",
    ROOT / "db" / "sensors.csv",
    ROOT / "db" / "sensors_data.csv",
]
WEATHER_CANDIDATES = [
    ROOT / "db" / "data_samples" / "weather.csv",
    ROOT / "db" / "weather.csv",
]
DETECTIONS_CANDIDATES = [
    ROOT / "db" / "data_samples" / "detections.csv",
    ROOT / "db" / "detections.csv",
]

def _read_first_existing(candidates):
    for p in candidates:
        if p.exists():
            try:
                df = pd.read_csv(p)
                return df, p
            except Exception:
                continue
    return None, None

def load_data(database_url: Optional[str] = None) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Carrega sensores, weather e detections. Usa CSV fallback.
    Retorna (df_sensors, df_weather, df_detections). DataFrames podem ser None.
    """
    df_sensors, p1 = _read_first_existing(SENSORS_CANDIDATES)
    df_weather, p2 = _read_first_existing(WEATHER_CANDIDATES)
    df_detections, p3 = _read_first_existing(DETECTIONS_CANDIDATES)

    if df_sensors is not None and 'ts' in df_sensors.columns:
        try:
            df_sensors['ts'] = pd.to_datetime(df_sensors['ts'], errors='coerce')
        except Exception:
            pass

    if df_weather is not None and 'ts' in df_weather.columns:
        try:
            df_weather['ts'] = pd.to_datetime(df_weather['ts'], errors='coerce')
        except Exception:
            pass

    if df_detections is not None and 'ts' in df_detections.columns:
        try:
            df_detections['ts'] = pd.to_datetime(df_detections['ts'], errors='coerce')
        except Exception:
            pass

    return df_sensors, df_weather, df_detections

def plot_humidity_timeseries(df_sensors: pd.DataFrame) -> plt.Figure:
    """
    Plota série temporal de umidade (média por hora).
    """
    fig, ax = plt.subplots(figsize=(9, 3.5))
    if df_sensors is None or df_sensors.empty:
        ax.text(0.5, 0.5, "No sensor data", ha="center", va="center")
        ax.set_axis_off()
        return fig

    df = df_sensors.copy()
    df = df.dropna(subset=['ts', 'umidade'])
    df['hour'] = df['ts'].dt.floor('H')
    series = df.groupby('hour')['umidade'].mean().sort_index()
    ax.plot(series.index.to_pydatetime(), series.values)
    ax.set_title("Umidade média por hora")
    ax.set_xlabel("Hora")
    ax.set_ylabel("Umidade")
    fig.tight_layout()
    return fig

def plot_avg_humidity_per_sensor(df_sensors: pd.DataFrame) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(6, 3.5))
    if df_sensors is None or df_sensors.empty or 'sensor_id' not in df_sensors.columns:
        ax.text(0.5, 0.5, "No sensor data", ha="center", va="center")
        ax.set_axis_off()
        return fig
    df = df_sensors.dropna(subset=['sensor_id', 'umidade'])
    agg = df.groupby('sensor_id')['umidade'].mean().sort_values(ascending=False)
    ax.bar(agg.index.astype(str), agg.values)
    ax.set_title("Umidade média por sensor")
    ax.set_xlabel("Sensor")
    ax.set_ylabel("Umidade média")
    plt.setp(ax.get_xticklabels(), rotation=30, ha='right')
    fig.tight_layout()
    return fig

def plot_nutrient_histogram(df_sensors: pd.DataFrame) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(6, 3.5))
    if df_sensors is None or df_sensors.empty or 'nutriente' not in df_sensors.columns:
        ax.text(0.5, 0.5, "No nutrient data", ha="center", va="center")
        ax.set_axis_off()
        return fig
    arr = pd.to_numeric(df_sensors['nutriente'], errors='coerce').dropna()
    if arr.empty:
        ax.text(0.5, 0.5, "No nutrient data", ha="center", va="center")
        ax.set_axis_off()
        return fig
    ax.hist(arr.values, bins=12)
    ax.set_title("Distribuição de nutrientes")
    ax.set_xlabel("Nível nutriente")
    ax.set_ylabel("Frequência")
    fig.tight_layout()
    return fig

def plot_detections_counts(df_detections: pd.DataFrame) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(6, 3.5))
    if df_detections is None or df_detections.empty or 'categoria' not in df_detections.columns:
        ax.text(0.5, 0.5, "No detections data", ha="center", va="center")
        ax.set_axis_off()
        return fig
    cnt = df_detections['categoria'].value_counts().sort_values(ascending=False)
    ax.bar(cnt.index.astype(str), cnt.values)
    ax.set_title("Contagem por categoria (detecções)")
    ax.set_xlabel("Categoria")
    ax.set_ylabel("Contagem")
    plt.setp(ax.get_xticklabels(), rotation=30, ha='right')
    fig.tight_layout()
    return fig

def render_kpis(df_sensors: pd.DataFrame, df_detections: pd.DataFrame):
    """
    Calcula e exibe KPIs simples: última umidade média, número de sensores, detecções recentes.
    """
    last_umidade = None
    sensors_count = 0
    detections_count = 0
    if df_sensors is not None and not df_sensors.empty:
        if 'umidade' in df_sensors.columns:
            try:
                last_row = df_sensors.sort_values('ts').iloc[-1]
                last_umidade = last_row.get('umidade')
            except Exception:
                last_umidade = None
        if 'sensor_id' in df_sensors.columns:
            sensors_count = int(df_sensors['sensor_id'].nunique())
    if df_detections is not None and not df_detections.empty:
        detections_count = int(len(df_detections))
    c1, c2, c3 = st.columns(3)
    c1.metric("Última umidade (última leitura)", f"{last_umidade}" if last_umidade is not None else "—")
    c2.metric("Sensores únicos (historic)", sensors_count)
    c3.metric("Detecções recentes", detections_count)


def render_visual_panels(database_url: Optional[str] = None):
    """
    Renderiza painéis de visualização no Streamlit.
    Use dentro do app.py, por exemplo na aba 'Dashboard Principal' ou em uma aba separada.
    """
    st.subheader("Visualizações — Painéis e Gráficos")

    df_sensors, df_weather, df_detections = load_data(database_url=database_url)

    # KPIs
    render_kpis(df_sensors, df_detections)
    st.markdown("---")

    row1_col1, row1_col2 = st.columns([2, 1])
    with row1_col1:
        fig1 = plot_humidity_timeseries(df_sensors)
        st.pyplot(fig1)
    with row1_col2:
        fig2 = plot_avg_humidity_per_sensor(df_sensors)
        st.pyplot(fig2)

    row2_col1, row2_col2 = st.columns(2)
    with row2_col1:
        fig3 = plot_nutrient_histogram(df_sensors)
        st.pyplot(fig3)
    with row2_col2:
        fig4 = plot_detections_counts(df_detections)
        st.pyplot(fig4)

    st.markdown("---")
    with st.expander("Mostrar dados brutos: sensores (preview)"):
        if df_sensors is None:
            st.info("Nenhum CSV de sensores encontrado.")
        else:
            st.dataframe(df_sensors.sort_values('ts', ascending=False).head(200), width='stretch')
    with st.expander("Mostrar dados brutos: detecções (preview)"):
        if df_detections is None:
            st.info("Nenhum CSV de detecções encontrado.")
        else:
            st.dataframe(df_detections.sort_values('ts', ascending=False).head(200), width='stretch')

    st.caption(f"Dados carregados: {time.strftime('%Y-%m-%d %H:%M:%S')}")
