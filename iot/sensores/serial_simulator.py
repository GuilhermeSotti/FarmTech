import time
import random
import json

def simulate():
    while True:
        data = {
            "sensor_id": "sim-01",
            "umidade": round(random.uniform(30, 70), 2),
            "nutriente": round(random.uniform(8, 15), 2),
            "ts": time.strftime('%Y-%m-%dT%H:%M:%S')
        }
        print(json.dumps(data))
        time.sleep(5)

if __name__ == '__main__':
    simulate()
