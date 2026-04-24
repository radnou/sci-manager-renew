FROM python:3.12-slim

WORKDIR /app

# Installer curl pour les health checks
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Run as non-root user (security: container escape mitigation)
RUN addgroup --system app && adduser --system --ingroup app app

COPY --chown=app:app app ./app
COPY --chown=app:app templates ./templates

USER app

EXPOSE 8000

# Production-ready command avec graceful shutdown
CMD ["uvicorn", "app.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "2", \
     "--timeout-keep-alive", "75", \
     "--timeout-graceful-shutdown", "30", \
     "--proxy-headers", \
     "--forwarded-allow-ips", "*"]
