#!/usr/bin/env bash

export APP_ENV=unittest
export APP_DEBUG=1

alembic upgrade head
