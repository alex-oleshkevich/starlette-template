#!/usr/bin/env bash

alembic upgrade head
python -m coverage run --branch --parallel-mode -m pytest
python -m coverage combine
python -m coverage html --skip-covered --skip-empty
python -m coverage report --fail-under=100
