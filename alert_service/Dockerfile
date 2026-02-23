FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copying modular structure
COPY app/ app/

# Disable output buffering for real-time logging
ENV PYTHONUNBUFFERED=1

# Entry point updated to modular path
CMD ["python", "-u", "-m", "app.main"]
