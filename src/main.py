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


def on_message(client, userdata, msg):
    payload = json.loads(msg.payload)
    device = payload["device_id"]
    lines = []
    for s in payload["samples"]:
        lines.append(f"voltage,device_id={device} value={s['v']} {s['t']}")
    write.write(bucket=INFLUX_BUCKET, record="\n".join(lines))


mqttc = mqtt.Client()
mqttc.on_message = on_message
mqttc.connect(MQTT_BROKER, MQTT_PORT)
mqttc.subscribe(MQTT_TOPIC)
mqttc.loop_forever()
