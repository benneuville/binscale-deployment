echo "Deploying k3s cluster (IP addresses in k3s/hosts.ini should be updated !)"
export ANSIBLE_HOST_KEY_CHECKING=False
/home/$(echo "$USER")/.local/bin/ansible-playbook k3s/deploy-cluster-kube.yaml -i k3s/hosts.ini
