#!/bin/bash

# WARNING
printf "📖\033[1;31m APPLICATION REQUIEREMENTS INSTALLATION \033[0m\n"
sleep 5

# PACKAGE PYTHON
printf "\n\033[1;36m## Installing Python packages\033[0m\n"
sudo apt update
sudo apt install -y python3-pip
sudo apt install -y python3-kubernetes
sudo apt install -y python3-pandas

# JQ
sudo apt install -y jq

# ANSIBLE
printf "\n\033[1;36m## Installing Ansible\033[0m\n"
sudo apt install -y ansible
ansible-galaxy collection install kubernetes.core

# HELM
printf "\n\033[1;36m## Installing Helm\033[0m\n"
curl -fsSL -o get_helm.sh https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3
chmod 700 get_helm.sh
./get_helm.sh