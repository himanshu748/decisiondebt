#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
if docker compose version >/dev/null 2>&1; then
  docker compose up -d db
elif docker container inspect decisiondebt-db >/dev/null 2>&1; then
  docker start decisiondebt-db
else
  docker volume create decisiondebt-data >/dev/null
  docker run -d --name decisiondebt-db --restart unless-stopped \
    -p 127.0.0.1:16380:6379 \
    -e 'REDIS_ARGS=--appendonly yes --appendfsync everysec' \
    -v decisiondebt-data:/data falkordb/falkordb:6.0.2
fi
