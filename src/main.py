import os
import json
import paho.mqtt.client as mqtt
from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS

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
    if reason_code == 0:
        client.subscribe(MQTT_TOPIC)
        print(f"[MQTT] Subscribed to {MQTT_TOPIC}")
    else:
        print(f"[MQTT] Connect failed (rc={reason_code})")


def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload)
        device = payload["device_id"]
        bucket = payload.get("bucket", INFLUX_BUCKET)
        lines = []
        for s in payload["samples"]:
            lines.append(f"voltage,device_id={device} value={s['v']} {s['t']}")
        write.write(bucket=bucket, record="\n".join(lines))
        print(f"[BRIDGE] {len(lines)} samples → {bucket} ({device})")
    except Exception as e:
        print(f"[BRIDGE] Error: {e}")


mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqttc.on_connect = on_connect
mqttc.on_message = on_message
mqttc.reconnect_delay_set(min_delay=1, max_delay=30)
mqttc.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
mqttc.loop_forever(retry_first_connection=True)
