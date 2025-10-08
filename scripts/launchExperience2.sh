#!/bin/bash

printf "\n\033[1;36m## Deleting the previous deployment\033[0m\n"
kubectl delete -f kubernetes/deployment.yml

sleep 45

printf "\n\033[1;36m## Starting the experience\033[0m\n"
start_time=$(date --utc --iso-8601=seconds | sed 's/+00:00/Z/')
ansible-playbook ansible/deploy-app.yaml

printf "\n\033[1;36m## Waiting 5 minutes for the end of the experience\033[0m\n"
sleep 300

while true; do
    desired_replicas=$(kubectl get deployment latency -o=jsonpath='{.spec.replicas}')
    if [ "$desired_replicas" -ge 2 ]; then
        echo "Experience not yet finished, retrying in 1 min"
        sleep 60 # Adjust the interval as needed
    else
        echo "Experience finished"
        break
    fi
done

