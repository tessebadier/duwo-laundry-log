FROM python:3.10-slim

RUN apt-get update && apt-get install -y

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY dashboard.py .

#CMD ["python", "dashboard.py"]
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8050", "dashboard:server"]
