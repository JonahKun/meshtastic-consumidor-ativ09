FROM python:3.14-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY consumidor/ ./consumidor/

# Usuario sem privilegios; logs em volume (/app/logs)
RUN useradd --create-home --uid 1000 app && mkdir -p /app/logs && chown -R app /app/logs
USER app
VOLUME ["/app/logs"]

# Configuracao toda por variaveis de ambiente (--env-file .env). O .env NAO entra na imagem.
CMD ["python", "-m", "consumidor"]
