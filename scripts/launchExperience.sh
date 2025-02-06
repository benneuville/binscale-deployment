 #!/bin/bash

printf "\n\033[1;36m## Deleting the previous deployment\033[0m\n"
kubectl delete -f kubernetes/deployment.yml

sleep 25

printf "\n\033[1;36m## Starting the experience\033[0m\n"
start_time=$(date --utc --iso-8601=seconds | sed 's/+00:00/Z/')
ansible-playbook ansible/deploy-app.yaml

printf "\n\033[1;36m## Waiting 10 minutes for the end of the experience\033[0m\n"
sleep 300

while true; do
    desired_replicas=$(kubectl get deployment latency -o=jsonpath='{.spec.replicas}')
    if [ "$desired_replicas" -ge 10 ]; then
        echo "Experience not yet finished, retrying in 1 min"
        sleep 60 # Adjust the interval as needed
    else
        echo "Experience finished"
        break
    fi
done

echo "Removing deployment"
kubectl delete -f kubernetes/deployment.yml

echo "Experience Finished, analysing output in the python/input folder"
cd python/input/ || exit
../../scripts/log_analysis/extractLogs.sh filebeat*
python3 ../../scripts/log_analysis/analyze.py consumer_logs.txt controler_logs.txt

exit 0


# Start port forwarding
kubectl port-forward svc/kibana-kb-http 15601:5601 -n elastic &
forward_pid=$!

# Function to stop port forwarding
stop_port_forwarding() {
    kill $forward_pid
}

sleep 1

# Start and get report
ELASTIC_PASSWORD=$(kubectl get secret elastic-cluster-es-elastic-user -o go-template='{{.data.elastic | base64decode}}' -n elastic)
echo "Get password : $ELASTIC_PASSWORD"

# Create data view
echo "Create or replace data view : Cluster logs"
curl -s --insecure \
-X POST 'https://localhost:15601/api/data_views/data_view' \
--header 'kbn-xsrf: creating' \
--header 'Content-Type: application/json' \
--header "Authorization: Basic $(echo -n "elastic:$ELASTIC_PASSWORD" | base64)" \
--data-raw '{
  "override": true,
  "data_view": {
     "title": "f*",
     "name": "Cluster logs",
     "id": "latency-id",
     "timeFieldName": "@timestamp"
  }
}'

end_time=$(date --utc --iso-8601=seconds | sed 's/+00:00/Z/')

encoded_start_time=$(echo "$start_time" | sed 's/:/%3A/g')
encoded_end_time=$(echo "$end_time" | sed 's/:/%3A/g')


