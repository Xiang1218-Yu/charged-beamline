#!/bin/sh
set -eu
cp "$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)/beamline_sim/core.py" "${TARGET_DIR:-/app}/beamline_sim/core.py"
cp "$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)/beamline_sim/__main__.py" "${TARGET_DIR:-/app}/beamline_sim/__main__.py"
