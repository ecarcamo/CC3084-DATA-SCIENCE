FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    MLFLOW_DISABLE_AGENT_HINT=1 \
    HOME=/tmp

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app app
COPY pipeline pipeline
COPY config config
COPY insumos insumos
COPY tests tests

ARG GIT_COMMIT=desconocido
ENV GIT_COMMIT=${GIT_COMMIT}

EXPOSE 8050 5000

CMD ["python", "-m", "app.main"]
