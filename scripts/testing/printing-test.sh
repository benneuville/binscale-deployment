#!/bin/bash

is_analyze_mode=true
DIR_OUTPUT_FINAL="2026-01-07-14.15"

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
current_path=$PWD
sed -i 's/\r$//' $SCRIPT_DIR/../log_analysis/extractLogs.sh
if [ "$is_analyze_mode" = true ]; then
    cd "$current_path/$DIR_OUTPUT_FINAL"
    $SCRIPT_DIR/../log_analysis/extractLogs.sh filebeat*
    python3 $SCRIPT_DIR/../log_analysis/mtnd-analyze.py consumer_logs.txt
    cd "$current_path"
else
    printf "\033[38;5;8m ◻ Files to analyze in \033[0m[$DIR_OUTPUT_FINAL]
   \033[38;5;8mExtract logs \033[0m[./scripts/log_analysis/extractLogs.sh filebeat*]
   \033[38;5;8mScript to analyze \033[0m[./scripts/log_analysis/mtnd-analyze.py consumer_logs.txt] \033[0m\n"
fi