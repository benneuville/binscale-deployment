printf "\t👑\033[1;31m MASTER NODE \033[0m"
printf "\n## (Note you had to launch multinode-requierements file(s) \n"

sleep 1
printf "\033[1;31m## WARNING : you need to rename the hostname of this node with command \033[1;33m'sudo hostnamectl set-hostname master-node'\033[0m\n"
printf "\033[1;31m## WARNING : you need to modify the host file with command \033[1;33m'sudo nano /etc/hosts'\033[1;31m to add the \033[1;33m<hostname> <address ip> \033[0m(ex. 10.0.230.17 master-node)\033[31m line of this nodes and others nodes (master + workers). \n## You can add the other nodes address after \n## \n## to get ip address of your node, use \033[1;33m 'ip addr' \033[1;31m command. \033[0m\n"
printf "\n\n"
sleep 10
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
"$SOURCE"/mtnd-experience-requierements.sh
"$SOURCE"/mtnd-requierements.sh
"$SOURCE"/mtnd-docker.sh
"$SOURCE"/mtnd-k8s.sh
"$SOURCE"/multinode-resetcluster.sh