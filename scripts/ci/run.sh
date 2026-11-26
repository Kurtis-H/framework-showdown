#!/usr/bin/env bash
# Run the whole test plan once with one framework, writing JUnit XML to
# $JUNIT_FILE. scripts/measure.py calls this once per run.
set -euo pipefail
root="$(cd "$(dirname "$0")/../.." && pwd)"
case "$1" in
  playwright) cd "$root/web/playwright" && exec npx playwright test ;;
  cypress)    cd "$root/web/cypress" && exec npx cypress run ;;
  appium)     cd "$root/mobile/appium" && exec npx wdio run wdio.conf.ts ;;
  maestro)
    # Maestro's setup scripts run here on the host, so they reach the API on
    # localhost; the app on the emulator uses 10.0.2.2.
    cd "$root/mobile/maestro" && exec "$HOME/.maestro/bin/maestro" test . \
      -e API_URL="${API_URL:-http://localhost:8000}" --format junit --output "$JUNIT_FILE" ;;
  *) echo "unknown framework: $1" >&2; exit 2 ;;
esac
