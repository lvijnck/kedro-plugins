# Postgres instance for Feast's online store.
# Prefer `docker compose up -d`; this Dockerfile is provided for a plain
# `docker build`/`docker run` workflow:
#
#   docker build -t feast-online-postgres .
#   docker run --rm -p 5432:5432 feast-online-postgres
FROM postgres:16

ENV POSTGRES_USER=feast
ENV POSTGRES_PASSWORD=feast
ENV POSTGRES_DB=feast

EXPOSE 5432
