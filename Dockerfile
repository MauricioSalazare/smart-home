FROM python:3.11-slim
LABEL authors="Mauricio"

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 1883
ENV PYTHONBUFFERED=1

ENTRYPOINT ["python", "main.py"]