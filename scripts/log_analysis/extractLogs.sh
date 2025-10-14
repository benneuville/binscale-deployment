echo "Extracting consumer logs"
jq 'select(.kubernetes.pod.name |startswith("latency")) |  .kubernetes.pod.uid+ " " + .message'  $@  2>/dev/null | tr -d '"' > consumer_logs.txt
echo "Extracting producer logs"
jq 'select(.kubernetes.pod.name |startswith("producer")) | .message' $@  2>/dev/null | tr -d '"' > producer_logs.txt
echo "Extracting controller logs"
jq 'select(.kubernetes.pod.name |startswith("controllerand")) | .message' $@  2>/dev/null | tr -d '"' > controller_logs.txt 
