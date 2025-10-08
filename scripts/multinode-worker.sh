printf "🦺\033[1;31m WORKER NODE \033[0m\n"
sleep 1
printf "\033[1;31m## WARNING : you need to rename the hostname of this node with command \033[1;33m'sudo hostnamectl set-hostname <hostname>'\033[0m\n"
printf "\033[1;31m## WARNING : you need to modify the host file with command \033[1;33m'sudo nano /etc/hosts'\033[1;31m to add the \033[1;33m<address ip> <hostname> \033[0m(ex. 10.0.230.17 master-node)\033[31m line of this nodes and others nodes (master + workers). \n## You can add the other nodes address after \n## \n## to get ip address of your node, use \033[1;33m 'ip addr' \033[1;31m command. \033[0m\n"
printf "\n\n"
sleep 10
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
echo "Script directory: $SCRIPT_DIR"

# PACKAGE PYTHON
printf "\n\033[1;36m## Installing Python packages\033[0m\n"
sudo apt update
sudo apt install -y python3-pip
sudo apt install -y python3-kubernetes
sudo apt install -y python3-pandas

"$SCRIPT_DIR"/mtnd-requierements.sh
"$SCRIPT_DIR"/mtnd-nfs-worker.sh
"$SCRIPT_DIR"/mtnd-docker.sh
"$SCRIPT_DIR"/mtnd-k8s.sh

printf "\033[1;31m## you have to launch the command you get from the master node \033[0m\n"
printf "\033[1;31m## to join the cluster \033[0m\n"
printf "\033[1;31m## format : sudo kubeadm join [master-node-ip]:6443 --token [token] --discovery-token-ca-cert-hash sha256:[hash] \033[0m\n"

