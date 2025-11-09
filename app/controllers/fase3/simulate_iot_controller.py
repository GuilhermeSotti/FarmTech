"""
Controller Fase 3 - Simulação IoT
Gera mensagens de exemplo e as publica via mensageria local/serviço.
"""
import time
import json
from random import uniform
from app.services.mensageria_aws import publish_alert

def main():
    print("Iniciando simulação IoT (5 amostras)")
    for i in range(5):
        payload = {
            "sensor_id": f"sensor_{i}",
            "timestamp": time.time(),
            "humidity": round(uniform(20, 90), 2)
        }
        print("Simulated:", payload)
        if payload["humidity"] < 30:
            publish_alert("Alerta de Umidade", json.dumps(payload))
        time.sleep(0.5)

if __name__ == "__main__":
    main()
