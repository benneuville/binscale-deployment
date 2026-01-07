#!/bin/bash

DEFAULT_NODES=3
DEFAULT_OUTPUT_DIR="."
DEFAULT_INPUT_SCRIPT_FILE="grid5000-deployment-script.sh"
DEFAULT_BRANCH_NAME="master"
DEFAULT_LIFESPAN=2
DEFAULT_SITE_NAME="grenoble"
DEFAULT_GIT_REPO="https://github.com/benneuville/binscale-deployment.git"
DEFAULT_QUEUE_NAME="default"

SSH_CONFIG_FILE="$HOME/.ssh/config"

NUM_NODES=$DEFAULT_NODES
OUTPUT_DIR=$DEFAULT_OUTPUT_DIR
BRANCH_NAME=$DEFAULT_BRANCH_NAME
LIFESPAN=$DEFAULT_LIFESPAN
SITE_NAME=$DEFAULT_SITE_NAME
GIT_REPO=$DEFAULT_GIT_REPO
QUEUE_NAME=$DEFAULT_QUEUE_NAME
USERNAME=""

master_node=""

worker_nodes=()

usage() {
    echo "Usage: $0 [OPTIONS]"
    echo "Deploy complete experience on Grid5000."
    echo ""
    echo "Options:"
    echo "  -n, --nodes NUM      Number of nodes to deploy (default: $DEFAULT_NODES)"
    echo "  -o, --output DIR     Output folder (default: $DEFAULT_OUTPUT_DIR)"
    echo "  -b, --branch NAME    Git branch name to use (default: $DEFAULT_BRANCH_NAME)"
    echo "  -ls, --lifespan SECS   Lifespan of the nodes in hours (default: $DEFAULT_LIFESPAN)"
    echo "  -sn, --site NAME     Grid5000 site name (default: $DEFAULT_SITE_NAME)"
    echo "  -u, --username USER  Grid5000 username (no default)"
    echo "  -g, --git-repo URL    Git repository URL (default: $DEFAULT_GIT_REPO)"
    echo "  -q, --queue NAME     Grid5000 queue name (default: $DEFAULT_QUEUE_NAME)"
    echo ""
    echo "  -h, --help           for help"
    echo ""
    exit 0
}

while [[ "$#" -gt 0 ]]; do
    case $1 in
        -n|--nodes)
            NUM_NODES="$2"
            shift
            ;;
        -o|--output)
            OUTPUT_DIR="$2"
            shift
            ;;
        -u|--username)
            USERNAME="$2"
            shift
            ;;
        -b|--branch)
            BRANCH_NAME="$2"
            shift
            ;;
        -ls|--lifespan)
            LIFESPAN="$2"
            shift
            ;;
        -sn|--site)
            SITE_NAME="$2"
            shift
            ;;
        -g|--git-repo)
            GIT_REPO="$2"
            shift
            ;;
        -q|--queue)
            QUEUE_NAME="$2"
            shift
            ;;
        -h|--help)
            usage
            ;;
        *)
            echo "Unknown options: $1" >&2
            usage
            exit 1
            ;;
    esac
    shift
done

if [ -z "$USERNAME" ]; then
    echo "Error: Grid5000 username is requiered." >&2
    usage
    exit 1
fi

if ! [[ "$NUM_NODES" =~ ^[0-9]+$ ]]; then
    echo "Error: The number of nodes must be a positive integer." >&2
    usage
    exit 1
fi

printf "🚂🚋\033[1;75m-EXPERIENCE : GRID'5000 \033[0m🚋\n"
printf "\e[38;5;8m###############################\033[0m \n"
sleep .5

