set -e

SERVICE_NAME="my-cluster-kafka-bootstrap"
LOCAL_PORT=9092
TOPIC="e2e-experiment-end"
MESSAGE='{"action": "export"}'

kubectl port-forward svc/$SERVICE_NAME $LOCAL_PORT:$LOCAL_PORT > /dev/null 2>&1 &
PORT_FORWARD_PID=$!

TIMEOUT=30
COUNT=0
while ! nc -z localhost $LOCAL_PORT; do
  sleep 1
  COUNT=$((COUNT + 1))
  if [ $COUNT -ge $TIMEOUT ]; then
    echo "❌ ERREUR: Timeout après $TIMEOUT secondes. Vérifiez que Kafka est bien déployé."
    kill $PORT_FORWARD_PID 2>/dev/null
    exit 1
  fi
done
echo "✅ Port $LOCAL_PORT est accessible !"

kafka-console-producer.sh \
  --broker-list localhost:$LOCAL_PORT \
  --topic $TOPIC \
  --message "$MESSAGE"

echo "✅ Message envoyé avec succès !"
