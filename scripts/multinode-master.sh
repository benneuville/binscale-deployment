printf "\033[1;31m## MASTER NODE \033[0m"
printf "\n## (Note you had to launch multinode-requierements file(s) \n\n\n"
sleep 1
printf "\n\033[1;31m## WARNING : you need to modify the host file with command \033[1;33m'sudo nano /etc/hosts'\033[1;31m to add the \033[1;33m<hostname> <ip address> \033[0m(ex. master 10.0.230.17)\033[31m line of this nodes and others nodes (master + workers). \n## You can add the other nodes address after \n## \n## to get ip address of your node, use \033[1;33m 'ip addr' \033[1;31m command. \033[0m\n"
printf "\n\n"
sleep 10

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
sudo tee /etc/systemd/system/kubelet.service.d/10-kubeadm.conf<<EOF
Environment="KUBELET_EXTRA_ARGS=--fail-swap-on=false"
EOF

sudo systemctl daemon-reload && sudo systemctl restart kubelet

printf "\033[1;33m## START KUBEADM \032[0m\n"
sudo kubeadm reset -f
sudo kubeadm init --control-plane-endpoint=master-node --upload-certs | tee /tmp/kubeadm_init.log
mkdir -p $HOME/.kube
sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
sudo chown $(id -u):$(id -g) $HOME/.kube/config

printf "\033[1;33m## DEPLOY FLANNEL NETWORK \032[0m\n"
kubectl apply -f https://github.com/flannel-io/flannel/releases/latest/download/kube-flannel.yml
kubectl taint nodes --all node-role.kubernetes.io/control-plane-

printf "\033[1;33m## note : the command below is requiered for worker nodes \033[0m\n"
printf "\033[1;32m"
tail -n 2 /tmp/kubeadm_init.log
printf "\033[0m"