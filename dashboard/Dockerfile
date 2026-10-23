FROM python:3.12-slim

RUN apt-get update && apt-get install -y

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY assets ./assets/
COPY dashboard.py .

#CMD ["python", "dashboard.py"]
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:8050", "dashboard:server"]
