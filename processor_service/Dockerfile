FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y libpq-dev gcc && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copying modular structure
COPY app/ app/

ENV PYTHONUNBUFFERED=1
# Entry point updated to modular path
CMD ["python", "-u", "-m", "app.main"]
