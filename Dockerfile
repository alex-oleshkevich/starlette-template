# ------------------------------------------------------
# STAGE 1 - build frontend assets
# ------------------------------------------------------
FROM node:22-alpine AS frontend
ARG PROJECT=app
WORKDIR /code

ADD package.json package-lock.json ./
RUN npm install
ADD . .
RUN npm run build

# ------------------------------------------------------
# STAGE 2 -- build application image
# ------------------------------------------------------
FROM python:3.12-slim
EXPOSE 8000
WORKDIR /code
ARG PROJECT=app
ARG POETRY_INSTALL_ARGS=''
ARG RUN_DEPS='gettext nano procps curl'
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_NO_CACHE_DIR=off
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

RUN --mount=type=cache,target=/var/lib/apt,sharing=locked \
    --mount=type=cache,target=/var/cache/apt,sharing=locked \
    set -xe \
    && apt update -y \
    && apt install -y --no-install-recommends $RUN_DEPS \
    && apt-get clean -y \
    && rm -rf /var/lib/apt/lists/*

ADD pyproject.toml poetry.lock ./
RUN --mount=type=cache,target=/var/lib/apt,sharing=locked \
    --mount=type=cache,target=/var/cache/apt,sharing=locked \
    set -xe \
    && BUILD_DEPS="git" \
    && apt update -y \
    && apt install -y --no-install-recommends $BUILD_DEPS \
    && update-ca-certificates \
    && pip install poetry --no-cache-dir \
    && poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-cache $POETRY_INSTALL_ARGS \
    && pip uninstall -y poetry \
    && pip cache purge || true \
    && rm -rf ~/.cache/pypoetry/{cache,artifacts} \
    && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false $BUILD_DEPS \
    && apt-get clean -y \
    && rm -rf /var/lib/apt/lists/*

ADD $PROJECT/ $PROJECT/
ADD alembic/ alembic/
ADD alembic.ini pybabel.ini ./
ADD manage.py ./
ADD deploy/docker/* /bin/
RUN ./manage.py locale compile

COPY --from=frontend /code/$PROJECT/resources/statics/ /code/$PROJECT/resources/statics/

CMD ["/bin/docker-run.sh"]
HEALTHCHECK --interval=10s --timeout=10s --start-period=5s --retries=3 CMD ["/bin/docker-healthcheck.sh"]

RUN groupadd -r app && useradd -d /code -M -u 1000 -g app app
USER app
SHELL ["/bin/bash"]

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
