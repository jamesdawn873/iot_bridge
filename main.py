import paho.mqtt.client as mqtt
import influxdb_client
from influxdb_client.client.write_api import SYNCHRONOUS
import struct
import os
import time

MQTT_BROKER = os.getenv('MQTT_BROKER', 'emqx')
MQTT_PORT = int(os.getenv('MQTT_PORT', 1883))
INFLUX_URL = os.getenv('INFLUX_URL', 'http://influxdb:8086')
INFLUX_TOKEN = os.getenv('INFLUX_TOKEN', 'YOUR_TOKEN_HERE')
INFLUX_ORG = os.getenv('INFLUX_ORG', 'YOUR_ORG')
INFLUX_BUCKET = os.getenv('INFLUX_BUCKET', 'sensor_data')

client_db = influxdb_client.InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
write_api = client_db.write_api(write_options=SYNCHRONOUS)


def on_connect(client, userdata, flags, rc):
    print("Connected to MQTT Broker!")
    client.subscribe("data/+/batch")


def on_message(client, userdata, msg):
    try:
        parts = msg.topic.split('/')
        device_id = parts[1]

        payload_size = len(msg.payload)
        count = payload_size // 4
        if count != 50:
            print(f"Warning: Expected 50 floats (200 bytes), got {payload_size} bytes")
            return

        values = struct.unpack(f'<{count}f', msg.payload)

        points = []
        now_ns = time.time_ns()
        interval_ns = 100 * 1_000_000  # 100ms in nanoseconds

        for i in range(count):
            offset = (count - 1 - i) * interval_ns
            timestamp = now_ns - offset

            p = influxdb_client.Point("analog_signal") \
                .tag("device_id", device_id) \
                .field("voltage", float(values[i])) \
                .time(timestamp, influxdb_client.WritePrecision.NS)
            points.append(p)

        write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=points)
        print(f"Stored {count} samples from {device_id}")

    except Exception as e:
        print(f"Error processing message: {e}")


client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

print(f"Connecting to {MQTT_BROKER}...")
client.connect(MQTT_BROKER, MQTT_PORT, 60)
client.loop_forever()