#!/bin/bash
set -e

kubectl port-forward svc/e2e-analyzer 8080:8080 > /tmp/port-forward.log 2>&1 &
PF_PID=$!

echo "Attente du service..."
while ! curl -s http://localhost:8080 >/dev/null; do sleep 1; done

curl -X POST http://localhost:8080/state/finish

kill $PF_PID