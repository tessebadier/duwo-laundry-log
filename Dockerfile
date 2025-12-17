FROM python:3.10-slim

RUN apt-get update && apt-get install -y

COPY requirements.txt .
COPY multiposs-nl-chain.pem .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY .env .
COPY main.py .

CMD ["python", "./main.py"]