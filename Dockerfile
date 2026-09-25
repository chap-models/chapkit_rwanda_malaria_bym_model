# chapkit_rwanda_malaria_bym_model Dockerfile
# chapkit-r-inla ships R 4.5 + INLA + the spatial / time-series stack (sf, spdep,
# dlnm, fmesher, ...) preinstalled - all the libraries scripts/predict.R needs.
# The image is amd64-only (INLA ships x86_64 binaries only), so the FROM line
# pins linux/amd64 via a build ARG; on Apple Silicon this runs under Rosetta.
ARG BASE_PLATFORM=linux/amd64
FROM --platform=${BASE_PLATFORM} ghcr.io/dhis2-chap/chapkit-r-inla:latest

# Build steps run as root; the service runs as the unprivileged chapkit user
# (uid/gid 1000). Newer chapkit base images ship the user, older ones do not,
# so create it only when missing.
USER root
RUN id -u chapkit >/dev/null 2>&1 \
    || (groupadd --gid 1000 chapkit && useradd --uid 1000 --gid 1000 --no-create-home --shell /usr/sbin/nologin chapkit)

WORKDIR /work
COPY pyproject.toml uv.lock ./

RUN --mount=type=cache,target=/root/.cache/uv \
    UV_PROJECT_ENVIRONMENT=/app/.venv uv sync --frozen --no-dev --no-install-project

# Commit the image was built from, reported as git_revision on /api/v1/info.
# The publish workflow passes it; locally: --build-arg GIT_REVISION=$(git rev-parse HEAD)
ARG GIT_REVISION=""
ENV GIT_REVISION=${GIT_REVISION}

COPY main.py ./
COPY scripts/ ./scripts/

# Writable paths at runtime are /work/data (the SQLite database, a volume in
# compose.yml) and /tmp, where chapkit unpacks its ML workspaces and R keeps
# its tempdir: predict.R writes its .graph file, the predictions CSV and
# model.rds there. Everything else stays read-only.
RUN mkdir -p /work/data && chown -R chapkit:chapkit /work/data

# The chapkit user has no home directory, so point HOME and the cache dirs at
# /tmp; R wants a writable home at startup, as do the Python-side caches.
ENV HOME=/tmp \
    MPLCONFIGDIR=/tmp \
    XDG_CACHE_HOME=/tmp/.cache

USER chapkit

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl --fail http://localhost:8000/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
