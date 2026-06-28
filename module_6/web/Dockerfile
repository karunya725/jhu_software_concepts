FROM python:3.12-slim

WORKDIR /app

RUN groupadd --system appuser \
    && useradd --system --gid appuser appuser

COPY web/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=appuser:appuser web/ .
COPY --chown=appuser:appuser shared/ shared/

USER appuser

EXPOSE 5000

CMD ["python", "app.py"]