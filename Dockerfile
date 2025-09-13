FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Explicitly use port 8080 and increase timeout
CMD ["gunicorn", "app:app", "-b", "0.0.0.0:8080", "--timeout", "120", "--preload"]