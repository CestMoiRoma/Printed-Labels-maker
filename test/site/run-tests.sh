#!/usr/bin/env bash
# Site pipeline: pytest (unit + structural guards), end-to-end scenario + GUI goldens.
# No build: site/ is served as is, exactly the folder wrangler deploys.
set -uo pipefail
REPO="${REPO:-/repo}"
source "$REPO/test/ci/pipeline.sh"
pipeline_mode "${1:-}"
cd "$REPO/test/site"
PYTEST_RC=$SKIPPED E2E_RC=$SKIPPED E2E_DETAIL=""

if runs_tests; then
  python -m pytest -q --color=no -p no:cacheprovider $(pytest_report_args "site")
  PYTEST_RC=$?
fi

if runs_goldens; then
  SHOTS="$(goldens_dir site)"
  APP_STATIC="$REPO/site" python screenshots.py "$SHOTS"   # end-to-end scenario + captures
  E2E_RC=$?
  E2E_DETAIL="$(ls -1 "$SHOTS"/*.png 2>/dev/null | wc -l | tr -d ' ') images"
fi

summary_line pytest "$PYTEST_RC"; summary_line e2e "$E2E_RC" "$E2E_DETAIL"
all_ok "$PYTEST_RC" "$E2E_RC"
