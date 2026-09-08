# chapkit_rwanda_malaria_bym_model Dockerfile
# chapkit-r-inla ships R 4.5 + INLA + the spatial / time-series stack (sf, spdep,
# dlnm, fmesher, ...) preinstalled - all the libraries scripts/predict.R needs.
# The image is amd64-only (INLA ships x86_64 binaries only), so the FROM line
# pins linux/amd64 via a build ARG; on Apple Silicon this runs under Rosetta.
ARG BASE_PLATFORM=linux/amd64
FROM --platform=${BASE_PLATFORM} ghcr.io/dhis2-chap/chapkit-r-inla:latest

USER root

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

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl --fail http://localhost:8000/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
