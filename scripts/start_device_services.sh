#!/bin/bash
pkill -f "uv run -m raspberry_pi.run_service"

# Path to the CSV file
csv_file="raspberry_pi/$1"
start_port=9999
i=0
log_dir="$2"

log_args=()
if [[ -n "$log_dir" ]]; then
    log_args=(-l "$log_dir")
fi

# Read the file
while IFS=, read -ra values; do
    for value in "${values[@]}"; do
        IFS='.' read -ra entity_id <<< "$value"
        uv run -m raspberry_pi.run_service \
            "${entity_id[0]}" \
            -e "$value" \
            -p $((start_port + i)) \
            "${log_args[@]}" &
        i=$((i+1))
    done
done < "$csv_file"