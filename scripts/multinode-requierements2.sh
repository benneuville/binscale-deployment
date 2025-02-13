#!/bin/bash

# WARNING
printf "\n\033[1;31m## Note you had to reboot the system (or disconnect/reconnect user) after multinode-requirements1.sh\033[0m\n"
printf "\033[1;31m## For this script to work properly, you must be able to run the docker ps command without being root\033[0m\n"
sleep 5

# Swap off
sudo swapoff -a

# PACKAGE PYTHON
printf "\n\033[1;36m## Installing Python packages\033[0m\n"
sudo apt update
sudo apt install -y python3-pip
sudo apt install -y python3-kubernetes
sudo apt install -y python3-pandas

# ANSIBLE
printf "\n\033[1;36m## Installing Ansible\033[0m\n"
sudo apt install -y ansible

# KUBECTL
printf "\n\033[1;36m## Installing Kubectl && ADM/LET\033[0m\n"
sudo apt install -y curl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
sudo apt-get install -y kubelet kubeadm kubectl
sudo apt-mark hold kubelet kubeadm kubectl

# Start & run kubelet 
sudo systemctl enable kubelet
sudo systemctl start kubelet

# HELM
printf "\n\033[1;36m## Installing Helm\033[0m\n"
curl -fsSL -o get_helm.sh https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3
chmod 700 get_helm.sh
./get_helm.sh
