kubectl port-forward svc/e2e-analyzer 8080:8080 > /dev/null 2>&1 &
sleep 3 && curl -X POST http://localhost:8080/state/finish