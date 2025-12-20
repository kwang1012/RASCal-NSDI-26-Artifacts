#!/bin/bash

# Experiment 7.4: RASCal scheduling performance
mkdir -p logs/7_4_logs

# 1. Start the simulated devices
./scripts/start_device_services.sh entity_ids_all.txt logs/7_4_logs &

cd home_assistant_core
source .venv/bin/activate
# 1. Overhead
# Run overhead experiments
estimations=(mean p50 p99)

for i in ${!estimations[@]}
do
    echo "Running overhead experiment (${estimations[$i]})"
    rm ./logs/7_4_logs/home_assistant_${estimations[$i]}.log
    hass -c ./config_7_4_${estimations[$i]} --log-file ./logs/7_4_logs/home_assistant_${estimations[$i]}.log
    sleep 2
done

# Run baseline
echo "Running overhead experiment baseline"
rm ./logs/7_4_logs/home_assistant_baseline.log
hass -c ./config_7_4_baseline --log-file ./logs/7_4_logs/home_assistant_baseline.log
sleep 2

# 2. Scheduling performance
echo "Running scheduling performance experiments"
scheduling_policies=(jit rv sjfw fcfs fcfs_post)

for i in ${!scheduling_policies[@]}
do
    echo "Running experiment with scheduler: ${scheduling_policies[$i]}"
    rm ./logs/7_4_logs/home_assistant_${scheduling_policies[$i]}.log
    hass -c ./config_7_4_${scheduling_policies[$i]} --log-file ./logs/7_4_logs/home_assistant_${scheduling_policies[$i]}.log
    sleep 2
done
deactivate
cd ..

pkill -f "uv run -m raspberry_pi.run_service"

# 3. Scalability
# echo "Running scalability experiments"

# rm ./logs/7_4_logs/home_assistant_${scheduling_policies[$i]}.log
# hass -c ./config_7_4_${scheduling_policies[$i]} --log-file ./logs/7_4_logs/home_assistant_${scheduling_policies[$i]}.log


# 3. Parse the logs to extract
uv run experiments/parse_7_4_result.py