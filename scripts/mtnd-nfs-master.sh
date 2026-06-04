#!/bin/bash
printf "💾\033[1;31m INSTALL & SETUP NFS SERVER \033[0m\n"


sudo apt update
sudo DEBIAN_FRONTEND=noninteractive apt install -y nfs-kernel-server

# export logs
sudo mkdir -p /export/logs

sudo chown nobody:nogroup /export/logs

if ! grep -qF "/export/logs" /etc/exports; then
    echo "/export/logs    *(rw,sync,no_subtree_check)" | sudo tee -a /etc/exports
fi

# export postgres

sudo mkdir -p /export/postgres

sudo chown nobody:nogroup /export/postgres
sudo chmod 777 /export/postgres

if ! grep -qF "/export/postgres" /etc/exports; then
    echo "/export/postgres    *(rw,sync,no_subtree_check,no_root_squash)" | sudo tee -a /etc/exports
fi

# export e2e analyzer

sudo mkdir -p /export/analyzer

sudo chown nobody:nogroup /export/analyzer
sudo chmod 777 /export/analyzer

if ! grep -qF "/export/analyzer" /etc/exports; then
    echo "/export/postgres    *(rw,sync,no_subtree_check,no_root_squash)" | sudo tee -a /etc/exports
fi

sudo exportfs -ra

showmount -e localhost