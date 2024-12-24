# ------------------------------------------------------
# STAGE 1 - build frontend assets
# ------------------------------------------------------
FROM node:22-alpine AS frontend
WORKDIR /code

ARG PROJECT=app
ARG NPM_CONFIG_CACHE=/root/.npm

ADD package.json package-lock.json /code/
RUN --mount=type=cache,target=$NPM_CONFIG_CACHE,sharing=locked \
    npm install
ADD . .
RUN npm run build

# ------------------------------------------------------
# STAGE 2 -- build application image
# ------------------------------------------------------
FROM python:3.13-slim
EXPOSE 8000
WORKDIR /code

ARG PROJECT=app
ARG POETRY_INSTALL_ARGS=''
ARG RUN_DEPS='gettext nano procps curl'
ARG BUILD_DEPS='git'
ARG PIP_CACHE_DIR=/root/pip-cache
ARG POETRY_CACHE_DIR=/root/poetry-cache
ARG USERNAME=app

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
ENV PIP_CACHE_DIR=$PIP_CACHE_DIR
ENV POETRY_CACHE_DIR=$POETRY_CACHE_DIR
ENV POETRY_VIRTUALENVS_CREATE=0

RUN useradd -d /code -M -u 1000 $USERNAME

RUN --mount=type=cache,target=/var/lib/apt,sharing=locked \
    --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt/lists,sharing=locked \
    set -xe \
    && apt update -y \
    && apt install -y --no-install-recommends $RUN_DEPS

ADD pyproject.toml poetry.lock /code/
RUN --mount=type=cache,target=/var/lib/apt,sharing=locked \
    --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt/lists,sharing=locked \
    --mount=type=cache,target=$PIP_CACHE_DIR,sharing=locked \
    --mount=type=cache,target=$POETRY_CACHE_DIR,sharing=locked \
    set -xe \
    && apt update -y \
    && apt install -y --no-install-recommends $BUILD_DEPS \
    && update-ca-certificates \
    && pip install poetry \
    && poetry install --no-interaction $POETRY_INSTALL_ARGS

USER app
ADD --chown=$USERNAME $PROJECT/ $PROJECT/
ADD alembic/ alembic/
ADD alembic.ini pybabel.ini manage.py ./
ADD deploy/docker/* /bin/
RUN ./manage.py locale compile

COPY --from=frontend /code/$PROJECT/resources/statics/ /code/$PROJECT/resources/statics/

SHELL ["/bin/bash"]
CMD ["/bin/docker-run.sh"]
HEALTHCHECK --interval=10s --timeout=10s --start-period=5s --retries=3 CMD ["/bin/docker-healthcheck.sh"]

ARG RELEASE_ID=''
ENV RELEASE_ID=$RELEASE_ID

ARG RELEASE_BRANCH=''
ENV RELEASE_BRANCH=$RELEASE_BRANCH

ARG RELEASE_COMMIT=''
ENV RELEASE_COMMIT=$RELEASE_COMMIT

ARG RELEASE_DATE=''
ENV RELEASE_DATE=$RELEASE_DATE

ARG REPO_URL=''
LABEL org.opencontainers.image.source=$REPO_URL