# Execute POST request for start the report on the last 10 minutes
echo "Request reporting"
response_post=$(
 curl --insecure \
 -H "Authorization: Basic $(echo -n "elastic:$ELASTIC_PASSWORD" | base64)" \
 -H "kbn-xsrf: reporting" \
 -X POST \
 "https://localhost:15601/api/reporting/generate/csv_searchsource?jobParams=%28browserTimezone%3AEurope%2FParis%2Ccolumns%3A%21%28%27%40timestamp%27%2Cmessage%2Ckubernetes.pod.name%29%2CobjectType%3Asearch%2CsearchSource%3A%28fields%3A%21%28%28field%3A%27%40timestamp%27%2Cinclude_unmapped%3Atrue%29%2C%28field%3Amessage%2Cinclude_unmapped%3Atrue%29%2C%28field%3Akubernetes.pod.name%2Cinclude_unmapped%3Atrue%29%29%2Cfilter%3A%21%28%28meta%3A%28field%3A%27%40timestamp%27%2Cindex%3Alatency-id%2Cparams%3A%28%29%29%2Cquery%3A%28range%3A%28%27%40timestamp%27%3A%28format%3Astrict_date_optional_time%2Cgte%3A%27$encoded_start_time%27%2Clte%3A%27$encoded_end_time%27%29%29%29%29%29%2Cindex%3Alatency-id%2Cparent%3A%28filter%3A%21%28%29%2Cindex%3Alatency-id%2Cquery%3A%28language%3Akuery%2Cquery%3A%27%27%29%29%2Csort%3A%21%28%28%27%40timestamp%27%3Adesc%29%29%2CtrackTotalHits%3A%21t%29%2Ctitle%3A%27Latency%20logs%20report%27%2Cversion%3A%278.6.2%27%29" 
 # https://localhost:15601/api/reporting/generate/csv_searchsource?jobParams=%28browserTimezone%3AEurope%2FParis%2Ccolumns%3A%21%28%27%40timestamp%27%2Cmessage%2Ckubernetes.pod.name%29%2CobjectType%3Asearch%2CsearchSource%3A%28fields%3A%21%28%28field%3A%27%40timestamp%27%2Cinclude_unmapped%3Atrue%29%2C%28field%3Amessage%2Cinclude_unmapped%3Atrue%29%2C%28field%3Akubernetes.pod.name%2Cinclude_unmapped%3Atrue%29%29%2Cfilter%3A%21%28%28meta%3A%28field%3A%27%40timestamp%27%2Cindex%3Abb5b36b2-3909-4792-82ba-14afad645925%2Cparams%3A%28%29%29%2Cquery%3A%28range%3A%28%27%40timestamp%27%3A%28format%3Astrict_date_optional_time%2Cgte%3A$encoded_start_time%2Clte%3A$encoded_end_time%29%29%29%29%29%2Cindex%3Abb5b36b2-3909-4792-82ba-14afad645925%2Cparent%3A%28filter%3A%21%28%29%2Cindex%3Abb5b36b2-3909-4792-82ba-14afad645925%2Cquery%3A%28language%3Akuery%2Cquery%3A%27%27%29%29%2Csort%3A%21%28%28%27%40timestamp%27%3Adesc%29%29%2CtrackTotalHits%3A%21t%29%2Ctitle%3A%27logs%27%2Cversion%3A%278.6.2%27%29" > scripts/logs.csv
 # https://localhost:15601/api/reporting/generate/csv_searchsource?jobParams=%28browserTimezone%3AEurope%2FParis%2Ccolumns%3A%21%28%27%40timestamp%27%2Cmessage%2Ckubernetes.pod.name%29%2CobjectType%3Asearch%2CsearchSource%3A%28fields%3A%21%28%28field%3A%27%40timestamp%27%2Cinclude_unmapped%3Atrue%29%2C%28field%3Amessage%2Cinclude_unmapped%3Atrue%29%2C%28field%3Akubernetes.pod.name%2Cinclude_unmapped%3Atrue%29%29%2Cfilter%3A%21%28%28meta%3A%28field%3A%27%40timestamp%27%2Cindex%3Alatency-id%2Cparams%3A%28%29%29%2Cquery%3A%28range%3A%28%27%40timestamp%27%3A%28format%3Astrict_date_optional_time%2Cgte%3A%27$encoded_start_time%27%2Clte%3A%27$encoded_end_time%27%29%29%29%29%29%2Cindex%3Alatency-id%2Cparent%3A%28filter%3A%21%28%28%27%24state%27%3A%28store%3AappState%29%2Cmeta%3A%28alias%3A%21n%2Cdisabled%3A%21f%2Cindex%3Alatency-id%2Ckey%3Akubernetes.deployment.name%2Cnegate%3A%21f%2Cparams%3A%28query%3Alatency%29%2Ctype%3Aphrase%29%2Cquery%3A%28match_phrase%3A%28kubernetes.deployment.name%3Alatency%29%29%29%2C%28%27%24state%27%3A%28store%3AappState%29%2Cmeta%3A%28alias%3A%21n%2Cdisabled%3A%21f%2Cindex%3Alatency-id%2Ckey%3Amessage%2Cnegate%3A%21f%2Cparams%3A%28query%3A%27latency%20is%27%29%2Ctype%3Aphrase%29%2Cquery%3A%28match_phrase%3A%28message%3A%27latency%20is%27%29%29%29%29%2Cindex%3Alatency-id%2Cquery%3A%28language%3Akuery%2Cquery%3A%27%27%29%29%2Csort%3A%21%28%28%27%40timestamp%27%3Adesc%29%29%2CtrackTotalHits%3A%21t%29%2Ctitle%3A%27Latency%20logs%20report%27%2Cversion%3A%278.6.2%27%29
)

#echo "Post response : $reponse_post"

# Extract the path from the response
url=$(echo "$response_post" | jq -r '.path')
echo "Path to get report : $url"

# Delete existing file
rm -f python/input/result.csv

logs_file="python/input/result.csv"

# Loop until the response is different from "wait"
while true; do
    # Execute GET a request to get the report
    curl --insecure -H "Authorization: Basic $(echo -n "elastic:$ELASTIC_PASSWORD" | base64)" "https://localhost:15601$url" -o "$logs_file" -s
    
    # Verify if the response is different from "processing"
    if grep -q -v -e "pending" -e "processing" "$logs_file"; then
        echo "Logs saved in $logs_file"
        break
    else
	    echo "Still processing, retrying in 1 min"
    fi
    
    # Sleep for 1 minute
    sleep 60
done
# Stop port forwarding
stop_port_forwarding

# Execute a Python script to process the result.csv file
printf "\n\033[1;36m## Executing process_output.py\033[0m\n"
python3 scripts/process_output.py python/input/result.csv
# Execute the python script
printf "\n\033[1;36m## Executing main.py\033[0m\n"
python3 python/main.py
printf "\n\033[1;36m## Executing cdf.py\033[0m\n"
python3 python/cdf.py
# python3 python/displayPlotLag.py

printf "\n\033[1;36m## Results are available in the python/output folder\033[0m\n"


#kubectl port-forward service/elastic-cluster-es-http 9200:9200 -n elastic --address 0.0.0.0
#curl -k -u  "elastic:$ELASTIC_PASSWORD" https://localhost:9200/_  
curl -XPOST "https://elastic-cluster-es-http.elastic.svc:9200/_search" -H "kbn-xsrf: reporting" -H "Content-Type: application/json" -d'
{
  "query": {
    "bool": {
      "must": [
        {
          "match_phrase": {
            "kubernetes.deployment.name": "latency"
          }
        }
      ]
    }
  },
  "_source": ["@timestamp", "message", "kubernetes.pod.name"],
  "sort": [
    {
      "@timestamp": {
        "order": "desc"
      }
    }
  ],
  "track_total_hits": true
}'