#!/bin/bash

rm -f /export/logs/*
printf "\n\033[1;36m Experience\033[0m [$1]"
sleep 5

python3 experience/generator/generate_deployment.py "$1" "$2"
if [ $? -ne 0 ]; then
    exit 1
fi

printf "\n\033[1;36m## Starting the experience [$1]\033[0m\n"
start_time=$(date --utc --iso-8601=seconds | sed 's/+00:00/Z/')
ansible-playbook ansible/deploy-app.yaml

printf "\n\033[1;36m## Waiting 10 minutes for the end of the experience [$1]\033[0m\n"
sleep 600

# todo: fix
while true; do
    desired_replicas=$(kubectl get deployment latency -o=jsonpath='{.spec.replicas}')
    if [ "$desired_replicas" -ge 2 ]; then
        echo "Experience [$1] not yet finished, retrying in 1 min"
        sleep 60
    else
        echo "Experience [$1] finished"
        break
    fi
done

echo "Removing deployment [$1]"
ansible-playbook ansible/undeploy-app.yaml
