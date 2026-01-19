#!/bin/bash

rm -f /export/logs/*
printf "\n\033[1;36m Experience\033[0m [$1]"
sleep 5

python3 experience/generator/generate_deployment.py "$1" "$2"
if [ $? -ne 0 ]; then
    exit 1
fi

printf "\n\033[1;36m## Starting the experience [$1]\033[0m\n"
ansible-playbook ansible/deploy-app.yaml

printf "\n\033[1;36m## Waiting 10 minutes for the end of the experience [$1]\033[0m\n"
sleep 60
printf "Producers are still running."

while true; do
    producer_pods=$(kubectl get pods -l app=workload --field-selector=status.phase=Running -o jsonpath='{.items[*].metadata.name}' | wc -w)

    if [ "$producer_pods" -gt 0 ]; then
        printf "."
        sleep 15
    else
        printf "\n"
        echo "All producers have finished. Experience [$1] is complete."
        break
    fi
done
echo "Removing deployment [$1]"
ansible-playbook ansible/undeploy-app.yaml
