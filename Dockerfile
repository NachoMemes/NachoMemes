FROM python:3.10.1-slim as poetry

ARG POETRY_VERSION='1.1.5'

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_NO_CACHE_DIR=off
ENV PIP_DISABLE_PIP_VERSION_CHECK=on
ENV PIP_DEFAULT_TIMEOUT=100



RUN python -m pip install --no-cache-dir "poetry==${POETRY_VERSION}" --user

FROM poetry as build
WORKDIR /app
COPY poetry.lock pyproject.toml /app/

RUN python -m poetry export --dev -f requirements.txt --output requirements-dev.txt && \
  python -m poetry export -f requirements.txt --output requirements.txt

FROM python:3.10.1-slim as dev
COPY --from=build /app/requirements-dev.txt /app/requirements.txt
RUN apt-get update && apt-get install gcc=4:10.2.1-1 -y
WORKDIR /app
RUN python -m pip install --no-cache-dir -r requirements.txt
COPY . /app/
ENTRYPOINT ["python", "-m", "nachomemes.bot", "-d"]

FROM python:3.10.1-slim as prod
WORKDIR /app
RUN apt-get update && apt-get install gcc=4:10.2.1-1 -y && rm  -rf /var/lib/apt/lists/*
COPY --from=build /app/requirements.txt /app/requirements.txt
RUN python -m pip install --no-cache-dir -r requirements.txt
COPY . /app/
ENTRYPOINT ["python", "-m", "nachomemes.bot"]
