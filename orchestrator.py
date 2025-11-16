import argparse
import subprocess
import sys
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent

PHASES = {
    "iot": ["python", "iot/sensores/serial_simulator.py"],
    "mqtt": ["python", "iot/mqtt_bridge.py"],
    "serial": ["python", "data_pipeline/serial_reader.py"],
    "train": ["python", "ml/train_model.py"],
    "predict": ["python", "ml/predict.py"],
    "yolo": ["python", "ml/train_yolo.py"],
    "streamlit": ["streamlit", "run", "visualization/streamlit_app/app.py"],
    "aws": ["python", "aws/notify.py"],
    "irrigation": ["python", "iot/atuadores/irrigation_control.py"],
}

def run_phase(phase_name):
    if phase_name not in PHASES:
        print(f"Fase desconhecida: {phase_name}")
        print(f"Fases disponíveis: {list(PHASES.keys())}")
        return
    
    cmd = PHASES[phase_name]
    print(f"Executando: {' '.join(cmd)}")
    os.chdir(PROJECT_ROOT)
    subprocess.run(cmd)

def run_all():
    print("Executando todas as fases...")
    for phase in ["iot", "mqtt", "train", "streamlit"]:
        print(f"\n=== {phase.upper()} ===")
        try:
            run_phase(phase)
        except KeyboardInterrupt:
            print(f"Fase {phase} interrompida")
            break

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="FarmTech Orchestrator")
    parser.add_argument("--phase", default="all", help="Phase to run (or 'all')")
    args = parser.parse_args()
    
    if args.phase == "all":
        run_all()
    else:
        run_phase(args.phase)