printf " \e[33m▣\e[1;33m Number of nodes\e[0m [$NUM_NODES]\n"
printf " \e[33m▣\e[1;33m Output directory for results\e[0m [$OUTPUT_DIR]\n"
printf " \e[33m▣\e[1;33m Git branch name\e[0m [$BRANCH_NAME]\n"
printf " \e[33m▣\e[1;33m Git repository URL\e[0m [$GIT_REPO]\n"
printf " \e[33m▣\e[1;33m Lifespan (hours)\e[0m [$LIFESPAN]\n"
printf " \e[33m▣\e[1;33m Grid5000 site name\e[0m [$SITE_NAME]\n"
printf " \e[33m▣\e[1;33m Grid5000 username\e[0m [$USERNAME]\n"
printf " \e[33m▣\e[1;33m Grid5000 queue name\e[0m [$QUEUE_NAME]\n"

# sleep 5

sudo mkdir -p "$HOME/.ssh"
sudo chmod 777 "$HOME/.ssh"

sudo touch "$SSH_CONFIG_FILE"
sudo chmod 677 "$SSH_CONFIG_FILE"

G5K_CONFIG="
Host g5k
    User $USERNAME
    Hostname access.grid5000.fr
    ForwardAgent no"

SITE_G5K_CONFIG="
Host $SITE_NAME.g5k
    User $USERNAME
    ProxyCommand ssh g5k -W $SITE_NAME:%p
    ForwardAgent no"

printf "\n\e[38;5;8m ◻ Adding hosts in ssh \033[0m"

if ! sudo grep -q "^Host g5k" "$SSH_CONFIG_FILE"; then
    sudo echo "$G5K_CONFIG" >> "$SSH_CONFIG_FILE"
fi

if ! sudo grep -q "^Host $SITE_NAME.g5k" "$SSH_CONFIG_FILE"; then
    sudo echo "$SITE_G5K_CONFIG" >> "$SSH_CONFIG_FILE"
fi

sed -i 's/\r$//' $SSH_CONFIG_FILE

# Try to connect to Grid5000 to check username validity
printf "\033[2K"
printf "\r\e[38;5;36m ▣ Hosts added in ssh \033[0m[$SSH_CONFIG_FILE]\n"
sudo chmod 700 "$HOME/.ssh"
sudo chmod 600 "$SSH_CONFIG_FILE"


printf "\e[38;5;8m ◻ Checking Grid5000 connection \033[0m"
ssh g5k "exit" >/dev/null 2>&1
if [ $? -ne 0 ]; then
    printf "\n\033[1;31m -----------------------------------------------------------------------------------------------\n"
    printf "      Error: Cannot connect to Grid5000. Please check your username or ssh configuration.\n" >&2
    printf " -----------------------------------------------------------------------------------------------\033[0m\n"
    exit 1
fi

printf "\033[2K"
printf "\r\e[38;5;36m ▣ Valid Grid5000 connection \033[0m"
echo ""

printf "\e[38;5;8m ◻ Check branch name \033[0m"

git rev-parse --verify "$BRANCH_NAME" >/dev/null 2>&1
if [ $? -ne 0 ]; then
    printf "\n\033[1;31m ----------------------------------------------------------------\n"
    printf "      Error: Branch '$BRANCH_NAME' does not exist in the repository.\n" >&2
    printf " ----------------------------------------------------------------\033[0m\n"
    exit 1
fi  
printf "\r\e[38;5;36m ▣ Branch name '$BRANCH_NAME' is valid \033[0m     "
echo ""

printf "\e[38;5;8m ◻ Check site name \033[0m"
ssh $SITE_NAME.g5k "exit" >/dev/null 2>&1
if [ $? -ne 0 ]; then
    printf "\n\033[1;31m ----------------------------------------------------------------------\n"
    printf "      Error: Site name '$SITE_NAME' is not valid or not accessible.\n" >&2
    printf " ----------------------------------------------------------------------\033[0m\n"
    exit 1
fi
printf "\033[2K"
printf "\r\e[38;5;36m ▣ Site name '$SITE_NAME' is valid\033[0m"
echo ""

