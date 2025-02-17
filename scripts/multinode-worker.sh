printf "\033[1;31m## WORKER NODE \033[0m"
printf "\n## (Note you had to launch multinode-requierements file(s) \n\n\n"
sleep 1
printf "\n\033[1;31m## WARNING : you need to modify the host file with command \033[1;33m'sudo nano /etc/hosts'\033[1;31m to add the \033[1;33m<hostname> <ip address> \033[0m(ex. master 10.0.230.17)\033[31m line of this nodes and others nodes (master + workers). \n## You can add the other nodes address after \n## \n## to get ip address of your node, use \033[1;33m 'ip addr' \033[1;31m command. \033[0m\n"
printf "\n\n"
sleep 10

sudo systemctl stop apparmor && sudo systemctl disable apparmor
sudo systemctl restart containerd.service

printf "\033[1;31m## you have to launch the command you get from the master node \033[0m\n"
printf "\033[1;31m## to join the cluster \033[0m\n"
printf "\033[1;31m## format : sudo kubeadm join [master-node-ip]:6443 --token [token] --discovery-token-ca-cert-hash sha256:[hash] \033[0m\n"