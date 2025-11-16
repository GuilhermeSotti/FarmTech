import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgres://farmtech:changeme@localhost:5432/farmdb")
SERIAL_PORT = os.getenv("SERIAL_PORT", "COM3")
BAUD_RATE = int(os.getenv("BAUD_RATE", "115200"))
MQTT_BROKER = os.getenv("MQTT_BROKER", "broker.hivemq.com")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
OUT_CSV = os.getenv("OUT_CSV", "/tmp/sensors_ingest.csv")
IRRIGATION_THRESHOLD = float(os.getenv("IRRIGATION_THRESHOLD", "40.0"))

def get_db_connection():
    import psycopg2
    return psycopg2.connect(DATABASE_URL)

if __name__ == '__main__':
    print(f"DATABASE_URL: {DATABASE_URL}")
    print(f"SERIAL_PORT: {SERIAL_PORT}")
    print(f"MQTT_BROKER: {MQTT_BROKER}")
