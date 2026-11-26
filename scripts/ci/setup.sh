#!/usr/bin/env bash
# Install one framework from scratch. scripts/measure.py times this.
set -euo pipefail
root="$(cd "$(dirname "$0")/../.." && pwd)"
case "$1" in
  playwright)
    cd "$root/web/playwright" && npm ci --no-audit --no-fund && npx playwright install --with-deps chromium ;;
  cypress)
    # npm ci also downloads Cypress's own browser bundle.
    cd "$root/web/cypress" && npm ci --no-audit --no-fund && npx cypress verify ;;
  appium)
    cd "$root/mobile/appium" && npm ci --no-audit --no-fund && npx appium driver install uiautomator2 ;;
  maestro)
    curl -fsSL "https://get.maestro.mobile.dev" | bash && "$HOME/.maestro/bin/maestro" --version ;;
  *) echo "unknown framework: $1" >&2; exit 2 ;;
esac
