DEFAULT_NODES=3
DEFAULT_OUTPUT_DIR="."
DEFAULT_INPUT_SCRIPT_FILE="grid5000-deployment-script.sh"
DEFAULT_BRANCH_NAME="master"
DEFAULT_LIFESPAN=2
DEFAULT_SITE_NAME="grenoble"
SSH_CONFIG_FILE="$HOME/.ssh/config"

NUM_NODES=$DEFAULT_NODES
OUTPUT_DIR=$DEFAULT_OUTPUT_DIR
BRANCH_NAME=$DEFAULT_BRANCH_NAME
LIFESPAN=$DEFAULT_LIFESPAN
SITE_NAME=$DEFAULT_SITE_NAME
USERNAME=""

master_node=""

printf "\n\e[38;5;8m ◻ Checking environment existence & deployment requirements \033[0m\n"

printf "\e[38;5;8m ◻ Verifying environment image on Grid5000 ['$SITE_NAME'] \033[0m"

# verify if tar.zst exist on server 
ssh $SITE_NAME.g5k "ls ~/environment/ | grep 'binscale_environment_image.tar.zst'" >/dev/null 2>&1
if [ $? -ne 0 ]; then
    printf "\n\033[1;31m ----------------------------------------------------------------------\n"
    printf "      Error: Environment image 'binscale_environment_image.tar.zst' is missing on Grid5000 server.\n"
    printf "      Please upload it to '~/environment/' directory before proceeding.\n"
    printf " ----------------------------------------------------------------------\033[0m\n"
    exit 1
fi
printf "\033[2K"
printf "\r\e[38;5;36m ▣ Environment image exists on Grid5000 ['$SITE_NAME'] \033[0m\n"


printf "\r\e[38;5;8m ◻ Verify environment deployment on Kadeploy/Kaenv \033[0m"
scp ./environment/binscale-deployment-environment.yaml $SITE_NAME.g5k:~/environment/binscale-deployment-environment.yaml >/dev/null 2>&1
# verify if environment exist, otherwise create it
ssh $SITE_NAME.g5k "kaenv3 -l | grep -q 'binscale-deployment-ubuntu'"
if [ $? -ne 0 ]; then
    printf "\r\e[38;5;125m ◻ Missing environment on Kadeploy/Kaenv, deploying it \033[0m"
    sleep 1
    ssh $SITE_NAME.g5k "kadeploy3 -a ~/environment/binscale-deployment-environment.yaml" >/dev/null 2>&1
    if [ $? -ne 0 ]; then
        printf "\n\033[1;31m ----------------------------------------------------------------------\n"
        printf "      Error: Failed to deploy environment 'binscale-deployment-ubuntu' on Kadeploy.\n" >&2
        printf " ----------------------------------------------------------------------\033[0m\n"
        exit 1
    fi
    ssh $SITE_NAME.g5k "kaenv3 -a ~/environment/binscale-deployment-environment.yaml" >/dev/null 2>&1
    if [ $? -ne 0 ]; then
        printf "\n\033[1;31m ----------------------------------------------------------------------\n"
        printf "      Error: Failed to register environment 'binscale-deployment-ubuntu' on Kaenv.\n" >&2
        printf " ----------------------------------------------------------------------\033[0m\n"
        exit 1
    fi
    printf "\033[2K"
    printf "\r\e[38;5;36m ▣ Environment 'binscale-deployment-ubuntu' deployed on Kadeploy/Kaenv \033[0m"
else
    printf "\033[2K"
    printf "\r\e[38;5;36m ▣ Environment 'binscale-deployment-ubuntu' already exists on Kadeploy/Kaenv \033[0m"
fi

printf "\e[2A"
printf "\r\e[38;5;36m ▣ Deployment requirements verified \033[0m"
printf "\e[u"
