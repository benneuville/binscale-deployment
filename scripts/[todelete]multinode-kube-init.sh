
printf "\n## MULTINODE REQUIEREMENTS INSTALLATION\n"
printf "\n\033[1;31m## /!\ BE CAREFUL : THE NAME GIVEN DOES NOT BE SIMILAR TO OTHER NODE \033[0m\n"
sleep 5

if [ -z "$1" ]
then
    printf "\n\033[1;31m## Please provide the name of the node :\033[0m multinode-kube-init.sh <node-name>\n"
    exit 1
fi

sudo swapoff -a

printf "\n\032[1;31m## INSTALL DOCKER \032[0m\n"
sudo apt update
sudo apt install docker.io -y
sudo systemctl enable docker
sudo systemctl start docker

printf "\n\032[1;31m## INSTALL KUBERNETES / KUBEADM / KUBELET \032[0m\n"
curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.30/deb/Release.key | sudo gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg
echo 'deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.30/deb/ /' | sudo tee /etc/apt/sources.list.d/kubernetes.list
sudo apt update
sudo apt -y install kubeadm kubelet kubectl
sudo apt-mark hold kubeadm kubelet kubectl

printf "\n\032[1;31m## VERIFY KUBEADM \032[0m\n"
kubeadm version

printf "\n\032[1;31m## PREPARING KUBE ENVIRONMENT \032[0m\n"
sudo swapoff -a
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

sudo hostnamectl set-hostname $1


printf "\n\032[1;31m## END OF INITIALISATION \032[0m\n"
printf "\n\033[1;31m## Before next step, you need to modify the host file with command \033[1;33m'sudo nano /etc/hosts'\033[1;31m to add the \033[1;33m<hostname> <ip address> \033[0m(ex. master 10.0.230.17)\033[31m line of this nodes and others nodes (master + workers). \n## You can add the other nodes address after \n## \n## to get ip address of your node, use \033[1;33m 'ip addr' \033[1;31m command. \033[0m\n"