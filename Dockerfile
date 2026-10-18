FROM python:3.10-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements-local.txt .
RUN pip install --no-cache-dir -r requirements-local.txt

RUN useradd --create-home --shell /usr/sbin/nologin appuser
COPY --chown=appuser:appuser app_local.py .
COPY --chown=appuser:appuser local_model/ ./local_model/
USER appuser

EXPOSE 8501

CMD ["streamlit", "run", "app_local.py", "--server.address", "0.0.0.0", "--server.port", "8501", "--server.headless", "true", "--browser.gatherUsageStats", "false"]