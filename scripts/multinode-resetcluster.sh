printf "🚀\033[1;31m LAUNCH MASTER-NODE \033[0m\n"
sudo kubeadm reset -f
sudo kubeadm init

mkdir -p $HOME/.kube
sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
sudo chown $(id -u):$(id -g) $HOME/.kube/config

kubectl apply -f https://raw.githubusercontent.com/projectcalico/calico/v3.25.0/manifests/calico.yaml

printf "⚠️\033[1;33m Note : the command below is requiered for worker nodes \033[0m\n"
printf "📍\033[1;32m "
kubeadm token create --print-join-command
printf "\033[0m"