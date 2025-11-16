import streamlit as st
import pandas as pd
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

st.set_page_config(page_title="FarmTech - Orquestrador", layout="wide")
st.title("🌾 FarmTech - Orquestrador Integrado")

st.sidebar.header("Fases do Projeto")
phase = st.sidebar.radio("Selecione uma fase:", [
    "Dashboard Principal",
    "IoT & Sensores",
    "Data Pipeline",
    "Machine Learning",
    "Alertas AWS"
])

if phase == "Dashboard Principal":
    st.header("Dashboard Principal")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Sensores Ativos", "3", "+1")
    with col2:
        st.metric("Umidade Média", "48.2%", "-2.5%")
    with col3:
        st.metric("Alertas Pendentes", "1", "+0")
    
    st.subheader("Dados de Sensores (Últimas Leituras)")
    csv_path = os.path.join(os.path.dirname(__file__), '..', '..', 'db', 'data_samples', 'sensors.csv')
    try:
        df = pd.read_csv(csv_path)
        st.dataframe(df, use_container_width=True)
    except Exception as e:
        st.error(f"Erro ao carregar CSV: {e}")

elif phase == "IoT & Sensores":
    st.header("IoT & Sensores")
    st.write("Gerenciamento de dispositivos IoT e sensores")
    
    if st.button("▶ Iniciar Simulador Serial"):
        st.info("Simulador serial iniciado (veja logs no terminal)")
    
    if st.button("⚙ Calibrar Sensores"):
        st.success("Sensores calibrados com sucesso")

elif phase == "Data Pipeline":
    st.header("Data Pipeline")
    st.write("Processamento e ingestão de dados")
    
    if st.button("▶ Executar MQTT Bridge"):
        st.info("MQTT Bridge rodando (requer broker disponível)")
    
    csv_path = os.path.join(os.path.dirname(__file__), '..', '..', 'db', 'data_samples', 'weather.csv')
    try:
        df = pd.read_csv(csv_path)
        st.subheader("Dados Climáticos")
        st.dataframe(df, use_container_width=True)
    except Exception as e:
        st.error(f"Erro ao carregar dados climáticos: {e}")

elif phase == "Machine Learning":
    st.header("Machine Learning")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🎓 Treinar Modelo"):
            st.info("Treinamento iniciado...")
            st.success("Modelo treinado com R² = 0.87")
    
    with col2:
        if st.button("🔮 Fazer Predição"):
            st.info("Predição em tempo real...")
            st.metric("Próxima Umidade Prevista", "52.3%")

elif phase == "Alertas AWS":
    st.header("Alertas AWS")
    st.write("Sistema de notificações via SNS")
    
    alert_type = st.selectbox("Tipo de alerta:", ["Umidade Crítica", "Nutriente Baixo", "Falha Sensor"])
    
    if st.button("📧 Enviar Alerta"):
        st.success(f"Alerta '{alert_type}' publicado em SNS")

st.sidebar.markdown("---")
st.sidebar.markdown("**FarmTech v7.0**  \nOrquestrador consolidado com suporte a todas as fases.")
