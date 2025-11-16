import paho.mqtt.client as mqtt
import csv
import json
import os

OUT_CSV = os.getenv("OUT_CSV", "/tmp/sensors_ingest.csv")

def on_connect(client, userdata, flags, rc):
    client.subscribe("farmtech/sensors/#")
    print(f"Connected with result code {rc}")

def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode('utf-8')
        data = json.loads(payload)
    except Exception as e:
        print(f"Error parsing message: {e}")
        return
    
    header = ['sensor_id', 'umidade', 'nutriente', 'ts']
    write_header = not os.path.exists(OUT_CSV)
    
    with open(OUT_CSV, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=header)
        if write_header:
            writer.writeheader()
        writer.writerow({
            'sensor_id': data.get('sensor_id'),
            'umidade': data.get('umidade'),
            'nutriente': data.get('nutriente'),
            'ts': data.get('ts')
        })
    print(f"Saved: {data}")

if __name__ == '__main__':
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect("broker.hivemq.com", 1883, 60)
    client.loop_forever()
