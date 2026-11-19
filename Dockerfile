FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src \
    REPRO360_DB=/data/repro360.db

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN useradd --create-home appuser && mkdir -p /data && chown -R appuser /data /app
USER appuser

EXPOSE 8000 8501
# Default: API. The compose file overrides the command for the dashboard.
CMD ["uvicorn", "repro360.api:app", "--host", "0.0.0.0", "--port", "8000"]
