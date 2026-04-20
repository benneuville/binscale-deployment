#!/bin/bash

DEFAULT_NODES=3
DEFAULT_OUTPUT_DIR="."
DEFAULT_INPUT_SCRIPT_FILE="grid5000-deployment-script.sh"
DEFAULT_BRANCH_NAME="master"
DEFAULT_LIFESPAN=2
DEFAULT_SITE_NAME="grenoble"
DEFAULT_GIT_REPO="https://github.com/benneuville/binscale-deployment.git"
DEFAULT_INPUT_GRAPH_FOLDER="./experience/generator/graphs/"
DEFAULT_QUEUE_NAME="default"

SSH_CONFIG_FILE="$HOME/.ssh/config"

NUM_NODES=$DEFAULT_NODES
OUTPUT_DIR=$DEFAULT_OUTPUT_DIR
BRANCH_NAME=$DEFAULT_BRANCH_NAME
LIFESPAN=$DEFAULT_LIFESPAN
SITE_NAME=$DEFAULT_SITE_NAME
GIT_REPO=$DEFAULT_GIT_REPO
QUEUE_NAME=$DEFAULT_QUEUE_NAME
INPUT_GRAPH_FOLDER=$DEFAULT_INPUT_GRAPH_FOLDER
USERNAME=""
IMAGE_TAG="latest"

master_node=""
is_analyze_mode=true
force_skip_merge_check=false
keep_alive=false

worker_nodes=()

usage() {
    echo "Usage: $0 [OPTIONS]"
    echo "Deploy complete experience on Grid5000."
    echo ""
    echo "Options:"
    echo "  -n, --nodes NUM                 Number of nodes to deploy (default: $DEFAULT_NODES)"
    echo "  -o, --output DIR                Output folder (default: $DEFAULT_OUTPUT_DIR)"
    echo "  -b, --branch NAME               Git branch name to use (default: $DEFAULT_BRANCH_NAME)"
    echo "  -ls, --lifespan SECS            Lifespan of the nodes in hours (default: $DEFAULT_LIFESPAN)"
    echo "  -sn, --site NAME                Grid5000 site name (default: $DEFAULT_SITE_NAME)"
    echo "  -u, --username USER             Grid5000 username (no default)"
    echo "  -g, --git-repo URL              Git repository URL (default: $DEFAULT_GIT_REPO)"
    echo "  -q, --queue NAME                Grid5000 queue name (default: $DEFAULT_QUEUE_NAME)"
    echo "  -if, --input-folder PATH        Path to folder of graph defined for experience (default: $DEFAULT_INPUT_GRAPH_FOLDER)"
    echo "  -na, --no-analyze               Unactive analyze logs"
    echo "  -smc, --skip-merge-check        To force skip git merge check"
    echo "  -cb, --current-branch           Use the current git branch"
    echo "  -it, --image-tag TAG            Docker image tag to use for deployment (default: latest)"
    echo "  -k, --keep-alive                Keep the deployed nodes alive after the experience (for debugging)"
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
        -na|--no-analyze)
            is_analyze_mode=false
            ;;
        -smc| --skip-merge-check)
            force_skip_merge_check=true
            ;;
        -if|--input-folder)
            INPUT_GRAPH_FOLDER="$2"
            shift
            ;;
        -cb|--current-branch)
            BRANCH_NAME=$(git rev-parse --abbrev-ref HEAD)
            ;;
        -it|--image-tag)
            IMAGE_TAG="$2"
            shift
            ;;
        -k|--keep-alive)
            keep_alive=true
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
printf "\033[38;5;8m###############################\033[0m \n"
sleep .5

printf " \033[33m▣\033[1;33m Number of nodes\033[0m [$NUM_NODES]\n"
printf " \033[33m▣\033[1;33m Output directory for results\033[0m [$OUTPUT_DIR]\n"
printf " \033[33m▣\033[1;33m Git branch name\033[0m [$BRANCH_NAME]\n"
printf " \033[33m▣\033[1;33m Git repository URL\033[0m [$GIT_REPO]\n"
printf " \033[33m▣\033[1;33m Lifespan (hours)\033[0m [$LIFESPAN]\n"
printf " \033[33m▣\033[1;33m Grid5000 site name\033[0m [$SITE_NAME]\n"
printf " \033[33m▣\033[1;33m Grid5000 username\033[0m [$USERNAME]\n"
printf " \033[33m▣\033[1;33m Grid5000 queue name\033[0m [$QUEUE_NAME]\n"
printf " \033[33m▣\033[1;33m Docker image tag\033[0m [$IMAGE_TAG]\n"

