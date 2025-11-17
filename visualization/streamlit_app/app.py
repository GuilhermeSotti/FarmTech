import streamlit as st
import pandas as pd
import os
import sys
import subprocess
import time
import signal
import platform
from pathlib import Path


ROOT = Path(__file__).parent.parent.parent.resolve()  
LOGS_DIR = ROOT / "logs"
LOGS_DIR.mkdir(exist_ok=True)

PY = sys.executable  
SNS_TOPIC_ARN = os.getenv("SNS_TOPIC_ARN")  
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")


SCRIPTS = {
    "simulador": ROOT / "iot" / "sensores" / "serial_simulator.py",
    "mqtt": ROOT / "iot" / "mqtt_bridge.py",
    "calibrar": ROOT / "iot" / "atuadores" / "irrigation_control.py",
    "train": ROOT / "ml" / "train_model.py",
    "predict": ROOT / "ml" / "predict.py"
}


if "farmtech_procs" not in st.session_state:
    st.session_state["farmtech_procs"] = {}  


def proc_is_running(proc):
    return proc and (proc.poll() is None)

def start_background(name, cmd):
    """
    Inicia processo em background, grava stdout/stderr em files e salva em session_state.
    """
    log_path = LOGS_DIR / f"{name}.log"
    err_path = LOGS_DIR / f"{name}.err.log"
    stdout_f = open(log_path, "a", encoding="utf-8", buffering=1)
    stderr_f = open(err_path, "a", encoding="utf-8", buffering=1)

    
    if platform.system().lower().startswith("win"):
        proc = subprocess.Popen(
            cmd,
            cwd=str(ROOT),
            stdout=stdout_f,
            stderr=stderr_f,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
        )
    else:
        proc = subprocess.Popen(
            cmd,
            cwd=str(ROOT),
            stdout=stdout_f,
            stderr=stderr_f,
            preexec_fn=os.setsid
        )

    st.session_state["farmtech_procs"][name] = {
        "proc": proc,
        "started_at": time.time(),
        "log": str(log_path),
        "err": str(err_path),
        "stdout_f": stdout_f,
        "stderr_f": stderr_f
    }
    return proc

def stop_background(name):
    info = st.session_state["farmtech_procs"].get(name)
    if not info:
        return
    proc = info.get("proc")
    if not proc:
        return
    try:
        if platform.system().lower().startswith("win"):
            
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
                os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
            except Exception:
                proc.terminate()
        
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            try:
                if platform.system().lower().startswith("win"):
                    proc.kill()
                else:
                    os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
            except Exception:
                proc.kill()
    except Exception as e:
        st.warning(f"Erro ao encerrar {name}: {e}")
    finally:
        
        for h in ("stdout_f", "stderr_f"):
            f = info.get(h)
            try:
                if f:
                    f.close()
            except Exception:
                pass
        st.session_state["farmtech_procs"].pop(name, None)

def tail(path, n=300):
    try:
        with open(path, "rb") as f:
            f.seek(0, os.SEEK_END)
            size = f.tell()
            block = 1024
            data = b""
            while size > 0 and len(data) < n * 200:
                size = max(0, size - block)
                f.seek(size)
                data = f.read(min(block, os.path.getsize(path))) + data
            text = data.decode("utf-8", errors="replace")
        return "\n".join(text.splitlines()[-n:])
    except FileNotFoundError:
        return "(log não encontrado)"
    except Exception as e:
        return f"(erro lendo log: {e})"

def run_blocking_script(path):
    """
    Executa script de forma bloqueante e retorna saída (stdout+stderr).
    """
    if not path.exists():
        return False, f"Script não encontrado: {path}"
    cmd = [PY, str(path)]
    try:
        completed = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True, check=False)
        out = completed.stdout or ""
        err = completed.stderr or ""
        combined = out + ("\n--- stderr ---\n" + err if err else "")
        return True, combined
    except Exception as e:
        return False, f"Erro executando: {e}"

def send_sns_alert(message, subject="Alerta FarmTech"):
    """
    Publica em SNS se houver SNS_TOPIC_ARN e boto3 configurado; caso contrário simula.
    """
    if not SNS_TOPIC_ARN:
        return False, "SNS_TOPIC_ARN não configurado. Simulação: mensagem não publicada."
    try:
        import boto3
        client = boto3.client("sns", region_name=AWS_REGION)
        resp = client.publish(TopicArn=SNS_TOPIC_ARN, Message=message, Subject=subject)
        return True, f"Publicado: MessageId={resp.get('MessageId')}"
    except Exception as e:
        return False, f"Erro publicando em SNS: {e}"

