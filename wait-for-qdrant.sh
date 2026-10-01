#!/bin/bash
set -e

host="$1"
port="$2"
shift 2
cmd="$@"

echo "Waiting for Qdrant at $host:$port to be ready..."

for i in {1..60}; do
  if nc -z "$host" "$port" 2>/dev/null; then
    # Port is open, now verify HTTP API is responding
    if curl -s http://"$host":"$port"/collections > /dev/null 2>&1; then
      echo "Qdrant is ready!"
      sleep 2  # Extra buffer to ensure Qdrant is fully ready
      exec $cmd
    fi
  fi
  echo "Attempt $i/60: Qdrant not ready yet, waiting..."
  sleep 1
done

echo "Timeout: Qdrant did not become ready after 60 seconds"
exit 1