echo ""
sleep 1
printf " \033[33m▣\033[1;33m Experience files targeted : \033[0m\n"
num_exp=0
for file in $INPUT_GRAPH_FOLDER/*.bs.yaml; do
    printf "\033[38;5;88m   ◻ $file\033[0m\n"
    ((num_exp++))
done
printf " \n\033[33m Deploying \033[1;33m$num_exp \033[33mexperience(s)\n\033[0m"
sleep 0.1

read -p " Do you want to proceed? [Y/n]" yn
case $yn in
    [Yy]* ) ;;
    [Nn]* ) exit;;
    * ) echo "Please answer yes or no.";;
esac

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

printf "\n\033[38;5;8m ◻ Adding hosts in ssh \033[0m"

if ! sudo grep -q "^Host g5k" "$SSH_CONFIG_FILE"; then
    sudo echo "$G5K_CONFIG" >> "$SSH_CONFIG_FILE"
fi

if ! sudo grep -q "^Host $SITE_NAME.g5k" "$SSH_CONFIG_FILE"; then
    sudo echo "$SITE_G5K_CONFIG" >> "$SSH_CONFIG_FILE"
fi

sed -i 's/\r$//' $SSH_CONFIG_FILE

# Try to connect to Grid5000 to check username validity
printf "\033[2K"
printf "\r\033[38;5;36m ▣ Hosts added in ssh \033[0m[$SSH_CONFIG_FILE]\n"
sudo chmod 700 "$HOME/.ssh"
sudo chmod 600 "$SSH_CONFIG_FILE"


printf "\033[38;5;8m ◻ Checking Grid5000 connection \033[0m"
ssh g5k "exit" >/dev/null 2>&1
if [ $? -ne 0 ]; then
    printf "\n\033[1;31m -----------------------------------------------------------------------------------------------\n"
    printf "      Error: Cannot connect to Grid5000. Please check your username or ssh configuration.\n" >&2
    printf " -----------------------------------------------------------------------------------------------\033[0m\n"
    exit 1
fi

printf "\033[2K"
printf "\r\033[38;5;36m ▣ Valid Grid5000 connection \033[0m"
echo ""

printf "\033[38;5;8m ◻ Check branch name \033[0m"

git rev-parse --verify "$BRANCH_NAME" >/dev/null 2>&1
if [ $? -ne 0 ]; then
    printf "\n\033[1;31m ----------------------------------------------------------------\n"
    printf "      Error: Branch '$BRANCH_NAME' does not exist in the repository.\n" >&2
    printf " ----------------------------------------------------------------\033[0m\n"
    exit 1
fi
printf "\033[2K"
printf "\r\033[38;5;36m ▣ Branch name '$BRANCH_NAME' is valid \033[0m"
if [ "$force_skip_merge_check" = true ]; then
    printf "\n\033[38;5;8m ◻ Check modification merge skiped... \033[0m"
else

    printf "\n\033[38;5;8m ◻ Check modification merge \033[0m"

    if ! git diff --quiet; then
        printf "\n\033[1;31m ------------------------------------------------------------------\n"
        printf "      Error: Branch '$BRANCH_NAME' have changes not merged on origin.\n" >&2
        printf " ------------------------------------------------------------------\033[0m\n"
        exit 1
    fi

    git fetch origin
    if [ "$(git rev-list --count "$BRANCH_NAME"..origin/"$BRANCH_NAME")" -gt 0 ]; then
        printf "\n\033[1;31m ------------------------------------------------------------------\n"
        printf "      Error: Branch '$BRANCH_NAME' have changes not merged on origin.\n" >&2
        printf " ------------------------------------------------------------------\033[0m\n"
        exit 1
    fi

    if [ "$(git rev-list --count origin/"$BRANCH_NAME".."$BRANCH_NAME")" -gt 0 ]; then
        printf "\n\033[1;31m ------------------------------------------------------------------\n"
        printf "      Error: Branch '$BRANCH_NAME' have unsynchronized changes from origin.\n" >&2
        printf " ------------------------------------------------------------------\033[0m\n"
        exit 1
    fi

    printf "\033[2K"
    printf "\r\033[38;5;36m ▣ Branch name '$BRANCH_NAME' is merged \033[0m"
fi
echo ""

printf "\033[38;5;8m ◻ Check site name \033[0m"
ssh $SITE_NAME.g5k "exit" >/dev/null 2>&1
if [ $? -ne 0 ]; then
    printf "\n\033[1;31m ----------------------------------------------------------------------\n"
    printf "      Error: Site name '$SITE_NAME' is not valid or not accessible.\n" >&2
    printf " ----------------------------------------------------------------------\033[0m\n"
    exit 1
fi
printf "\033[2K"
printf "\r\033[38;5;36m ▣ Site name '$SITE_NAME' is valid\033[0m"
echo ""

printf "\033[38;5;8m ◻ Check allocation availability \033[0m['$SITE_NAME' | $NUM_NODES nodes | $LIFESPAN hours]"
echo 'N' | ssh $SITE_NAME.g5k "funk -m free -r $SITE_NAME:$NUM_NODES -w $LIFESPAN:0:0" >/dev/null 2>&1
if [ $? -ne 0 ]; then
    printf "\n\033[1;31m ----------------------------------------------------------------------\n"
    printf "      Error: Cannot allocate $NUM_NODES nodes for $LIFESPAN hours on '$SITE_NAME' site.\n" >&2
    printf " ----------------------------------------------------------------------\033[0m\n"
    exit 1
fi
printf "\033[2K"
printf "\r\033[38;5;36m ▣ Allocation is available \033[0m['$SITE_NAME' | $NUM_NODES nodes | $LIFESPAN hours]"

echo ""
echo ""

printf "\033[38;5;8m ◻ Submitting deployment job \033[0m"
JOB_ID=$(ssh $SITE_NAME.g5k "oarsub -l host=$NUM_NODES,walltime=$LIFESPAN -q \"$QUEUE_NAME\" -t deploy \"kadeploy3 ubuntu2204-min && sleep infinity\"" | grep -oP 'OAR_JOB_ID=\K[0-9]+')

trap "ssh $SITE_NAME.g5k \"oardel $JOB_ID\"; printf \"\033[38;5;88mJob $JOB_ID killed.\033[0m\n\"; exit 0" SIGINT

printf "\033[2K"
printf "\r\033[38;5;8m ▣ job ID : \033[1m$JOB_ID\033[0m\n"

time_waited=0
printf "\033[38;5;8m ◻ Waiting for job $JOB_ID to complete \033[0m"
while true; do
    STATUS=$(ssh $SITE_NAME.g5k "oarstat -j $JOB_ID -s" | awk '{print $2}')
    if [ "$STATUS" = "Running" ]; then
        printf "\033[2K" 
        printf "\r\033[38;5;36m ▣ Job running.\033[0m\n"
        break
    else
        if [ "$STATUS" = "Waiting" ] || [ "$STATUS" = "Launching" ] || [ "$STATUS" = "toLaunch" ]; then
            time_waited=$((time_waited + 10))
            printf "\033[2K"
            printf "\r\033[38;5;8m ◻ Waiting time for job running : ${time_waited}s\033[0m"
            sleep 10
        else
            printf "\n\033[1;31m ----------------------------------------------------------------------\n"
            printf "      Error: Job failed. Status: $STATUS\n" >&2
            printf " ----------------------------------------------------------------------\033[0m\n"
            exit 1
        fi
    fi
done

printf "\033[38;5;8m ◻ Retrieving deployed nodes \033[0m"

time_waited=0
while true; do
    OUTPUT=$(ssh "$SITE_NAME.g5k" "cat OAR.$JOB_ID.stdout | grep -P -i 'Deployment #D-.*-.*-.*-.*-.* done'")
    if [ -n "$OUTPUT" ]; then
        printf "\033[2K" 
        printf "\r\033[38;5;36m ▣ Deployed nodes retrieved.\033[0m\n"
        break
    else
        time_waited=$((time_waited + 10))
        printf "\033[2K"
        printf "\r\033[38;5;8m ◻ Waiting time for retrieving nodes : ${time_waited}s\033[0m"
        sleep 10
    fi
done

nodes_deployed=$(ssh "$SITE_NAME.g5k" "tail -n$NUM_NODES OAR.$JOB_ID.stdout")

master_node=$(echo -e "$nodes_deployed" | head -n 1)
export master_node
worker_nodes=$(echo "$nodes_deployed" | tail -n $(($NUM_NODES - 1)))
export worker_nodes
printf "\033[38;5;8m  ▣ Master node :\n\033[1m\033[38;5;104m$master_node\033[0m\n"
printf "\033[38;5;8m  ▣ Worker node(s) :\n\033[1m\033[38;5;108m${worker_nodes[@]}\033[0m\n"


printf "\033[38;5;8m ◻ Building hosts file \033[0m"
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
printf "\r\033[38;5;36m ▣ Hosts file built.\033[0m\n"

printf "\033[38;5;8m ◻ Deploying nodes \033[0m\n"

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
printf "\033[38;5;36m ▣ Nodes deployed.\033[0m\n"
printf "\033[38;5;8m ◻ Worker nodes join cluster \033[0m"

join_command=$(ssh $SITE_NAME.g5k "ssh root@$master_node 'kubeadm token create --print-join-command'")

for wk in $worker_nodes; do
    ssh $SITE_NAME.g5k "ssh root@$wk \"$join_command\"" >/dev/null 2>&1
done
sleep 10
printf "\033[2K"
printf "\r\033[38;5;36m ▣ Worker nodes have joined the cluster.\033[0m\n"

echo ""
printf "\033[38;5;8m ◻ Application deployment \033[0m\n"
sleep 1
ssh $SITE_NAME.g5k "ssh root@$master_node \"cd binscale-deployment && scripts/deployEnv.sh\""
stty sane
printf "\033[38;5;36m ▣ Application deployed.\033[0m\n"

buff_output_exp="\033[0m Experience results :\033[0m\n"

folders_to_analyze=()

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
sed -i 's/\r$//' "$SCRIPT_DIR"/log_analysis/*.sh

for file in $INPUT_GRAPH_FOLDER/*.bs.yaml; do

    printf "\033[38;5;8m ◻ Run experience \033[0m[$file]"

    file_name=$(basename "$file" .bs.yaml | tr " " "_")
    date=$(date '+%Y-%m-%d-%H.%M')
    DIR_OUTPUT_FINAL="$OUTPUT_DIR/$date-$file_name-$NUM_NODES-nodes"

    printf "\033[38;5;8m ◻ SSH connection \033[0m[$file]"
    ssh $SITE_NAME.g5k "ssh root@$master_node \"cd binscale-deployment && scripts/multinode-launchExperience.sh "$file" "$IMAGE_TAG"\""

    file_name_escaped="${file_name//\"/\\\"}"
    if [ $? -ne 0 ]; then
        buff_output_exp+="\033[38;5;88m ◻ Experience [$file_name_escaped] failed.\033[0m\n"
        break;
    else
        buff_output_exp+="\033[38;5;36m ▣ Experience [$file_name_escaped] completed.\033[0m\n"
        folders_to_analyze+="$DIR_OUTPUT_FINAL"
    fi

    sleep 20

    printf "\033[38;5;8m ◻ Output directory creation \033[0m"
    mkdir -p "$DIR_OUTPUT_FINAL"
    cp "$file" "$DIR_OUTPUT_FINAL"

    printf "\033[2K"
    printf "\r\033[38;5;36m ▣ Output directory created. [$DIR_OUTPUT_FINAL]\033[0m\n"

    scp -oStrictHostKeyChecking=no -oUserKnownHostsFile=/dev/null -J "$SITE_NAME.g5k" "root@$master_node:/export/logs/*" "$DIR_OUTPUT_FINAL"
    printf "\033[38;5;36m ▣ Experience [$file] run completed. Logs retrieved in \033[0m[$DIR_OUTPUT_FINAL]\n"
    
    if [ "$is_analyze_mode" = true ]; then
        printf "\r\033[38;5;36m ▣ Analyze processed in parallel [$file_name]\033[0m\n"
        {
            cd $DIR_OUTPUT_FINAL || exit 1
            "$SCRIPT_DIR/log_analysis/extractLogs.sh" filebeat* >/dev/null 2>&1
            python3 "$SCRIPT_DIR/log_analysis/mtnd-consumer-analysis.py" consumer_logs.txt &
            python3 "$SCRIPT_DIR/log_analysis/mtnd-controller-analysis.py" controller_logs.txt &
            python3 "$SCRIPT_DIR/log_analysis/mtnd-experience-analysis.py" consumer_logs.txt controller_logs.txt &
            python3 "$SCRIPT_DIR/../experience/generator/graph_visualizor.py" $SCRIPT_DIR/../$file &
            wait
        } &
    fi
done

printf "\033[38;5;8m ◻ Job cleanup \033[0m"
ssh $SITE_NAME.g5k "ssh root@$master_node \"rm -R /export/logs/*\""
printf "\033[2K"
printf "\r\033[38;5;36m ▣ Job cleaned up.\033[0m\n"
if [ "$keep_alive" = false ]; then
    printf "\033[38;5;8m ◻ Kill job \033[0m"
    ssh $SITE_NAME.g5k "oardel $JOB_ID" >/dev/null 2>&1
    printf "\033[2K"
    printf "\r\033[38;5;88m ▣ Job $JOB_ID killed.\033[0m\n"
else
    printf "\033[38;5;88m ▣ Job $JOB_ID kept alive.\033[0m\n"
fi

if [ "$is_analyze_mode" = true ]; then
    printf "\033[38;5;8m ◻ Waiting for analysis process \033[0m\n"
    wait
    printf "\033[38;5;8m ▣ Analysis process ended \033[0m\n"
else
    printf "\033[38;5;8m ◻ You can analyze files by going to folder and execute :
   \033[38;5;8mExtract logs \033[0m[./scripts/log_analysis/extractLogs.sh filebeat*]
   \033[38;5;8mScript to analyze \033[0m[./scripts/log_analysis/mtnd-consumer-analysis.py consumer_logs.txt] \033[0m\n"
fi

printf '%b' "$buff_output_exp"

exit 0
