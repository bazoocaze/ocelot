#!/bin/bash
SCRIPT_DIR="$(realpath "$(dirname "$0")")"
PIPFILE_PATH="${SCRIPT_DIR}/Pipfile"
ENTRYPOINT="${SCRIPT_DIR}/ocelot.py"
PIPENV_PIPFILE="$PIPFILE_PATH" pipenv run python "$ENTRYPOINT" "$@"
