#!/usr/bin/env bash

# This script is used to run tests in an isolated and reproducible Docker environment.
# It builds the Docker images, runs the tests, and then removes the containers.
# This is useful for running tests in a CI/CD pipeline or locally without installing dependencies.

set -e

export POSTGRES_PORT=55432
export REDIS_PORT=56379

mkdir -p build
docker compose -f compose.yml build --pull
docker compose -f compose.yml run \
    --rm \
    --volume $(pwd)/build/:/code/build \
    --remove-orphans app \
    alembic upgrade head && ./scripts/testcover.sh $@
