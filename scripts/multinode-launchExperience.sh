#!/bin/bash

rm -f /export/logs/*
rm -f /export/analyzer/*

printf "\n\033[1;36m Experience\033[0m [$1]"
sleep 10

printf "\n\033[1;36m## Waiting filebeat logs file for [$1] experience \033[0m\n"

python3 experience/generator/generate_deployment.py "$1" "$2"
if [ $? -ne 0 ]; then
    exit 1
fi

printf "\n\033[1;36m## Starting the experience [$1]\033[0m\n"
ansible-playbook ansible/deploy-app.yaml

printf "\n\033[1;36m## Waiting for the end of the experience [$1]\033[0m\n"
sleep 60
printf "Producers are still running."

while true; do
    producer_pods=$(kubectl get pods -l app=workload --field-selector=status.phase=Running -o jsonpath='{.items[*].metadata.name}' | wc -w)

    if [ "$producer_pods" -gt 0 ]; then
        printf "."
        sleep 15
    else
        printf "\n"
        printf "All producers have finished. \nExperience [$1] is complete."
        break
    fi
done

sleep 15
printf "Deploying e2e Analyzer [$1]"
ansible-playbook ansible/deploy-e2e-analyzer.yaml
ansible-playbook ansible/undeploy-app.yaml
printf "Waiting for e2e Analyzer to finish."

while true; do
    e2e_analyzer_pod=$(kubectl get pods -l app=e2e-analyzer --field-selector=status.phase=Running -o jsonpath='{.items[*].metadata.name}' | wc -w)

    if [ "$e2e_analyzer_pod" -gt 0 ]; then
        printf "."
        sleep 10
    else
        printf "\n"
        printf "\nAnalyze finished. \nAnalyze of experience [$1] is complete."
        break
    fi
done

echo "Removing e2e analyzer & deployment [$1]"
ansible-playbook ansible/undeploy-e2e-analyzer.yaml