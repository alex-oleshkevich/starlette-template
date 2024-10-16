#!/usr/bin/env bash
# This script is used to compose the project without port conflicts.

set -e

export APP_PORT=58000
export POSTGRES_PORT=55432
export REDIS_PORT=56379

docker compose -f compose.yml build
docker compose -f compose.yml up $@
