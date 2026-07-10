FROM python:3.12-slim

WORKDIR /app
RUN pip install paho-mqtt influxdb-client
COPY src/main.py .
CMD ["python", "-u", "main.py"]
