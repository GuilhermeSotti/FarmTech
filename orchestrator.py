
"""
Orchestrator FarmTech (melhorado)

- Long-running processes (simulador, mqtt, streamlit) são iniciados com Popen (background)
  e mantidos vivos até Ctrl+C (shutdown gracioso).
- Short tasks (train, predict, db seed) são executadas e aguardadas.
- Logs de cada processo vão para logs/{phase}.log e logs/{phase}.err.log
- Uso:
    python orchestrator.py --phase all
    python orchestrator.py --phase mqtt
    python orchestrator.py --phase train
"""

import argparse
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
import platform

PROJECT_ROOT = Path(__file__).parent.resolve()
LOG_DIR = PROJECT_ROOT / "logs"
LOG_DIR.mkdir(exist_ok=True)


PHASES = {
    "iot": ["python", str(PROJECT_ROOT / "iot" / "sensores" / "serial_simulator.py")],
    "mqtt": ["python", str(PROJECT_ROOT / "iot" / "mqtt_bridge.py")],
    "serial": ["python", str(PROJECT_ROOT / "data_pipeline" / "serial_reader.py")],
    "train": ["python", str(PROJECT_ROOT / "ml" / "train_model.py")],
    "predict": ["python", str(PROJECT_ROOT / "ml" / "predict.py")],
    "yolo": ["python", str(PROJECT_ROOT / "ml" / "train_yolo.py")],
    "streamlit": ["streamlit", "run", str(PROJECT_ROOT / "visualization" / "streamlit_app" / "app.py")],
    "aws": ["python", str(PROJECT_ROOT / "aws" / "notify.py")],
    "irrigation": ["python", str(PROJECT_ROOT / "iot" / "atuadores" / "irrigation_control.py")],
}

LONG_RUNNING = {"iot", "mqtt", "streamlit", "irrigation"}

background_procs = {}

def is_windows():
    return platform.system().lower().startswith("win")

def start_background(phase, cmd):
    """
    Start a long-running command with Popen, redirecting stdout/stderr to logs.
    Returns the Popen object.
    """
    stdout_path = LOG_DIR / f"{phase}.log"
    stderr_path = LOG_DIR / f"{phase}.err.log"
    stdout_f = open(stdout_path, "a", buffering=1, encoding="utf-8")
    stderr_f = open(stderr_path, "a", buffering=1, encoding="utf-8")
    print(f"[ORCH] Iniciando (background) {phase}: {' '.join(cmd)}")
    print(f"[ORCH] stdout -> {stdout_path}, stderr -> {stderr_path}")
    if is_windows():
        proc = subprocess.Popen(
            cmd,
            stdout=stdout_f,
            stderr=stderr_f,
            cwd=str(PROJECT_ROOT),
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
        )
    else:
        proc = subprocess.Popen(
            cmd,
            stdout=stdout_f,
            stderr=stderr_f,
            cwd=str(PROJECT_ROOT),
            preexec_fn=os.setsid
        )
    proc._orch_stdout = stdout_f
    proc._orch_stderr = stderr_f
    return proc

def run_blocking(phase, cmd, env=None):
    """
    Run a command and wait (for short tasks). Streams output to screen.
    """
    print(f"[ORCH] Executando (blocking) {phase}: {' '.join(cmd)}")
    try:
        completed = subprocess.run(cmd, cwd=str(PROJECT_ROOT), env=env, check=False)
        print(f"[ORCH] Fase {phase} finalizada com returncode={completed.returncode}")
        return completed.returncode
    except KeyboardInterrupt:
        print(f"[ORCH] Execução da fase {phase} interrompida via KeyboardInterrupt")
        return 1

def terminate_proc(proc):
    """Graceful terminate a Popen proc (cross-platform)"""
    if proc.poll() is not None:
        return
    try:
        print(f"[ORCH] Encerrando PID {proc.pid}")
        if is_windows():
            try:
                proc.send_signal(signal.CTRL_BREAK_EVENT)
                time.sleep(1)
                proc.terminate()
            except Exception:
                proc.terminate()
        else:
            try:
                os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
            except Exception:
                proc.terminate()

        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            print(f"[ORCH] Forçando kill PID {proc.pid}")
            try:
                if is_windows():
                    proc.kill()
                else:
                    os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
            except Exception:
                proc.kill()
    except Exception as e:
        print(f"[ORCH] Erro ao encerrar PID {getattr(proc,'pid',None)}: {e}")
    finally:
        for attr in ("_orch_stdout", "_orch_stderr"):
            f = getattr(proc, attr, None)
            if f:
                try:
                    f.close()
                except Exception:
                    pass

def run_phase(phase):
    if phase not in PHASES:
        print(f"[ORCH] Fase desconhecida: {phase}")
        print(f"[ORCH] Fases disponíveis: {sorted(PHASES.keys())}")
        return

    cmd = PHASES[phase]
    if phase in LONG_RUNNING:
        proc = start_background(phase, cmd)
        background_procs[phase] = proc
        return proc
    else:
        return_code = run_blocking(phase, cmd)
        return return_code

def run_all(sequential_short=True):
    """
    Strategy:
      - Start all LONG_RUNNING processes in background first.
      - Then run short tasks sequentially (or you can change to parallel).
      - Keep the script alive until Ctrl+C, which will trigger shutdown.
    """
    print("[ORCH] Iniciando execução de todas as fases.")

    for phase in PHASES:
        if phase in LONG_RUNNING:
            try:
                run_phase(phase)
            except Exception as e:
                print(f"[ORCH] Falha ao iniciar {phase}: {e}")

    for phase in PHASES:
        if phase not in LONG_RUNNING:
            try:
                run_phase(phase)
            except Exception as e:
                print(f"[ORCH] Erro na fase {phase}: {e}")

    print("[ORCH] Todas as fases curtas iniciadas/completadas. Backgrounds seguem rodando.")
    print("[ORCH] Pressione Ctrl+C para encerrar todos os processos e sair.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("[ORCH] Ctrl+C detectado, iniciando shutdown...")

def shutdown_all():
    print("[ORCH] Shutdown: terminando processos em background...")

    for phase, proc in list(background_procs.items())[::-1]:
        try:
            print(f"[ORCH] Parando {phase} (PID {getattr(proc,'pid',None)})")
            terminate_proc(proc)
        except Exception as e:
            print(f"[ORCH] Erro ao parar {phase}: {e}")

def _signal_handler(sig, frame):
    print(f"[ORCH] Sinal recebido: {sig}. Encerrando.")
    shutdown_all()
    sys.exit(0)

def main():
    parser = argparse.ArgumentParser(description="FarmTech Orchestrator (improved)")
    parser.add_argument("--phase", default="all", help="Phase to run (or 'all')")
    args = parser.parse_args()

    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    if args.phase == "all":
        run_all()
        shutdown_all()
    else:
        proc = run_phase(args.phase)
        if args.phase in LONG_RUNNING:
            print(f"[ORCH] {args.phase} iniciado em background. Ctrl+C para encerrar.")
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("[ORCH] Ctrl+C detectado, encerrando...")
                shutdown_all()
        else:
            pass

if __name__ == "__main__":
    main()
