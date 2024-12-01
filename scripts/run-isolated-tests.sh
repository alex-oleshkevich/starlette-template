#!/usr/bin/env bash

# This script is used to run tests in an isolated and reproducible Docker environment.
# It builds the Docker images, runs the tests, and then removes the containers.
# This is useful for running tests in a CI/CD pipeline or locally without installing dependencies.

set -e

function cleanup {
    docker compose -f compose.yml down -v --remove-orphans
}

trap cleanup EXIT ERR

export APP_ENV=unittest
export POSTGRES_DB=postgres_test
export TEST_DATABASE_URL=postgresql+psycopg_async://postgres:postgres@postgres:5432/$POSTGRES_DB

mkdir -p build
docker compose build --pull
docker compose -f compose.yml run --rm app alembic upgrade head
docker compose -f compose.yml run --user 0 --rm app ./scripts/testcover.sh $@
