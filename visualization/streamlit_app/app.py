import os
import sys
import time
import signal
import subprocess
import platform
import logging
import json
import uuid
from pathlib import Path
from datetime import datetime

import streamlit as st
import pandas as pd
import sqlalchemy
from botocore.exceptions import ClientError
import boto3

# ----------------- Config / Paths -----------------
ROOT = Path(__file__).parent.parent.parent.resolve()
LOGS_DIR = ROOT / "logs"
LOGS_DIR.mkdir(exist_ok=True)

PY = sys.executable
SNS_TOPIC_ARN = (os.getenv("SNS_TOPIC_ARN") or "").strip()
AWS_REGION = (os.getenv("AWS_REGION") or "sa-east-1").strip()
DATABASE_URL = os.getenv("DATABASE_URL") or os.getenv("DB_URL") or None

# MQTT script paths (opcional)
SIMULATOR_SCRIPT = ROOT / "iot" / "sensores" / "serial_simulator.py"
MQTT_SCRIPT = ROOT / "iot" / "mqtt_bridge.py"

# logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("farmtech.app")

# ----------------- Helpers: process management -----------------
def is_windows():
    return platform.system().lower().startswith("win")

def start_background(name, cmd):
    """Inicia processo (background) e registra handles em st.session_state"""
    log_path = LOGS_DIR / f"{name}.log"
    err_path = LOGS_DIR / f"{name}.err.log"
    stdout_f = open(log_path, "a", encoding="utf-8", buffering=1)
    stderr_f = open(err_path, "a", encoding="utf-8", buffering=1)

    if is_windows():
        proc = subprocess.Popen(cmd, cwd=str(ROOT), stdout=stdout_f, stderr=stderr_f,
                                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
    else:
        proc = subprocess.Popen(cmd, cwd=str(ROOT), stdout=stdout_f, stderr=stderr_f,
                                preexec_fn=os.setsid)

    st.session_state["farmtech_procs"][name] = {
        "proc": proc,
        "started_at": time.time(),
        "log": str(log_path),
        "err": str(err_path),
        "stdout_f": stdout_f,
        "stderr_f": stderr_f
    }
    return proc

def terminate_proc(proc):
    if proc.poll() is not None:
        return
    try:
        if is_windows():
            try:
                proc.send_signal(signal.CTRL_BREAK_EVENT)
                time.sleep(0.5)
            except Exception:
                pass
            try:
                proc.terminate()
            except Exception:
                pass
        else:
            try:
                import os as _os
                _os.killpg(_os.getpgid(proc.pid), signal.SIGTERM)
            except Exception:
                proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            try:
                if is_windows():
                    proc.kill()
                else:
                    import os as _os
                    _os.killpg(_os.getpgid(proc.pid), signal.SIGKILL)
            except Exception:
                proc.kill()
    except Exception as e:
        logger.exception("Erro terminando proc: %s", e)

def stop_background(name):
    info = st.session_state["farmtech_procs"].get(name)
    if not info:
        return
    proc = info.get("proc")
    try:
        terminate_proc(proc)
    finally:
        for h in ("stdout_f", "stderr_f"):
            f = info.get(h)
            try:
                if f:
                    f.close()
            except Exception:
                pass
        st.session_state["farmtech_procs"].pop(name, None)

def tail(path: str, n: int = 200):
    try:
        with open(path, "rb") as f:
            f.seek(0, 2)
            size = f.tell()
            block = 4096
            data = b""
            while size > 0 and len(data) < n * 300:
                size = max(0, size - block)
                f.seek(size)
                data = f.read(min(block, size)) + data
            text = data.decode("utf-8", errors="replace")
        return "\n".join(text.splitlines()[-n:])
    except FileNotFoundError:
        return "(log não encontrado)"
    except Exception as e:
        return f"(erro lendo log: {e})"

# ----------------- SNS helper -----------------
def publish_sns(message: str, subject: str = "Alerta FarmTech", message_group_id: str = None):
    """
    Publica em SNS. Detecta FIFO (.fifo) e injeta MessageGroupId/MessageDeduplicationId automaticamente.
    Retorna resposta boto3 ou lança exceção.
    """
    arn = SNS_TOPIC_ARN
    if not arn:
        raise RuntimeError("SNS_TOPIC_ARN não configurado")
    client = boto3.client("sns", region_name=AWS_REGION)
    is_fifo = arn.lower().endswith(".fifo")
    kwargs = {"TopicArn": arn, "Message": message, "Subject": subject[:100]}
    if is_fifo:
        kwargs["MessageGroupId"] = message_group_id or f"farmtech-{datetime.utcnow().strftime('%Y%m%d')}"
        kwargs["MessageDeduplicationId"] = str(uuid.uuid4())
    resp = client.publish(**kwargs)
    return resp

# ----------------- fetch_metrics -----------------
@st.cache_data(ttl=5)
def _get_engine(url: str):
    try:
        engine = sqlalchemy.create_engine(url)
        with engine.connect() as conn:
            conn.execute(sqlalchemy.text("SELECT 1"))
        return engine
    except Exception:
        return None

@st.cache_data(ttl=5)
def fetch_metrics(database_url: str = None):
    """
    Retorna dicionário com:
      - sensors_active (int)
      - umidade_media (float)
      - alerts_pending (int)
      - latest_readings (DataFrame)
    Usa DB se database_url válido; fallback CSV se não.
    """
    result = {
        "sensors_active": 0,
        "umidade_media": None,
        "alerts_pending": 0,
        "latest_readings": pd.DataFrame()
    }

    engine = None
    if database_url:
        engine = _get_engine(database_url)

    if engine:
        # DB queries (Postgres)
        try:
            q_active = """
            SELECT sensor_id, MAX(ts) as last_ts
            FROM sensors
            GROUP BY sensor_id
            HAVING MAX(ts) >= (now() - interval '15 minutes')
            """
            df_active = pd.read_sql_query(sqlalchemy.text(q_active), con=engine)
            result["sensors_active"] = int(df_active.shape[0])
        except Exception:
            result["sensors_active"] = 0

        try:
            q_um = "SELECT umidade FROM sensors WHERE umidade IS NOT NULL ORDER BY ts DESC LIMIT 100"
            df_um = pd.read_sql_query(sqlalchemy.text(q_um), con=engine)
            if df_um is not None and not df_um.empty:
                result["umidade_media"] = round(float(df_um['umidade'].mean()), 2)
        except Exception:
            result["umidade_media"] = None

        try:
            q_alerts = "SELECT COUNT(*) as pending FROM alerts WHERE resolved = false"
            df_alerts = pd.read_sql_query(sqlalchemy.text(q_alerts), con=engine)
            result["alerts_pending"] = int(df_alerts['pending'].iloc[0]) if not df_alerts.empty else 0
        except Exception:
            result["alerts_pending"] = 0

        try:
            q_latest = "SELECT sensor_id, umidade, nutriente, ts FROM sensors ORDER BY ts DESC LIMIT 20"
            df_latest = pd.read_sql_query(sqlalchemy.text(q_latest), con=engine)
            result["latest_readings"] = df_latest
        except Exception:
            result["latest_readings"] = pd.DataFrame()

        return result

    # ---------- CSV fallback ----------
    csv_candidates = [
        ROOT / "db" / "data_samples" / "sensors.csv",
        ROOT / "db" / "sensors.csv",
        ROOT / "db" / "sensors_data.csv",
    ]
    df = None
    for p in csv_candidates:
        try:
            if p.exists():
                df = pd.read_csv(p)
                break
        except Exception:
            df = None

    if df is None:
        return result

    # normalize timestamp
    if 'ts' in df.columns:
        df['ts'] = pd.to_datetime(df['ts'], errors='coerce')

    try:
        now = pd.Timestamp.now()
        last_per_sensor = df.sort_values('ts').groupby('sensor_id').last().reset_index()
        recent = last_per_sensor[last_per_sensor['ts'] >= (now - pd.Timedelta(minutes=15))]
        result['sensors_active'] = int(recent.shape[0])
    except Exception:
        result['sensors_active'] = int(df['sensor_id'].nunique()) if 'sensor_id' in df.columns else 0

    if 'umidade' in df.columns:
        try:
            result['umidade_media'] = round(float(df['umidade'].dropna().astype(float).tail(100).mean()), 2)
        except Exception:
            result['umidade_media'] = None

    try:
        if 'ts' in df.columns:
            result['latest_readings'] = df.sort_values('ts', ascending=False).head(20)
        else:
            result['latest_readings'] = df.head(20)
    except Exception:
        result['latest_readings'] = df.head(20)

    return result

# ----------------- Streamlit UI -----------------
st.set_page_config(page_title="FarmTech - Orquestrador", layout="wide")
st.title("🌾 FarmTech - Orquestrador Integrado")

# init process store
if "farmtech_procs" not in st.session_state:
    st.session_state["farmtech_procs"] = {}

# Sidebar
st.sidebar.header("Fases")
phase = st.sidebar.radio("Selecione uma fase:", [
    "Dashboard Principal",
    "IoT & Sensores",
    "Data Pipeline",
    "Machine Learning",
    "Alertas AWS"
])

# ---------------- Dashboard Principal (com cálculos econômicos) ----------------
if phase == "Dashboard Principal":
    st.header("Dashboard Principal — Dados Reais + Cálculos Econômicos")

    if st.button("🔄 Atualizar métricas"):
        try:
            st.cache_data.clear()
        except Exception:
            pass

    with st.spinner("Consultando dados..."):
        metrics = fetch_metrics(DATABASE_URL)

    # Mostrar métricas (reais)
    sensores_ativos = metrics.get("sensors_active", 0)
    umidade_media = metrics.get("umidade_media")
    alertas_pendentes = metrics.get("alerts_pending", 0)

    col1, col2, col3 = st.columns(3)
    col1.metric("Sensores Ativos", sensores_ativos)
    col2.metric("Umidade Média", f"{umidade_media}%" if umidade_media is not None else "—")
    col3.metric("Alertas Pendentes", alertas_pendentes)

    st.markdown("---")
    st.subheader("Parâmetros agrícolas (insira valores para cálculos)")

    # Inputs
    c1, c2, c3 = st.columns(3)
    with c1:
        area_ha = st.number_input("Área total (ha)", min_value=0.0, value=1.0, step=0.1, format="%.3f")
        yield_per_ha = st.number_input("Produtividade esperada (kg/ha)", min_value=0.0, value=5000.0, step=100.0)
        unit_name = st.text_input("Unidade de produção", value="kg")
    with c2:
        price_per_unit = st.number_input(f"Preço por {unit_name}", min_value=0.0, value=1.5, step=0.01)
        cost_per_ha = st.number_input("Custo variável por ha", min_value=0.0, value=200.0, step=1.0)
        fixed_costs = st.number_input("Custos fixos (total)", min_value=0.0, value=100.0, step=1.0)
    with c3:
        sensor_cost_unit = st.number_input("Custo por sensor", min_value=0.0, value=25.0, step=1.0)
        other_variable_costs = st.number_input("Outros custos variáveis (total)", min_value=0.0, value=0.0, step=1.0)
        contingency_pct = st.slider("Reserva/Contingência (%)", 0, 50, 5)

    # cálculos
    try:
        sensors_active_count = int(sensores_ativos or 0)
    except Exception:
        sensors_active_count = 0

    production_total = area_ha * yield_per_ha
    revenue_total = production_total * price_per_unit
    variable_costs_total = (cost_per_ha * area_ha) + float(other_variable_costs or 0.0)
    sensor_total_cost = sensor_cost_unit * sensors_active_count
    total_costs = variable_costs_total + fixed_costs + sensor_total_cost
    contingency_amount = (contingency_pct / 100.0) * total_costs
    total_costs_with_contingency = total_costs + contingency_amount
    profit_total = revenue_total - total_costs_with_contingency
    profit_per_ha = profit_total / area_ha if area_ha > 0 else 0.0
    profit_margin = (profit_total / revenue_total * 100.0) if revenue_total > 0 else None
    roi = (profit_total / total_costs_with_contingency * 100.0) if total_costs_with_contingency > 0 else None
    revenue_per_sensor = revenue_total / sensors_active_count if sensors_active_count > 0 else None
    cost_per_sensor = total_costs_with_contingency / sensors_active_count if sensors_active_count > 0 else None
    production_per_sensor = production_total / sensors_active_count if sensors_active_count > 0 else None

    # exibir métricas financeiras
    rc1, rc2, rc3 = st.columns(3)
    rc1.metric("Produção Total", f"{production_total:,.0f} {unit_name}")
    rc2.metric("Receita Estimada", f"{revenue_total:,.2f}")
    rc3.metric("Custo Total (+cont.)", f"{total_costs_with_contingency:,.2f}")

    rc4, rc5, rc6 = st.columns(3)
    rc4.metric("Lucro Total", f"{profit_total:,.2f}")
    rc5.metric("Lucro por ha", f"{profit_per_ha:,.2f}")
    rc6.metric("ROI (%)", f"{roi:.2f}%" if roi is not None else "—")

    st.markdown("#### Detalhes por sensor")
    st.write(f"Sensores ativos usados no cálculo: **{sensors_active_count}**")
    st.write(f"Receita por sensor: **{revenue_per_sensor:,.2f}**" if revenue_per_sensor is not None else "—")
    st.write(f"Custo por sensor: **{cost_per_sensor:,.2f}**" if cost_per_sensor is not None else "—")
    st.write(f"Produção por sensor: **{production_per_sensor:,.0f} {unit_name}**" if production_per_sensor is not None else "—")

    # resumo em tabela
    summary = {
        "Métrica": [
            "Área (ha)",
            f"Produtividade ({unit_name}/ha)",
            "Produção total",
            f"Preço por {unit_name}",
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
            area_ha,
            yield_per_ha,
            f"{production_total:,.0f} {unit_name}",
            price_per_unit,
            f"{revenue_total:,.2f}",
            f"{variable_costs_total:,.2f}",
            f"{sensor_total_cost:,.2f}",
            f"{fixed_costs:,.2f}",
            f"{contingency_pct}%",
            f"{contingency_amount:,.2f}",
            f"{total_costs_with_contingency:,.2f}",
            f"{profit_total:,.2f}",
            f"{profit_per_ha:,.2f}",
            f"{roi:.2f}%" if roi is not None else "—",
            sensors_active_count
        ]
    }
    df_summary = pd.DataFrame(summary)
    st.dataframe(df_summary, width='stretch')

    st.markdown("---")
    st.subheader("Últimas leituras (fonte)")
    latest = metrics.get("latest_readings")
    if latest is None or latest.empty:
        st.info("Nenhuma leitura disponível.")
    else:
        if 'ts' in latest.columns:
            latest = latest.copy()
            latest['ts'] = pd.to_datetime(latest['ts']).astype(str)
        st.dataframe(latest, width='stretch')

    # export
    e1, e2 = st.columns(2)
    if e1.button("💾 Exportar resumo CSV"):
        repdir = ROOT / "reports"
        repdir.mkdir(exist_ok=True)
        fname = repdir / f"farmtech_summary_{int(time.time())}.csv"
        df_summary.to_csv(fname, index=False)
        st.success(f"Resumo salvo: {fname}")
    if e2.button("📋 Mostrar CSV (preview)"):
        st.code(df_summary.to_csv(index=False)[:3000])

# ---------------- IoT & Sensores (simplificado) ----------------
elif phase == "IoT & Sensores":
    st.header("IoT & Sensores")
    st.write("Controles básicos para simulador e MQTT bridge (dev)")

    sim_running = "simulator" in st.session_state["farmtech_procs"]
    if not sim_running:
        if st.button("▶ Iniciar Simulador Serial"):
            if not SIMULATOR_SCRIPT.exists():
                st.error(f"Script não encontrado: {SIMULATOR_SCRIPT}")
            else:
                start_background("simulator", [PY, str(SIMULATOR_SCRIPT)])
                st.success("Simulador iniciado")
    else:
        if st.button("⏸ Parar Simulador Serial"):
            stop_background("simulator")
            st.warning("Simulador parado")

    mqtt_running = "mqtt" in st.session_state["farmtech_procs"]
    if not mqtt_running:
        if st.button("▶ Iniciar MQTT Bridge"):
            if not MQTT_SCRIPT.exists():
                st.error(f"Script não encontrado: {MQTT_SCRIPT}")
            else:
                start_background("mqtt", [PY, str(MQTT_SCRIPT)])
                st.success("MQTT Bridge iniciado")
    else:
        if st.button("⏸ Parar MQTT Bridge"):
            stop_background("mqtt")
            st.warning("MQTT Bridge parado")

    # logs preview
    info = st.session_state["farmtech_procs"].get("mqtt")
    if info:
        st.subheader("Logs MQTT (últimas linhas)")
        st.text_area("mqtt_log", value=tail(info["log"], 500), height=300)

# ---------------- Data Pipeline ----------------
elif phase == "Data Pipeline":
    st.header("Data Pipeline")
    st.write("Ações rápidas: executar bridge one-shot, visualizar CSVs")

    if st.button("▶ Executar MQTT Bridge (one-shot)"):
        if not MQTT_SCRIPT.exists():
            st.error(f"Script não encontrado: {MQTT_SCRIPT}")
        else:
            ok = subprocess.run([PY, str(MQTT_SCRIPT)], cwd=str(ROOT))
            st.info(f"Exit code: {ok.returncode}")

    # show weather CSV
    cands = [ROOT / "db" / "data_samples" / "weather.csv", ROOT / "db" / "weather.csv"]
    found = None
    for p in cands:
        if p.exists():
            found = p
            break
    if found:
        try:
            dfw = pd.read_csv(found)
            st.subheader("Dados Climáticos (preview)")
            st.dataframe(dfw.head(200), width='stretch')
        except Exception as e:
            st.error(f"Erro lendo CSV clima: {e}")
    else:
        st.info("CSV de clima não encontrado.")

# ---------------- Machine Learning ----------------
elif phase == "Machine Learning":
    st.header("Machine Learning")
    st.write("Treinamento e predição (scripts externos)")

    if st.button("🎓 Treinar Modelo"):
        train_script = ROOT / "ml" / "train_model.py"
        if not train_script.exists():
            st.error(f"Script não encontrado: {train_script}")
        else:
            with st.spinner("Treinando..."):
                proc = subprocess.run([PY, str(train_script)], cwd=str(ROOT), capture_output=True, text=True)
                if proc.returncode == 0:
                    st.success("Treinamento finalizado")
                    st.code(proc.stdout[:10000])
                else:
                    st.error("Erro no treinamento")
                    st.code(proc.stderr[:10000])

    if st.button("🔮 Fazer Predição"):
        pred_script = ROOT / "ml" / "predict.py"
        if not pred_script.exists():
            st.error(f"Script não encontrado: {pred_script}")
        else:
            proc = subprocess.run([PY, str(pred_script)], cwd=str(ROOT), capture_output=True, text=True)
            if proc.returncode == 0:
                st.success("Predição executada")
                st.code(proc.stdout[:5000])
            else:
                st.error("Erro na predição")
                st.code(proc.stderr[:5000])

# ---------------- Alertas AWS ----------------
elif phase == "Alertas AWS":
    st.header("Alertas AWS (SNS)")
    st.write("Enviar alerta para SNS (requer SNS_TOPIC_ARN nas variáveis de ambiente)")

    alert_type = st.selectbox("Tipo de alerta", ["Umidade Crítica", "Nutriente Baixo", "Falha Sensor"])
    custom_msg = st.text_area("Mensagem (opcional)")
    if st.button("📧 Enviar Alerta"):
        msg = custom_msg.strip() or f"[{alert_type}] - Evento detectado no FarmTech: {datetime.utcnow().isoformat()}"
        try:
            resp = publish_sns(msg, subject=f"FarmTech - {alert_type}")
            st.success(f"Alerta enviado. MessageId: {resp.get('MessageId')}")
        except Exception as e:
            st.error(f"Erro ao publicar alerta: {e}")

st.sidebar.markdown("---")
st.sidebar.markdown("**FarmTech v7.0** - Orquestrador")

if st.sidebar.checkbox("Mostrar processos ativos"):
    procs = st.session_state["farmtech_procs"]
    if not procs:
        st.sidebar.info("Nenhum processo em background.")
    else:
        for name, info in procs.items():
            pid = info["proc"].pid if info.get("proc") else "?"
            st.sidebar.write(f"- {name}: PID {pid} • iniciado em {time.ctime(info['started_at'])}")
            if st.sidebar.button(f"Stop {name}"):
                stop_background(name)
                st.experimental_rerun()
