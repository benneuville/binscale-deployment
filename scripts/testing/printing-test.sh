
printf "\e[38;5;8m ◻ Deploying nodes \033[0m\n"

printf "\e[38;5;8m    ◻ Deploying master node \033[0m\n"

printf "\e[38;5;8m    ◻ Deploying worker nodes \033[0m\n"

sleep 3

printf "\e[2A\033[2K\r\e[38;5;36m    ▣ Master node deployment completed.\e[0m\n\e[1B"
sleep 1
printf "\e[1A\033[2K\r\e[38;5;36m    ▣ Worker nodes deployment completed.\e[0m\n"
sleep .5
printf "\e[3A\033[2K\r\e[38;5;36m ▣ Nodes deployed.\e[0m\n\e[2B"

echo "Starting deployment script..."