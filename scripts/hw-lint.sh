#!/usr/bin/env bash
# Run a hardware linter if it is installed; otherwise warn and pass (pre-commit hook helper).
# Usage: hw-lint.sh <tool> [args...] -- files...
set -euo pipefail
tool="$1"; shift
if ! command -v "$tool" >/dev/null 2>&1; then
  echo "hw-lint: $tool not installed, skipping" >&2
  exit 0
fi
exec "$tool" "$@"
