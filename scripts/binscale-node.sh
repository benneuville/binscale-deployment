#!/bin/bash
BRANCH_NAME=""
SITE_NAME=""
GIT_REPO=""
NODE_G5K_NAME=""
NODE_NAME=""
BUFFER_HOSTS=""
is_master_node=false
OUTPUT_DIR="."

usage() {
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  -b, --branch NAME           Git branch name (no default)"
    echo "  -sn, --site NAME            Grid5000 site name (no default)"
    echo "  -g, --git-repo URL          Git repository URL (no default)"
    echo "  -gn, --g5k-node NAME        Grid5000 node name (no default)"
    echo "  -nn, --node-name NAME       Desired hostname for the node (no default)"
    echo "  -bh, --buffer-hosts string  String containing hosts entries to add to /etc/hosts (no default)"
    echo "  -m, --master-node            Flag to indicate if this node is the master node"
    echo "  -o, --output DIR            Output directory"
    echo ""
    echo "  -h, --help                  for help"
    echo ""
    exit 0
}

while [[ "$#" -gt 0 ]]; do
    case $1 in
        -b|--branch)
            BRANCH_NAME="$2"
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
        -gn|--g5k-node)
            NODE_G5K_NAME="$2"
            shift
            ;;
        -nn|--node-name)
            NODE_NAME="$2"
            shift
            ;;
        -bh|--buffer-hosts)
            BUFFER_HOSTS="$2"
            shift
            ;;
        -m|--master-node)
            is_master_node=true
            ;;
        -o|--output)
            OUTPUT_DIR="$2"
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

if [ -z "$BRANCH_NAME" ] || [ -z "$SITE_NAME" ] || [ -z "$GIT_REPO" ] || [ -z "$NODE_G5K_NAME" ] || [ -z "$NODE_NAME" ] || [ -z "$BUFFER_HOSTS" ]; then
    printf "\033[1;31m -------------------------------------------\n"
    printf "      Error: Missing required arguments.\n" >&2
    printf "\e[0;38;5;8m           -\e[4mh\e[0m or --\e[4mhelp\e[0m for help \n"
    printf "\033[1;31m -------------------------------------------\033[0m\n"
    exit 1
    usage
    exit 1
fi

printf "\e[38;5;8m ▣ config $NODE_NAME on '$NODE_G5K_NAME' \033[0m\n"
ssh $SITE_NAME.g5k "ssh root@$NODE_G5K_NAME \"sudo hostnamectl set-hostname $NODE_NAME\""
ssh $SITE_NAME.g5k "ssh root@$NODE_G5K_NAME 'printf \"%b\" \"$BUFFER_HOSTS\" > /etc/hosts'"
ssh $SITE_NAME.g5k "ssh root@$NODE_G5K_NAME \"git clone $GIT_REPO\""
ssh $SITE_NAME.g5k "ssh root@$NODE_G5K_NAME \"cd binscale-deployment && git checkout $BRANCH_NAME && chmod +x scripts/* && sed -i 's/\r$//' scripts/*.*\""


if [ "$is_master_node" = true ]; then
    printf "\e[38;5;8m ▣ Setting up MASTER NODE on '$NODE_G5K_NAME' \033[0m\n"
    ssh $SITE_NAME.g5k "ssh root@$NODE_G5K_NAME \"sed -i 's/\r$//' binscale-deployment/scripts/*.* && binscale-deployment/scripts/multinode-master.sh\" 2>&1" | tee $OUTPUT_DIR/master_node_setup.log 2>&1
else
    printf "\e[38;5;8m ▣ Setting up WORKER NODE on '$NODE_G5K_NAME' \033[0m\n"
    ssh $SITE_NAME.g5k "ssh root@$NODE_G5K_NAME \"sed -i 's/\r$//' binscale-deployment/scripts/*.* && binscale-deployment/scripts/multinode-worker.sh\" 2>&1" | tee $OUTPUT_DIR/worker_node_"$NODE_NAME"_setup.log 2>&1
fi