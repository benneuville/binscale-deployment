#!/bin/bash

# WARNING
printf "\n\033[1;31m## Note you had to reboot the system (or disconnect/reconnect user) after multinode-requirements1.sh\033[0m\n"
printf "\033[1;31m## For this script to work properly, you must be able to run the docker ps command without being root\033[0m\n"
sleep 5

# Swap off
sudo swapoff -a

#launch Docker
sudo systemctl start docker


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
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl.sha256"
echo "$(cat kubectl.sha256)  kubectl" | sha256sum --check
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
# Check version
kubectl version --client
# Port availability
sudo apt install -y netcat-openbsd
nc 127.0.0.1 6443 -v

sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.30/deb/Release.key | sudo gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg
echo 'deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.30/deb/ /' | sudo tee /etc/apt/sources.list.d/kubernetes.list
sudo apt update
sudo apt install -y kubeadm kubelet kubectl
sudo apt-mark hold kubeadm kubelet kubectl

kubeadm version

sudo sed -i '/ swap / s/^\(.*\)$/#\1/g' /etc/fstab
sudo tee /etc/modules-load.d/containerd.conf <<EOF
overlay
br_netfilter
EOF

sudo modprobe overlay
sudo modprobe br_netfilter
sudo tee /etc/sysctl.d/kubernetes.conf <<EOF
net.bridge.bridge-nf-call-ip6tables = 1
net.bridge.bridge-nf-call-iptables = 1
net.ipv4.ip_forward = 1
EOF
sudo sysctl --system


# Start & run kubelet 
sudo systemctl enable kubelet
sudo systemctl start kubelet

# HELM
printf "\n\033[1;36m## Installing Helm\033[0m\n"
curl -fsSL -o get_helm.sh https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3
chmod 700 get_helm.sh
./get_helm.sh
