#!/bin/bash
printf "💾\033[1;31m INSTALL & SETUP NFS (UTILS) \033[0m\n"

sudo apt update
sudo DEBIAN_FRONTEND=noninteractive apt install -y nfs-common 
sudo mkdir -p /var/log/experiments
sudo mount -t nfs master-node:/export/logs /var/log/experiments

sudo mkdir -p /mnt/nfs/postgres
sudo mount -t nfs master-node:/export/postgres /mnt/nfs/postgres