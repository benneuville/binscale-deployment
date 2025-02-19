printf "\033[1;33m## START KUBEADM \033[0m\n"
sudo kubeadm reset -f
sudo kubeadm init --pod-network-cidr=192.168.0.0/16 | tee /tmp/kubeadm_init.log
mkdir -p $HOME/.kube
sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
sudo chown $(id -u):$(id -g) $HOME/.kube/config

printf "\033[1;33m## DEPLOY FLANNEL NETWORK \033[0m\n"
kubectl apply -f https://github.com/flannel-io/flannel/releases/latest/download/kube-flannel.yml
kubectl taint nodes --all node-role.kubernetes.io/control-plane-

printf "\033[1;33m## note : the command below is requiered for worker nodes \033[0m\n"
printf "\033[1;32m"
tail -n 2 /tmp/kubeadm_init.log
printf "\033[0m"