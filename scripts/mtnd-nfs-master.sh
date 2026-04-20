#!/bin/bash
printf "💾\033[1;31m INSTALL & SETUP NFS SERVER \033[0m\n"


sudo apt update
sudo DEBIAN_FRONTEND=noninteractive apt install -y nfs-kernel-server

sudo mkdir -p /export/logs

sudo chown nobody:nogroup /export/logs

if ! grep -qF "/export/logs" /etc/exports; then
    echo "/export/logs    *(rw,sync,no_subtree_check)" | sudo tee -a /etc/exports
fi

sudo exportfs -ra

showmount -e localhost