printf "\e[38;5;8m ◻ Check allocation availability ['$SITE_NAME' | $NUM_NODES nodes | $LIFESPAN hours] \033[0m"
echo 'N' | ssh $SITE_NAME.g5k "funk -m free -r $SITE_NAME:$NUM_NODES -w $LIFESPAN:0:0" >/dev/null 2>&1
if [ $? -ne 0 ]; then
    printf "\n\033[1;31m ----------------------------------------------------------------------\n"
    printf "      Error: Cannot allocate $NUM_NODES nodes for $LIFESPAN hours on '$SITE_NAME' site.\n" >&2
    printf " ----------------------------------------------------------------------\033[0m\n"
    exit 1
fi
printf "\r\e[38;5;36m ▣ Allocation is available ['$SITE_NAME' | $NUM_NODES nodes | $LIFESPAN hours]       \033[0m"

echo ""
echo ""

printf "\e[38;5;8m ◻ Submitting deployment job \033[0m"
JOB_ID=$(ssh $SITE_NAME.g5k "oarsub -l host=$NUM_NODES,walltime=$LIFESPAN -q \"$QUEUE_NAME\" -t deploy \"kadeploy3 ubuntu2204-min && sleep infinity\"" | grep -oP 'OAR_JOB_ID=\K[0-9]+')

printf "\033[2K"
printf "\r\e[38;5;8m ▣ job ID : \e[1m$JOB_ID\e[0m\n"

time_waited=0
printf "\e[38;5;8m ◻ Waiting for job $JOB_ID to complete \033[0m"
while true; do
    STATUS=$(ssh $SITE_NAME.g5k "oarstat -j $JOB_ID -s" | awk '{print $2}')
    if [ "$STATUS" = "Running" ]; then
        printf "\033[2K" 
        printf "\r\e[38;5;36m ▣ Job running.\e[0m\n"
        break
    else if [ "$STATUS" = "Waiting" ] || [ "$STATUS" = "Launching" ] || [ "$STATUS" = "toLaunch" ]; then
        time_waited=$((time_waited + 10))
        printf "\033[2K"
        printf "\r\e[38;5;8m ◻ Waiting time for job running : ${time_waited}s\e[0m"
        sleep 10
    else
        printf "\n\033[1;31m ----------------------------------------------------------------------\n"
        printf "      Error: Job failed. Status: $STATUS\n" >&2
        printf " ----------------------------------------------------------------------\033[0m\n"
        exit 1
    fi
    fi
done

printf "\e[38;5;8m ◻ Retrieving deployed nodes \033[0m"

time_waited=0
while true; do
    OUTPUT=$(ssh $SITE_NAME.g5k "cat OAR.$JOB_ID.stdout | grep -P -i 'Deployment #D-.*-.*-.*-.*-.* done'")
    if [ -n "$OUTPUT" ]; then
        printf "\033[2K" 
        printf "\r\e[38;5;36m ▣ Deployed nodes retrieved.\e[0m\n"
        break
    else
        time_waited=$((time_waited + 10))
        printf "\033[2K"
        printf "\r\e[38;5;8m ◻ Waiting time for retrieving nodes : ${time_waited}s\e[0m"
        sleep 10
    fi
done

nodes_deployed=$(ssh $SITE_NAME.g5k "tail -n$NUM_NODES OAR.$JOB_ID.stdout")
# printf "\e[38;5;8m ▣ Deployed nodes : \e[1m\n$nodes_deployed\e[0m\n"
export nodes_deployed

master_node=$(echo -e "$nodes_deployed" | head -n 1)
export master_node
worker_nodes=$(echo "$nodes_deployed" | tail -n $(($NUM_NODES - 1)))
export worker_nodes
printf "\e[38;5;8m  ▣ Master node :\n\e[1m\e[38;5;104m$master_node\e[0m\n"
printf "\e[38;5;8m  ▣ Worker node(s) :\n\e[1m\e[38;5;108m${worker_nodes[@]}\e[0m\n"


printf "\e[38;5;8m ◻ Building hosts file \033[0m"
hosts_buffer=""

