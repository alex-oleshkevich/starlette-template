#!/usr/bin/env bash

set -e

export APP_ENV=unittest
export APP_DEBUG=1

pytest --cov-report term --cov-report html --cov=app $@
