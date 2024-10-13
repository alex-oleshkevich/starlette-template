#!/usr/bin/env bash

export APP_ENV=test
export APP_DEBUG=1

alembic upgrade head
pytest
