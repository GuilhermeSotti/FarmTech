
"""
mqtt_bridge.py (versão atualizada)
- Callback API v2 (paho >= 2.x)
- Reconnect/backoff, will, logs e escrita CSV segura
- Testado com broker público (broker.hivemq.com)
"""

import os
import csv
import json
import time
import logging
from pathlib import Path
import signal
import sys
import paho.mqtt.client as mqtt


OUT_CSV = os.getenv("OUT_CSV", str(Path.cwd() / "db" / "sensors_ingest.csv"))
BROKER = os.getenv("MQTT_BROKER", "broker.hivemq.com")
PORT = int(os.getenv("MQTT_PORT", "1883"))
TOPIC = os.getenv("MQTT_TOPIC", "farmtech/sensors/#")
CLIENT_ID = os.getenv("MQTT_CLIENT_ID", "farmtech-bridge-01")
QOS = int(os.getenv("MQTT_QOS", "0"))
KEEPALIVE = int(os.getenv("MQTT_KEEPALIVE", "60"))

RECONNECT_MIN = int(os.getenv("MQTT_RECONNECT_MIN", "1"))
RECONNECT_MAX = int(os.getenv("MQTT_RECONNECT_MAX", "120"))

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("mqtt_bridge")


out_path = Path(OUT_CSV)
out_path.parent.mkdir(parents=True, exist_ok=True)
HEADER = ["sensor_id", "umidade", "nutriente", "ts"]

def safe_write_row(row: dict):
    write_header = not out_path.exists()
    try:
        with out_path.open("a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=HEADER)
            if write_header:
                writer.writeheader()
            to_write = {k: row.get(k, "") for k in HEADER}
            writer.writerow(to_write)
    except Exception as e:
        logger.exception("Falha ao gravar CSV: %s", e)



def on_connect(client, userdata, flags, reasonCode, properties=None):
    
    try:
        rc = int(reasonCode) if reasonCode is not None else 0
    except Exception:
        rc = reasonCode
    
    try:
        conn_str = mqtt.connack_string(rc)
    except Exception:
        conn_str = str(rc)
    if rc == 0:
        logger.info("Conectado ao broker %s:%s (resultado=%s)", BROKER, PORT, conn_str)
        client.subscribe(TOPIC, qos=QOS)
        logger.info("Inscrito em: %s (qos=%s)", TOPIC, QOS)
    else:
        logger.warning("Falha na conexão, result code: %s", conn_str)

def on_message(client, userdata, msg, properties=None):
    payload = msg.payload.decode("utf-8", errors="ignore")
    logger.debug("Mensagem recebida em %s: %s", msg.topic, payload)
    try:
        data = json.loads(payload)
        normalized = {
            "sensor_id": data.get("sensor_id") or data.get("id") or data.get("device"),
            "umidade": data.get("umidade") or data.get("humidity"),
            "nutriente": data.get("nutriente") or data.get("nutrient"),
            "ts": data.get("ts") or data.get("timestamp") or time.strftime("%Y-%m-%dT%H:%M:%S")
        }
        safe_write_row(normalized)
    except json.JSONDecodeError:
        parts = [p.strip() for p in payload.split(",")]
        if len(parts) >= 3:
            row = {
                "sensor_id": parts[0],
                "umidade": parts[1],
                "nutriente": parts[2],
                "ts": parts[3] if len(parts) > 3 else time.strftime("%Y-%m-%dT%H:%M:%S")
            }
            safe_write_row(row)
        else:
            logger.warning("Payload não reconhecido e não gravado: %s", payload)

def on_disconnect(client, userdata, reasonCode, properties=None):
    try:
        rc = int(reasonCode) if reasonCode is not None else 0
    except Exception:
        rc = reasonCode
    try:
        rc_str = mqtt.error_string(rc) if isinstance(rc, int) else str(rc)
    except Exception:
        rc_str = str(rc)
    logger.warning("Desconectado do broker (rc=%s). Cliente tentará reconectar automaticamente. Reason: %s", rc, rc_str)

def on_subscribe(client, userdata, mid, granted_qos, properties=None):
    logger.info("Subscribe OK (mid=%s, qos=%s)", mid, granted_qos)

def on_log(client, userdata, level, buf):
    logger.debug("paho-mqtt: %s", buf)


def create_client():
    """
    Use Callback API v2 (if paho supports) and MQTT v3.1.1 protocol for widest broker compatibility.
    If your paho version is <2.x, you may need to adjust or install a newer paho.
    """
    
    try:
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=CLIENT_ID, protocol=mqtt.MQTTv311)
    except Exception:
        
        client = mqtt.Client(client_id=CLIENT_ID, protocol=mqtt.MQTTv311)

    
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect
    client.on_subscribe = on_subscribe
    

    
    try:
        client.reconnect_delay_set(RECONNECT_MIN, RECONNECT_MAX)
    except Exception:
        
        try:
            client.reconnect_delay_set(RECONNECT_MIN, RECONNECT_MAX, False)
        except Exception:
            pass

    
    try:
        will_topic = "farmtech/status"
        will_payload = json.dumps({"client": CLIENT_ID, "status": "offline"})
        client.will_set(will_topic, payload=will_payload, qos=0, retain=True)
    except Exception:
        pass

    
    try:
        client.max_inflight_messages_set(20)
        client.max_queued_messages_set(0)
    except Exception:
        pass

    return client


def main():
    client = create_client()

    
    attempt = 0
    max_attempts = 10  
    while True:
        try:
            logger.info("Tentando conectar ao broker %s:%s (attempt %s)", BROKER, PORT, attempt + 1)
            client.connect(BROKER, PORT, keepalive=KEEPALIVE)
            break
        except Exception as e:
            attempt += 1
            logger.warning("Falha ao conectar: %s", e)
            delay = min(RECONNECT_MIN * (2 ** attempt), RECONNECT_MAX)
            logger.info("Aguardando %s segundos antes de novo attempt...", delay)
            time.sleep(delay)
            if max_attempts and attempt >= max_attempts:
                logger.error("Número máximo de tentativas alcançado. Encerrando.")
                sys.exit(1)

    
    client.loop_start()

    
    def _shutdown(sig, frame):
        logger.info("Sinal recebido (%s). Encerrando...", sig)
        try:
            client.loop_stop()
            client.disconnect()
        except Exception:
            pass
        sys.exit(0)

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        _shutdown("KeyboardInterrupt", None)


if __name__ == "__main__":
    main()
