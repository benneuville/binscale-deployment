 #!/bin/bash

printf "\n\033[1;36m## Deleting the previous deployment\033[0m\n"
ansible-playbook ansible/undeploy-app.yaml


sleep 25

printf "\n\033[1;36m## Starting the experience\033[0m\n"
start_time=$(date --utc --iso-8601=seconds | sed 's/+00:00/Z/')
ansible-playbook ansible/deploy-app.yaml

printf "\n\033[1;36m## Waiting 15 minutes for the end of the experience\033[0m\n"
sleep 600

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

echo "Removing deployment"
ansible-playbook ansible/undeploy-app.yaml

echo "Experience Finished, analysing output in the python/input folder"
cd python/input/ || exit
../../scripts/log_analysis/extractLogs.sh filebeat*
python3 ../../scripts/log_analysis/analyze.py consumer_logs.txt controller_logs.txt

exit 0

# Execute a Python script to process the result.csv file
printf "\n\033[1;36m## Executing process_output.py\033[0m\n"
python3 scripts/process_output.py python/input/result.csv
# Execute the python script
printf "\n\033[1;36m## Executing main.py\033[0m\n"
python3 python/main.py
printf "\n\033[1;36m## Executing cdf.py\033[0m\n"
python3 python/cdf.py
# python3 python/displayPlotLag.py

printf "\n\033[1;36m## Results are available in the 'python' folder\033[0m\n"
