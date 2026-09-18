#!/usr/bin/env bash
# Site pipeline: pytest (unit + structural guards), offline check of the Cloudflare config (wrangler
# dry-run), end-to-end scenario + GUI goldens.
# No build: site/ is served as is, exactly the folder wrangler deploys.
set -uo pipefail
REPO="${REPO:-/repo}"
WRANGLER_OUT="${WRANGLER_OUT:-/tmp/wrangler-out}"   # dry-run output, outside the mounted repo
source "$REPO/test/ci/pipeline.sh"
pipeline_mode "${1:-}"
cd "$REPO/test/site"
PYTEST_RC=$SKIPPED WRANGLER_RC=$SKIPPED WRANGLER_DETAIL="" E2E_RC=$SKIPPED E2E_DETAIL=""

if runs_tests; then
  python -m pytest -q --color=no -p no:cacheprovider $(pytest_report_args "site")
  PYTEST_RC=$?

  # wrangler.jsonc and site/ as Workers Builds would deploy them, without account or network: the pinned
  # wrangler of the image (package-lock.json) validates the config, reads the assets and stops before upload.
  rm -rf "$WRANGLER_OUT"
  WRANGLER_DETAIL="wrangler $(wrangler --version 2>/dev/null | tail -n 1)"
  (cd "$REPO" && wrangler deploy --dry-run --outdir "$WRANGLER_OUT")
  WRANGLER_RC=$?
fi

if runs_goldens; then
  SHOTS="$(goldens_dir site)"
  APP_STATIC="$REPO/site" python screenshots.py "$SHOTS"   # end-to-end scenario + captures
  E2E_RC=$?
  E2E_DETAIL="$(ls -1 "$SHOTS"/*.png 2>/dev/null | wc -l | tr -d ' ') images"
fi

summary_line pytest "$PYTEST_RC"; summary_line wrangler "$WRANGLER_RC" "$WRANGLER_DETAIL"
summary_line e2e "$E2E_RC" "$E2E_DETAIL"
all_ok "$PYTEST_RC" "$WRANGLER_RC" "$E2E_RC"
