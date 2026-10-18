#!/bin/bash
set -euo pipefail
BASE="$(cd "$(dirname "$0")" && pwd)"
exec python3 "$BASE/scripts/relink.py" "$@"
