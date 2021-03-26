FROM python:3.9-slim as poetry

ARG POETRY_VERSION='1.1.5'
ARG SITE_PACKAGES_PATH='/usr/local/lib/python3.9/site-packages'

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

FROM python:3.9-slim as dev
COPY --from=build-dev ${SITE_PACKAGES_PATH} ${SITE_PACKAGES_PATH}
COPY . /app/
WORKDIR /app
ENTRYPOINT ["python", "-m", "nachomemes.bot", "-d"]

FROM python:3.9-slim as prod
COPY --from=build-prod ${SITE_PACKAGES_PATH} ${SITE_PACKAGES_PATH}
COPY . /app/
WORKDIR /app
ENTRYPOINT ["python", "-m", "nachomemes.bot"]
