FROM python:3.9-slim as poetry

ARG BUILD_ESSENATIAL_VERSION='12.6*'
ARG POETRY_VERSION='1.1.5'

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_NO_CACHE_DIR=off
ENV PIP_DISABLE_PIP_VERSION_CHECK=on
ENV PIP_DEFAULT_TIMEOUT=100

RUN pip3 install "poetry==${POETRY_VERSION}"

FROM poetry as build-dev
WORKDIR /app
COPY poetry.lock pyproject.toml /app/
RUN poetry config virtualenvs.create false \
  && poetry install --no-interaction --no-ansi

FROM poetry as build-prod
WORKDIR /app
COPY poetry.lock pyproject.toml /app/
RUN poetry config virtualenvs.create false \
  && poetry install --no-dev --no-interaction --no-ansi

FROM build-dev as dev
COPY --from=build-dev /app /app
COPY . /app/
WORKDIR /app
ENTRYPOINT	["python", "-m", "nachomemes.bot", "-d"]

FROM build-prod as prod
COPY --from=build-prod /app /app
COPY . /app/
WORKDIR /app
ENTRYPOINT	["python", "-m", "nachomemes.bot"]
