printf "💾\033[1;31m INSTALL & SETUP NFS SERVER \033[0m\n"


sudo apt update
sudo apt install nfs-kernel-server -y

sudo mkdir -p /export/logs
sudo chown root:root /export/logs
echo "/export/logs *(rw,sync,no_subtree_check)" | sudo tee -a /etc/exports
sudo exportfs -ra
showmount -e localhost
