FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8000

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY --chown=10001:10001 . .
RUN mkdir -p logs reports/drift final_model Artifacts && chown -R 10001:10001 /app
USER 10001

EXPOSE 8000
CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port ${PORT:-8000}"]
