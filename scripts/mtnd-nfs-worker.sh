printf "💾\033[1;31m INSTALL & SETUP NFS (UTILS) \033[0m\n"

sudo apt update
sudo apt install nfs-common -y
sudo mkdir -p /var/log/experiments
sudo mount -t nfs master-node:/export/logs /var/log/experiments
