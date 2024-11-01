#!/usr/bin/env bash
set -e

# Run unit tests.

export APP_ENV=unittest
export APP_DEBUG=1

pytest $@
