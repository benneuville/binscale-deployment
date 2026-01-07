
# printf "\e[38;5;8m ◻ Deploying nodes \033[0m\n"

# printf "\e[38;5;8m    ◻ Deploying master node \033[0m\n"

# printf "\e[38;5;8m    ◻ Deploying worker nodes \033[0m\n"

# sleep 3

# printf "\e[2A\033[2K\r\e[38;5;36m    ▣ Master node deployment completed.\e[0m\n\e[1B"
# sleep 1
# printf "\e[1A\033[2K\r\e[38;5;36m    ▣ Worker nodes deployment completed.\e[0m\n"
# sleep .5
# printf "\e[3A\033[2K\r\e[38;5;36m ▣ Nodes deployed.\e[0m\n\e[2B"

# echo "Starting deployment script..."

#!/bin/bash

FIFO_PATH="/tmp/fifos"
mkdir -p "$FIFO_PATH"
rm -f "$FIFO_PATH/"*

fifos=()
# Build a FIFO for each command
for cmd in "$@"; do
    fifo="${cmd// /_}"
    mkfifo "$FIFO_PATH/$fifo"
    fifos+=("$fifo")
    eval "$cmd" > "$FIFO_PATH/$fifo" 2>&1 &
done

# Initialize the lines array: for each FIFO, store its name followed by 3 placeholders
lines=()
for fifo in "${fifos[@]}"; do
    lines+=("$fifo")
    for ((i=0; i<3; i++)); do
        lines+=(".")
    done
done

echo "Number of FIFOs: ${#fifos[@]}"
echo "Lines array size: ${#lines[@]}"

# Calculate the number of lines to move up
lines_to_move_up=$(( ${#fifos[@]} * 4 ))

# Use the ANSI escape code to move the cursor up
count_finished_fifos=0
# Read from FIFOs and update the last 3 lines for each
count=0
while true; do
    if [ ${#fifos[@]} -eq $count_finished_fifos ]; then
        break
    fi
    for i in "${!fifos[@]}"; do
        # Read a line from the FIFO
        if [ "${fifos[$i]}" == "finished" ]; then
            continue
        fi
        if read -r line < "$FIFO_PATH/${fifos[$i]}"; then
            # Shift the lines for this FIFO
            lines[$((i*4+1))]="${lines[$((i*4+2))]}"
            lines[$((i*4+2))]="${lines[$((i*4+3))]}"
            lines[$((i*4+3))]="$line"
        else
            lines[$((i*4+1))]="${lines[$((i*4+2))]}"
            lines[$((i*4+2))]="${lines[$((i*4+3))]}"
            lines[$((i*4+3))]="end of fifo"
            ((count_finished_fifos++))
            fifos[$i]="finished"
        fi
    done

    for ((i=0; i<${#fifos[@]}; i++)); do
        echo "${lines[$i * 4]} $count"
        printf "\033[2K"
        printf "\e[38;5;8m   ${lines[$i*4+1]}\n\e[0m"
        printf "\033[2K"
        printf "\e[38;5;8m   ${lines[$i*4+2]}\n\e[0m"
        printf "\033[2K"
        printf "\e[38;5;8m   ${lines[$i*4+3]}\n\e[0m"
    done
    (( count++ ))
    # Print the last 3 lines for each FIFO
    printf "\033[%sA" "$lines_to_move_up"
done
echo "end"
printf "\033[%sB" "$lines_to_move_up"