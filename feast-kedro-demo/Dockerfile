# Image for the Kedro/Feast workspace (apply, ingest, and the inference service).
#
# Build from the PARENT directory so the local `kedro-datasets` path dependency
# is in the build context (docker-compose sets context: ..):
#   docker build -f feast-kedro-demo/Dockerfile -t feast-kedro-demo ..
FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app
# The workspace depends on ../kedro-datasets (editable path dep), so both
# directories must be in the image.
COPY kedro-datasets /app/kedro-datasets
COPY feast-kedro-demo /app/feast-kedro-demo

WORKDIR /app/feast-kedro-demo
# Sync ALL workspace members (pipelines + services) into one venv. The root is a
# virtual (package=false) workspace, so without --all-packages the members'
# dependencies (feast, kedro, ...) are not installed.
RUN uv sync --all-packages

# Put the workspace venv on PATH so `feast`/`kedro`/`uvicorn` resolve directly,
# without relying on `uv run` from non-member subdirectories.
ENV PATH="/app/feast-kedro-demo/.venv/bin:${PATH}"

EXPOSE 8000
# Default: run the inference service. `apply`/`ingest` override this command.
CMD ["sh", "-c", "cd services && uvicorn inference_service.main:app --host 0.0.0.0 --port 8000"]
