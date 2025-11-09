"""
Orquestrador principal - executa fases via controller (MVC adaptado).
Uso: python orchestrator.py --phase 1
"""
import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent
APP = ROOT / "app"

def run_cmd(module_path):
    subprocess.run([sys.executable, "-m", module_path], check=True)

def run_phase(phase):
    mapping = {
        "1": "app.controllers.fase1.calc_area_controller",
        "2": "app.controllers.fase2.model_training_controller",
        "3": "app.controllers.fase3.simulate_iot_controller",
        "4": "app.controllers.fase4.dashboard_controller",
        "5": "app.controllers.fase5.vision_controller",
        "all": None
    }
    if phase == "all":
        for ph in ["1","2","3","4","5"]:
            print(f"[orchestrator] iniciando fase {ph}")
            run_cmd(mapping[ph])
    else:
        if phase not in mapping:
            raise SystemExit(f"Fase desconhecida: {phase}")
        run_cmd(mapping[phase])

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--phase", choices=["1","2","3","4","5","all"], required=True)
    args = p.parse_args()
    run_phase(args.phase)
