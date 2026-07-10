import os
import json
import paho.mqtt.client as mqtt
from paho.mqtt.client import CallbackAPIVersion
from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS, WritePrecision

MQTT_BROKER = os.getenv('MQTT_BROKER', 'emqx')
MQTT_PORT = int(os.getenv('MQTT_PORT', '1883'))
MQTT_TOPIC = os.getenv('MQTT_TOPIC', 'data/+/batch')
INFLUX_URL = os.getenv('INFLUX_URL', 'http://influxdb:8086')
INFLUX_TOKEN = os.getenv('INFLUX_TOKEN', '')
INFLUX_ORG = os.getenv('INFLUX_ORG', 'calit2')
INFLUX_BUCKET = os.getenv('INFLUX_BUCKET', 'calit2-bucket')

influx = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
write = influx.write_api(write_options=SYNCHRONOUS)


def on_connect(client, userdata, flags, reason_code, properties):
    print(f"[MQTT] Connected to {MQTT_BROKER}:{MQTT_PORT} (rc={reason_code})")
    client.subscribe(MQTT_TOPIC)
    print(f"[MQTT] Subscribed to {MQTT_TOPIC}")


def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload)
        device = payload["device_id"]
        bucket = payload.get("bucket") or INFLUX_BUCKET
        lines = []
        for s in payload["samples"]:
            lines.append(f"voltage,device_id={device} value={s['v']} {s['t']}")
        write.write(
            bucket=bucket,
            record="\n".join(lines),
            write_precision=WritePrecision.MS,
        )
        print(f"[INFLUX] Wrote {len(lines)} samples for device {device} → {bucket}")
    except Exception as e:
        print(f"[ERROR] Failed to process message: {e}")


mqttc = mqtt.Client(CallbackAPIVersion.VERSION2)
mqttc.on_connect = on_connect
mqttc.on_message = on_message
mqttc.connect(MQTT_BROKER, MQTT_PORT)
mqttc.loop_forever()