def find_csv(*candidates):
    for p in candidates:
        p = ROOT / p
        if p.exists():
            return p
    return None


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
    csv_candidates = [
        "db/data_samples/sensors.csv",
        "db/sensors.csv",
        "db/sensors_data.csv",
        "db/sensors.csv"
    ]
    csv_path = find_csv(*csv_candidates)
    if csv_path:
        try:
            df = pd.read_csv(csv_path)
            st.dataframe(df, width='stretch')
        except Exception as e:
            st.error(f"Erro ao carregar CSV: {e}")
    else:
        st.info("CSV de sensores não encontrado. Caminhos verificados: " + ", ".join(csv_candidates))


elif phase == "IoT & Sensores":
    st.header("IoT & Sensores")
    st.write("Gerenciamento de dispositivos IoT e sensores")

    
    sim_running = "simulador" in st.session_state["farmtech_procs"]
    col1, col2 = st.columns([1, 2])

    with col1:
        if not sim_running:
            if st.button("▶ Iniciar Simulador Serial"):
                script = SCRIPTS["simulador"]
                if not script.exists():
                    st.error(f"Script não encontrado: {script}")
                else:
                    start_background("simulador", [PY, str(script)])
                    st.success("Simulador iniciado (background). Verifique logs.")
        else:
            if st.button("⏸ Parar Simulador Serial"):
                stop_background("simulador")
                st.warning("Simulador parado.")

    with col2:
        
        info = st.session_state["farmtech_procs"].get("simulador")
        if info:
            st.subheader("Logs do Simulador (últimas linhas)")
            st.text_area("sim_log", value=tail(info["log"], 200), height=300)

    
    mqtt_running = "mqtt" in st.session_state["farmtech_procs"]
    col1, col2 = st.columns([1, 2])
    with col1:
        if not mqtt_running:
            if st.button("▶ Iniciar MQTT Bridge"):
                script = SCRIPTS["mqtt"]
                if not script.exists():
                    st.error(f"Script não encontrado: {script}")
                else:
                    start_background("mqtt", [PY, str(script)])
                    st.success("MQTT Bridge iniciado (background).")
        else:
            if st.button("⏸ Parar MQTT Bridge"):
                stop_background("mqtt")
                st.warning("MQTT Bridge parado.")
    with col2:
        info = st.session_state["farmtech_procs"].get("mqtt")
        if info:
            st.subheader("Logs do MQTT Bridge (últimas linhas)")
            st.text_area("mqtt_log", value=tail(info["log"], 200), height=300)

    
    st.markdown("---")
    if st.button("⚙ Calibrar Sensores"):
        script = SCRIPTS["calibrar"]
        ok, output = run_blocking_script(script)
        if ok:
            st.success("Calibração executada")
            st.code(output[:10000])
        else:
            st.error(output)


elif phase == "Data Pipeline":
    st.header("Data Pipeline")
    st.write("Processamento e ingestão de dados")

    
    if st.button("▶ Executar MQTT Bridge (one-shot)"):
        script = SCRIPTS["mqtt"]
        ok, output = run_blocking_script(script)
        if ok:
            st.success("MQTT Bridge executou (one-shot). Vários bridges são normalmente long-running.")
            st.code(output[:10000])
        else:
            st.error(output)

    
    csv_candidates = [
        "db/data_samples/weather.csv",
        "db/weather.csv",
    ]
    csv_path = find_csv(*csv_candidates)
    if csv_path:
        try:
            df = pd.read_csv(csv_path)
            st.subheader("Dados Climáticos")
            st.dataframe(df, width='stretch')
        except Exception as e:
            st.error(f"Erro ao carregar dados climáticos: {e}")
    else:
        st.info("CSV de clima não encontrado. Caminhos verificados: " + ", ".join(csv_candidates))


elif phase == "Machine Learning":
    st.header("Machine Learning")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🎓 Treinar Modelo"):
            script = SCRIPTS["train"]
            ok, output = run_blocking_script(script)
            if ok:
                st.success("Treinamento finalizado")
                st.code(output[:10000])
            else:
                st.error(output)
    with col2:
        if st.button("🔮 Fazer Predição"):
            script = SCRIPTS["predict"]
            ok, output = run_blocking_script(script)
            if ok:
                
                st.success("Predição executada")
                st.code(output[:10000])
            else:
                st.error(output)


elif phase == "Alertas AWS":
    st.header("Alertas AWS")
    st.write("Sistema de notificações via SNS (requer configuração de credenciais AWS e SNS_TOPIC_ARN no ambiente)")

    alert_type = st.selectbox("Tipo de alerta:", ["Umidade Crítica", "Nutriente Baixo", "Falha Sensor"])
    custom_msg = st.text_area("Mensagem (opcional)", value="")
    if st.button("📧 Enviar Alerta"):
        
        msg = custom_msg.strip() or f"[{alert_type}] - Evento detectado no FarmTech (simulação)."
        ok, out = send_sns_alert(msg, subject=f"FarmTech - {alert_type}")
        if ok:
            st.success(out)
        else:
            st.error(out)

st.sidebar.markdown("---")
st.sidebar.markdown("**FarmTech v7.0**  \nOrquestrador consolidado com suporte a todas as fases.")


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
