FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y libpq-dev gcc && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copying the modular app structure
COPY app/ app/

EXPOSE 8000

ENV PYTHONUNBUFFERED=1
# Entry point updated to the new module location
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
