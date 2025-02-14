#!/bin/bash

# WARNING
printf "\n\033[1;31m## Note you had to launch multinode-requierements file(s) \033[0m\n"
printf "\033[1;31m## MASTER NODE \033[0m\n"
sleep 5

sudo sh -c 'echo "127.0.0.1 master-node" >> /etc/hosts'
sudo hostnamectl set-hostname master-node

sudo tee /etc/default/kubelet<<EOF
KUBELET_EXTRA_ARGS="--cgroup-driver=cgroupfs"
EOF
sudo systemctl daemon-reload && sudo systemctl restart kubelet
sudo tee /etc/docker/daemon.json<<EOF
{
      "exec-opts": ["native.cgroupdriver=systemd"],
      "log-driver": "json-file",
      "log-opts": {
      "max-size": "100m"
   },
       "storage-driver": "overlay2"
        }
EOF
sudo systemctl daemon-reload && sudo systemctl restart docker
mkdir /etc/systemd/system/kubelet.service.d
sudo tee /etc/systemd/system/kubelet.service.d/10-kubeadm.conf<<EOF
Environment="KUBELET_EXTRA_ARGS=--fail-swap-on=false"
EOF
sudo systemctl daemon-reload && sudo systemctl restart kubelet
sudo kubeadm init --control-plane-endpoint=master-node --upload-certs

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