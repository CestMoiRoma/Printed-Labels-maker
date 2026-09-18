# The one pinned image: lint, tests and GUI goldens, locally (just ...) and in CI.
# Build context: test/, plus the repository root as the named context "repo" for package.json and its lock:
#   docker build --platform linux/amd64 --build-context repo=. -f test/ci/Dockerfile test
# Base: node:22-bookworm-slim, linux/amd64 manifest (node is needed by prettier, and by wrangler in phase 3).
FROM node:22-bookworm-slim@sha256:4d676821dff059fd00d277ee4261ef34ea712317fed0737c03941481b5760c96

ARG DEBIAN_SNAPSHOT=20260915T202328Z
ARG TREEFMT_VERSION=2.6.0
ARG TREEFMT_SHA256=2deff4c0f381d560784c5632cf5860da712891ccd9185306e73d8ba37778ab7f
ARG PRETTIER_VERSION=3.9.8

ENV DEBIAN_FRONTEND=noninteractive PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
    RUFF_CACHE_DIR=/tmp/ruff-cache LANG=C.UTF-8 TZ=UTC PATH=/venv/bin:$PATH

# OS packages from a fixed snapshot: same versions on every build
RUN rm -f /etc/apt/sources.list.d/debian.sources \
 && printf '%s\n' \
    "deb [check-valid-until=no] http://snapshot.debian.org/archive/debian/${DEBIAN_SNAPSHOT} bookworm main" \
    "deb [check-valid-until=no] http://snapshot.debian.org/archive/debian-security/${DEBIAN_SNAPSHOT} bookworm-security main" \
    > /etc/apt/sources.list \
 && apt-get -o Acquire::Retries=5 update \
 && apt-get -o Acquire::Retries=5 install -y --no-install-recommends \
    ca-certificates curl git python3 python3-venv \
    fonts-dejavu-core fonts-noto-core fonts-noto-color-emoji \
 && rm -rf /var/lib/apt/lists/*

# treefmt + prettier
RUN curl -fsSL -o /tmp/treefmt.tgz \
      "https://github.com/numtide/treefmt/releases/download/v${TREEFMT_VERSION}/treefmt_${TREEFMT_VERSION}_linux_amd64.tar.gz" \
 && echo "${TREEFMT_SHA256}  /tmp/treefmt.tgz" | sha256sum -c - \
 && tar -xzf /tmp/treefmt.tgz -C /usr/local/bin treefmt && rm /tmp/treefmt.tgz \
 && npm install -g --no-audit --no-fund "prettier@${PRETTIER_VERSION}" && npm cache clean --force

# Python: lock first (pinned closure), then the requirements offline (fails if the lock misses something)
RUN python3 -m venv /venv
COPY ci/requirements.lock ci/requirements.txt /tmp/ci/
COPY site/requirements-test.txt /tmp/site/requirements-test.txt
RUN pip install --no-cache-dir -r /tmp/ci/requirements.lock \
 && pip install --no-cache-dir --no-index -r /tmp/ci/requirements.txt \
 && playwright install --with-deps chromium && rm -rf /var/lib/apt/lists/*

# Playwright's deps pull GNU Unifont / FreeFont, which fontconfig then prefers for emoji: reject them
COPY ci/fonts.conf /etc/fonts/conf.d/99-screenshots.conf
RUN fc-cache -f

# Wrangler, for the offline check of wrangler.jsonc (wrangler deploy --dry-run in test/site/run-tests.sh),
# pinned by the repository's package.json and package-lock.json: npm ci fails the build if the lock is
# incomplete or out of step with package.json. Installed outside /repo, on PATH. Nothing phones home:
# no telemetry, no error reports, and no banner (its update check queries the npm registry).
COPY --from=repo package.json package-lock.json /opt/wrangler/
RUN cd /opt/wrangler && npm ci --no-audit --no-fund --loglevel=error && npm cache clean --force
ENV PATH=/opt/wrangler/node_modules/.bin:$PATH \
    WRANGLER_SEND_METRICS=false WRANGLER_SEND_ERROR_REPORTS=false WRANGLER_HIDE_BANNER=true

WORKDIR /repo