res="$(ssh $SITE_NAME.g5k "getent hosts $master_node | awk '{ print $1 }'")"
cut="$(cut -d ' ' -f 1 <<< $res )"
hosts_buffer+="$cut  master-node\n"

index_node=0
for wk in $worker_nodes; do
    res="$(ssh $SITE_NAME.g5k "getent hosts $wk | awk '{ print $1 }'")"
    cut="$(cut -d ' ' -f 1 <<< $res )"
    hosts_buffer+="$cut  worker$index_node\n"
    index_node=$((index_node + 1))
done

printf "\033[2K"
printf "\r\e[38;5;36m ▣ Hosts file built.\e[0m\n"

printf "\e[38;5;8m ◻ Output directory creation \033[0m"
date=$(date '+%Y-%m-%d-%H.%M')
DIR_OUTPUT_FINAL="$OUTPUT_DIR/$date"
mkdir -p "$DIR_OUTPUT_FINAL"

printf "\033[2K"
printf "\r\e[38;5;36m ▣ Output directory created. [$DIR_OUTPUT_FINAL]\e[0m\n"
printf "\e[38;5;8m ◻ Deploying nodes \033[0m"

./scripts/binscale-node.sh -b "$BRANCH_NAME" -sn "$SITE_NAME" -g "$GIT_REPO" -gn "$master_node" -nn "master-node" -bh "$hosts_buffer" -m &
master_pid=$!

worker_pids=()
index_node=0
for wk in $worker_nodes; do
    ./scripts/binscale-node.sh -b "$BRANCH_NAME" -sn "$SITE_NAME" -g "$GIT_REPO" -gn "$wk" -nn "worker$index_node" -bh "$hosts_buffer" &
    worker_pids+=($!)
    index_node=$((index_node + 1))
done

wait $master_pid

for pid in "${worker_pids[@]}"; do
    wait $pid
done

sleep 1
echo ""
printf "\e[38;5;36m ▣ Nodes deployed.\e[0m\n"
printf "\e[38;5;8m ◻ Worker nodes join cluster \033[0m"

join_command=$(ssh $SITE_NAME.g5k "ssh root@$master_node 'kubeadm token create --print-join-command'")

for wk in $worker_nodes; do
    ssh $SITE_NAME.g5k "ssh root@$wk \"$join_command\"" >/dev/null 2>&1
done
sleep 10
printf "\033[2K"
printf "\r\e[38;5;36m ▣ Worker nodes have joined the cluster.\e[0m\n"

echo ""
printf "\e[38;5;8m ◻ Application deployment \033[0m"
sleep 1
ssh $SITE_NAME.g5k "ssh root@$master_node 'cd binscale-deployment && scripts/deployEnv.sh'"
printf "\e[38;5;36m ▣ Application deployed.\e[0m\n"

printf "\e[38;5;8m ◻ Run experience \033[0m"
ssh $SITE_NAME.g5k "ssh root@$master_node 'cd binscale-deployment && scripts/multinode-launchExperience.sh'"
scp -J "$SITE_NAME.g5k" "root@$master_node:/export/logs/*" "$DIR_OUTPUT_FINAL" > /dev/null 2>&1
printf "\e[38;5;36m ▣ Experience run completed. Logs retrieved. \e[0m[$DIR_OUTPUT_FINAL]\n"

printf "\e[38;5;8m ◻ Job cleanup \033[0m"
ssh $SITE_NAME.g5k "ssh root@$master_node 'rm -R /export/logs/*'"
printf "\033[2K"
printf "\r\e[38;5;36m ▣ Job cleaned up.\e[0m\n"

printf "\e[38;5;8m ◻ Kill job \033[0m"
ssh $SITE_NAME.g5k "oardel $JOB_ID" >/dev/null 2>&1
printf "\033[2K"
printf "\r\e[38;5;88m ▣ Job $JOB_ID killed.\e[0m\n"