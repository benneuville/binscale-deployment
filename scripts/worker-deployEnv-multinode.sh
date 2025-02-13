#!/bin/bash

# WARNING
printf "\n\033[1;31m## Note you had to launch multinode-requierements file(s) \033[0m\n"
printf "\033[1;31m## WORKER NODE \033[0m\n"
sleep 5

# Remplacez <MASTER_IP>, <TOKEN> et <HASH> par les valeurs fournies par le master lors de l'initialisation.
sudo kubeadm join <MASTER_IP>:6443 --token <TOKEN> --discovery-token-ca-cert-hash sha256:<HASH>

# Une fois la commande exécutée, le nœud worker rejoindra le cluster.