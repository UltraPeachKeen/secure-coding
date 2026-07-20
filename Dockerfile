FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN addgroup --system app && adduser --system --ingroup app app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY --chown=app:app . .
RUN mkdir -p /app/instance /app/uploads && chown -R app:app /app/instance /app/uploads

USER app
EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5000/healthz', timeout=2)"

CMD ["sh", "-c", "flask --app run.py init-db && exec gunicorn --workers 1 --threads 4 --bind 0.0.0.0:5000 --access-logfile - run:app"]

