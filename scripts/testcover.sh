#!/usr/bin/env bash

set -e

export APP_ENV=unittest
export APP_DEBUG=1

python -m coverage run -m pytest $@
python -m coverage combine
python -m coverage html
python -m coverage report
