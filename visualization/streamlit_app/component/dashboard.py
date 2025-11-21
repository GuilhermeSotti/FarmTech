# visualization/streamlit_app/components/dashboard.py
"""
dashboard.py
Módulo responsável pelo Dashboard Principal do FarmTech.
Fornece:
 - compute_financials(metrics, params)
 - render_dashboard(database_url=None)

Como usar:
from visualization.components.dashboard import render_dashboard
render_dashboard(database_url=...)  # em seu app.py
"""

from typing import Dict, Any, Tuple, Optional
from dataclasses import dataclass, asdict
import streamlit as st
import pandas as pd
import time
from pathlib import Path
from ml.train_model import fetch_metrics


@dataclass
class FinancialParams:
    area_ha: float = 1.0
    yield_per_ha: float = 5000.0
    unit_name: str = "kg"
    price_per_unit: float = 1.5
    cost_per_ha: float = 200.0
    fixed_costs: float = 100.0
    sensor_cost_unit: float = 25.0
    other_variable_costs: float = 0.0
    contingency_pct: float = 5.0

def compute_financials(metrics: Dict[str, Any], params: FinancialParams) -> Dict[str, Any]:
    """
    Calcula todas as métricas financeiras a partir das métricas do sistema e parâmetros agrícolas.
    Retorna um dicionário com valores e também dataframe 'summary_df' no campo 'df_summary'.
    """
    # extrai sensores ativos (defensivo)
    try:
        sensors_active_count = int(metrics.get("sensors_active", 0) or 0)
    except Exception:
        sensors_active_count = 0

    # cálculos principais
    area_ha = float(params.area_ha or 0.0)
    yield_per_ha = float(params.yield_per_ha or 0.0)
    production_total = area_ha * yield_per_ha  # unidades (kg por exemplo)

    price_per_unit = float(params.price_per_unit or 0.0)
    revenue_total = production_total * price_per_unit

    variable_costs_total = (params.cost_per_ha * area_ha) + float(params.other_variable_costs or 0.0)
    sensor_total_cost = params.sensor_cost_unit * sensors_active_count
    total_costs = variable_costs_total + params.fixed_costs + sensor_total_cost
    contingency_amount = (params.contingency_pct / 100.0) * total_costs
    total_costs_with_contingency = total_costs + contingency_amount

    profit_total = revenue_total - total_costs_with_contingency
    profit_per_ha = profit_total / area_ha if area_ha > 0 else 0.0
    profit_margin = (profit_total / revenue_total * 100.0) if revenue_total > 0 else None
    roi = (profit_total / total_costs_with_contingency * 100.0) if total_costs_with_contingency > 0 else None

    revenue_per_sensor = revenue_total / sensors_active_count if sensors_active_count > 0 else None
    cost_per_sensor = total_costs_with_contingency / sensors_active_count if sensors_active_count > 0 else None
    production_per_sensor = production_total / sensors_active_count if sensors_active_count > 0 else None

    # montar resumo como dataframe (valores legíveis)
    summary = {
        "Métrica": [
            "Área (ha)",
            f"Produtividade ({params.unit_name}/ha)",
            "Produção total",
            f"Preço por {params.unit_name}",
            "Receita total",
            "Custo variável total",
            "Custo por sensor (total)",
            "Custos fixos",
            "Contingência (%)",
            "Contingência (valor)",
            "Custo total (+conting.)",
            "Lucro total",
            "Lucro / ha",
            "ROI (%)",
            "Sensores usados"
        ],
        "Valor": [
            round(area_ha, 6),
            round(yield_per_ha, 3),
            f"{production_total:,.0f} {params.unit_name}",
            round(price_per_unit, 4),
            f"{revenue_total:,.2f}",
            f"{variable_costs_total:,.2f}",
            f"{sensor_total_cost:,.2f}",
            f"{params.fixed_costs:,.2f}",
            f"{params.contingency_pct:.1f}%",
            f"{contingency_amount:,.2f}",
            f"{total_costs_with_contingency:,.2f}",
            f"{profit_total:,.2f}",
            f"{profit_per_ha:,.2f}",
            f"{roi:.2f}%" if roi is not None else "—",
            sensors_active_count
        ]
    }
    df_summary = pd.DataFrame(summary)

    result = {
        "sensors_active_count": sensors_active_count,
        "production_total": production_total,
        "revenue_total": revenue_total,
        "variable_costs_total": variable_costs_total,
        "sensor_total_cost": sensor_total_cost,
        "total_costs": total_costs,
        "contingency_amount": contingency_amount,
        "total_costs_with_contingency": total_costs_with_contingency,
        "profit_total": profit_total,
        "profit_per_ha": profit_per_ha,
        "profit_margin": profit_margin,
        "roi": roi,
        "revenue_per_sensor": revenue_per_sensor,
        "cost_per_sensor": cost_per_sensor,
        "production_per_sensor": production_per_sensor,
        "df_summary": df_summary
    }
    return result

def _display_top_metrics(metrics: Dict[str, Any]):
    """Exibe os três widgets principais do dashboard (sensores, umidade, alertas)."""
    sensores_ativos = metrics.get("sensors_active", 0)
    umidade_media = metrics.get("umidade_media", None)
    alertas_pendentes = metrics.get("alerts_pending", 0)

    col1, col2, col3 = st.columns(3)
    col1.metric("Sensores Ativos", int(sensores_ativos))
    col2.metric("Umidade Média", f"{umidade_media}%" if umidade_media is not None else "—")
    col3.metric("Alertas Pendentes", int(alertas_pendentes))

