FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt ./
COPY src ./src

ENV TELEMETRY_DB=/data/telemetry.db

CMD ["python", "src/monitor.py"]
