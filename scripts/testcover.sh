#!/usr/bin/env bash

# Run unit tests with coverage.

set -e

DIRNAME=$(dirname $BASH_SOURCE[0])
$DIRNAME/test.sh --cov-report term --cov-report html --cov=app --cov=tests $@
