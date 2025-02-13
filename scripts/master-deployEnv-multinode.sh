#!/bin/bash

# WARNING
printf "\n\033[1;31m## Note you had to launch multinode-requierements file(s) \033[0m\n"
printf "\033[1;31m## MASTER NODE \033[0m\n"
sleep 5

# Start Kubernetes cluster with kubeadm
sudo kubeadm init --pod-network-cidr=10.244.0.0/16

# Configure kubectl
mkdir -p $HOME/.kube
sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
sudo chown $(id -u):$(id -g) $HOME/.kube/config

# Install Flannel
kubectl apply -f https://raw.githubusercontent.com/coreos/flannel/master/Documentation/kube-flannel.yml

kubectl get pods -n kube-system

printf "\n\033[1;32m## On the next list, the ip address requiered for worker nodes is on the line \"default\" \033[0m\n\n"