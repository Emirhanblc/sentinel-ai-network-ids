FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /service
COPY requirements-api.txt .
RUN pip install --no-cache-dir -r requirements-api.txt
COPY src src
COPY models/metrics.json models/metrics.json

RUN useradd --create-home ids
USER ids
EXPOSE 8000
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
