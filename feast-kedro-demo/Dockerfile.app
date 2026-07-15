# Image for the Kedro inference service.
#
# Build from the PARENT directory so the local `kedro-datasets` path dependency
# is in the build context. docker-compose does this for you (context: ..); by
# hand:
#   docker build -f feast-kedro-demo/Dockerfile.app -t feast-kedro-inference ..
FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app
# The demo project depends on ../kedro-datasets (editable path dep), so both
# directories must be copied.
COPY kedro-datasets /app/kedro-datasets
COPY feast-kedro-demo /app/feast-kedro-demo

WORKDIR /app/feast-kedro-demo
RUN uv sync

EXPOSE 8000
CMD ["uv", "run", "uvicorn", "feast_kedro_demo.service:app", "--host", "0.0.0.0", "--port", "8000"]
