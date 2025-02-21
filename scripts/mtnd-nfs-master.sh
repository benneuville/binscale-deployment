printf "💾\033[1;31m INSTALL & SETUP NFS SERVER \033[0m\n"


sudo apt update
sudo apt install nfs-kernel-server -y

sudo mkdir -p /export/logs

sudo chown nobody:nogroup /export/logs

grep -qF "master-node:/export/logs" /etc/fstab || sudo sh -c 'echo "master-node:/export/logs   /var/log/experiments   nfs   defaults   0 0" >> /etc/fstab'


sudo exportfs -ra

showmount -e localhost