def render_dashboard(database_url: Optional[str] = None):
    """
    Renderiza todo o Dashboard Principal no Streamlit.
    Retorna (metrics, financials) para uso programático se necessário.
    """
    st.header("Dashboard Principal — Dados Reais e Cálculos Econômicos")

    # botão para forçar refresh - limpa cache do fetch_metrics
    if st.button("🔄 Atualizar métricas"):
        try:
            st.cache_data.clear()
        except Exception:
            pass

    with st.spinner("Consultando métricas..."):
        metrics = fetch_metrics(database_url)

    # Exibir top metrics
    _display_top_metrics(metrics)
    st.markdown("---")
    st.subheader("Parâmetros agrícolas (insira os valores para os cálculos)")

    # UI inputs (mantidos em session_state para persistência entre reruns)
    if "dashboard_params" not in st.session_state:
        st.session_state["dashboard_params"] = FinancialParams()  # defaults

    cols = st.columns(3)
    with cols[0]:
        st.session_state.dashboard_params.area_ha = st.number_input(
            "Área total (ha)",
            min_value=0.0,
            value=float(st.session_state.dashboard_params.area_ha),
            step=0.1,
            format="%.3f"
        )
        st.session_state.dashboard_params.yield_per_ha = st.number_input(
            "Produtividade esperada (kg/ha)",
            min_value=0.0,
            value=float(st.session_state.dashboard_params.yield_per_ha),
            step=100.0
        )
        st.session_state.dashboard_params.unit_name = st.text_input(
            "Unidade de produção",
            value=st.session_state.dashboard_params.unit_name
        )

    with cols[1]:
        st.session_state.dashboard_params.price_per_unit = st.number_input(
            f"Preço por {st.session_state.dashboard_params.unit_name}",
            min_value=0.0,
            value=float(st.session_state.dashboard_params.price_per_unit),
            step=0.01
        )
        st.session_state.dashboard_params.cost_per_ha = st.number_input(
            "Custo variável por ha",
            min_value=0.0,
            value=float(st.session_state.dashboard_params.cost_per_ha),
            step=1.0
        )
        st.session_state.dashboard_params.fixed_costs = st.number_input(
            "Custos fixos (total)",
            min_value=0.0,
            value=float(st.session_state.dashboard_params.fixed_costs),
            step=1.0
        )

    with cols[2]:
        st.session_state.dashboard_params.sensor_cost_unit = st.number_input(
            "Custo por sensor (amortizado)",
            min_value=0.0,
            value=float(st.session_state.dashboard_params.sensor_cost_unit),
            step=1.0
        )
        st.session_state.dashboard_params.other_variable_costs = st.number_input(
            "Outros custos variáveis (total)",
            min_value=0.0,
            value=float(st.session_state.dashboard_params.other_variable_costs),
            step=1.0
        )
        st.session_state.dashboard_params.contingency_pct = st.slider(
            "Reserva/Contingência (%)",
            min_value=0,
            max_value=50,
            value=int(st.session_state.dashboard_params.contingency_pct)
        )

    # compute financials
    params = st.session_state.dashboard_params
    fin = compute_financials(metrics, params)

    # exibicao principal
    st.markdown("---")
    st.subheader("Resultados Financeiros")
    r1, r2, r3 = st.columns(3)
    r1.metric("Produção Total", f"{fin['production_total']:,.0f} {params.unit_name}")
    r2.metric("Receita Estimada", f"{fin['revenue_total']:,.2f}")
    r3.metric("Custo Total (+cont.)", f"{fin['total_costs_with_contingency']:,.2f}")

    r4, r5, r6 = st.columns(3)
    r4.metric("Lucro Total", f"{fin['profit_total']:,.2f}")
    r5.metric("Lucro por ha", f"{fin['profit_per_ha']:,.2f}")
    r6.metric("ROI (%)", f"{fin['roi']:.2f}%" if fin['roi'] is not None else "—")

    st.markdown("#### Detalhes por sensor")
    st.write(f"Sensores ativos usados no cálculo: **{fin['sensors_active_count']}**")
    st.write(f"Receita por sensor: **{fin['revenue_per_sensor']:,.2f}**" if fin['revenue_per_sensor'] is not None else "—")
    st.write(f"Custo por sensor: **{fin['cost_per_sensor']:,.2f}**" if fin['cost_per_sensor'] is not None else "—")
    st.write(f"Produção por sensor: **{fin['production_per_sensor']:,.0f} {params.unit_name}**" if fin['production_per_sensor'] is not None else "—")

    # tabela resumo
    st.markdown("---")
    st.subheader("Resumo")
    df_summary = fin['df_summary']
    st.dataframe(df_summary, width='stretch')

    # últimas leituras
    st.markdown("---")
    st.subheader("Últimas leituras (fonte)")
    latest = metrics.get("latest_readings")
    if latest is None or latest.empty:
        st.info("Nenhuma leitura disponível (DB ou CSV).")
    else:
        if 'ts' in latest.columns:
            latest = latest.copy()
            latest['ts'] = pd.to_datetime(latest['ts'], errors='coerce').astype(str)
        st.dataframe(latest, width='stretch')

    # ações: exportar CSV / copiar preview
    cols_actions = st.columns(2)
    if cols_actions[0].button("💾 Exportar resumo CSV"):
        repdir = Path.cwd() / "reports"
        repdir.mkdir(exist_ok=True)
        fname = repdir / f"farmtech_summary_{int(time.time())}.csv"
        df_summary.to_csv(fname, index=False)
        st.success(f"Resumo salvo: {fname}")

    if cols_actions[1].button("📋 Mostrar CSV (preview)"):
        st.code(df_summary.to_csv(index=False)[:4000])

    # retorno para uso programático
    return metrics, fin
