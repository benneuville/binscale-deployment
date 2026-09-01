echo "Extracting consumer logs"
jq 'select(.kubernetes.labels.app |startswith("latency")) |  .kubernetes.pod.uid + " - " + .kubernetes.container.name + " - " + .message'  $@  2>/dev/null | tr -d '"' > consumer_logs.txt &
echo "Extracting producer logs"
jq 'select(.kubernetes.labels.app |startswith("workload")) | .message' $@  2>/dev/null | tr -d '"' > producer_logs.txt &
echo "Extracting controller logs"
jq 'select(.kubernetes.labels.app |startswith("controllerandscaler")) | .message' $@  2>/dev/null | tr -d '"' > controller_logs.txt &

wait
