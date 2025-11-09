"""
Streamlit dashboard (View). Chama controllers via subprocess ou import.
Execute: streamlit run app/views/dashboard/dashboard.py
"""
import streamlit as st
import subprocess, sys
from pathlib import Path

ROOT = Path(__file__).parents[3]

st.set_page_config(page_title="FarmTech - Dashboard Consolidado")
st.title("FarmTech - Dashboard (Fase 7)")

col1, col2 = st.columns(2)

with col1:
    if st.button("Executar Fase 1"):
        subprocess.Popen([sys.executable, str(ROOT / "orchestrator.py"), "--phase", "1"])
        st.success("Fase 1 iniciada")

with col2:
    if st.button("Executar IoT (Fase 3)"):
        subprocess.Popen([sys.executable, str(ROOT / "orchestrator.py"), "--phase", "3"])
        st.success("Simulação IoT iniciada")

st.markdown("### Logs (simples)")
st.text("Logs aparecerão no terminal onde o orchestrator roda.")
