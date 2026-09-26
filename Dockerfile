# syntax=docker/dockerfile:1
FROM python:3.11-slim

WORKDIR /app

# git isn't required by the engine today, but risk-score/churn work (Phase 4)
# will want it; cheap to include now rather than re-touch this file then.
RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
COPY repoguard_engine ./repoguard_engine
COPY demo-repo ./demo-repo

# Playwright's Python package installs here; the Chromium *browser* binary
# does not (kept out to keep the image small). Visual checks (capture_screenshot,
# collect_console_logs, check_accessibility) will report a graceful per-call
# error until it's added — see repoguard_engine/visual.py's except Exception
# handling. To enable them, add:
#   RUN playwright install --with-deps chromium
#
# [vertex] extra included so /api/summary's ok=true path actually works on
# the deployed service (REPOGUARD_AI_PROVIDER=vertex, set via cd.yml) --
# without it, get_provider() fails loud with "google-genai is not
# installed" instead of generating real text. [ai] (watsonx) stays out:
# vertex is this deployment's configured provider, and Application Default
# Credentials (the runtime service account) are what watsonx has no
# equivalent to -- it needs a separate WATSONX_APIKEY nobody has set here.
RUN pip install --no-cache-dir -e ".[vertex]"

EXPOSE 8080

# Cloud Run injects $PORT; default to 8080 for a plain `docker run -p 8080:8080`.
# Shell form (not exec form) so the ${PORT:-8080} substitution actually happens.
CMD repoguard serve --host 0.0.0.0 --port ${PORT:-8080}
