#!/bin/bash
set -e

# Запускаем Elasticsearch в фоне
/usr/local/bin/docker-entrypoint.sh elasticsearch \
  -E path.data=/tmp/data \
  -E xpack.security.enabled=false \
  -E discovery.type=single-node &



es_pid=$!

# Ждем пока Elasticsearch будет доступен на localhost:9200
until curl -s http://localhost:9200 >/dev/null; do
  echo "Waiting for Elasticsearch to start..."
  sleep 1
done

# Запускаем скрипт предзагрузки
/preload.sh

# Ждем завершения elasticsearch
wait $es_pid
