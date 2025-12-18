#!/bin/bash
pkill -9 python Python

# Path to the CSV file
csv_file=$1
start_port=9999
i=0
# Read the file
while IFS=, read -ra values; do
    for value in "${values[@]}"; do
        IFS='.' read -ra entity_id <<< "$value"
        uv run raspberry_pi/run_service.py ${entity_id[0]} -e ${value} -p $((start_port+i))&
        i=$((i+1))
    done
done < "$csv_file"