### STAGE 1 ###
FROM node:20-alpine AS frontend
ARG PROJECT=app
WORKDIR /code

ADD package.json package-lock.json ./
RUN npm install
ADD . .
RUN npm run build

### STAGE 2 ###
FROM python:3.12-slim
ARG REPO_URL=''
LABEL org.opencontainers.image.source $REPO_URL
ARG PROJECT=rvapp

ENV PIP_NO_CACHE_DIR=off
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
EXPOSE 8000
WORKDIR /code

RUN set -xe \
    && RUN_DEPS="gettext nano procps curl" \
    && apt update -y \
    && apt install -y --no-install-recommends $RUN_DEPS \
    && apt-get clean -y \
    && rm -rf /var/lib/apt/lists/*

ADD pyproject.toml poetry.lock ./
RUN set -xe \
    && BUILD_DEPS="git" \
    && apt update -y \
    && apt install -y --no-install-recommends $BUILD_DEPS \
    && update-ca-certificates \
    && pip install poetry --no-cache-dir \
    && poetry config virtualenvs.create false \
    && poetry install --no-interaction --without dev --no-root --no-cache \
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

COPY --from=frontend /code/$PROJECT/statics/ $PROJECT/statics/
RUN groupadd -r app && useradd -r -m -g app app

ARG RELEASE_ID=''
ENV RELEASE_ID=$RELEASE_ID

ARG RELEASE_BRANCH=''
ENV RELEASE_BRANCH=$RELEASE_BRANCH

ARG RELEASE_COMMIT=''
ENV RELEASE_COMMIT=$RELEASE_COMMIT

ARG RELEASE_DATE=''
ENV RELEASE_DATE=$RELEASE_DATE

#RUN pybabel compile -d $PROJECT/locales/
RUN echo "Branch = ${GIT_BRANCH} - Commit SHA = ${GIT_REVISION} - Built at = " ${RELEASE_DATE} > ./version
SHELL ["/bin/bash"]

ADD deploy/docker/scripts/* /bin/
CMD ["/bin/docker-run.sh"]
HEALTHCHECK \
    --interval=10s \
    --timeout=10s \
    --start-period=5s \
    --retries=3 \
    CMD ["/bin/docker-healthcheck.sh"]
