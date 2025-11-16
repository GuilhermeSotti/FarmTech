import os
import json
import time

THRESHOLD = float(os.getenv("IRRIGATION_THRESHOLD", "40.0"))

def evaluate(reading):
    if reading.get("umidade", 100) < THRESHOLD:
        return "ON"
    return "OFF"

if __name__ == '__main__':
    sample = {"umidade": 37.5}
    action = evaluate(sample)
    print("Ação:", action)
