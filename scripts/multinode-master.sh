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

sh ./multinode-master-deploy.sh