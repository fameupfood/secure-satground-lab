FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY sat_agentd.py orbit_model.py ./

CMD ["python", "sat_agentd.py"]