#!/bin/bash

# Experiment 7.4: RASCal scheduling performance
mkdir -p logs/7_4_logs

# 1. Overhead
# Run overhead experiments
estimations=(mean p50 p99)

for i in ${!estimations[@]}
do
    echo "=============================="
    echo "Running overhead experiment (${estimations[$i]})"
    echo "=============================="
    mkdir -p logs/7_4_logs/device_${estimations[$i]}_logs
    rm logs/7_4_logs/device_${estimations[$i]}_logs/*.log
    # 1. Start the simulated devices
    ./scripts/start_device_services.sh entity_ids_all.txt logs/7_4_logs/device_${estimations[$i]}_logs

    # 2. Start home assistant
    cd home-assistant-core
    source .venv/bin/activate
    rm ./logs/7_4_logs/home_assistant_${estimations[$i]}.log
    mkdir -p ./config_tmp
    cp ../rasc_configs/automations.yaml ./config_tmp/automations.yaml
    cp ../rasc_configs/configuration.yaml ./config_tmp/configuration.yaml
    cp ../rasc_configs/routine_setup.yaml ./config_tmp/routine_setup.yaml
    cp ../rasc_configs/rasc_7_4_${estimations[$i]}.yaml ./config_tmp/rasc.yaml
    hass -c ./config_tmp --log-file ../logs/7_4_logs/home_assistant_${estimations[$i]}.log
    rm -rf ./config_tmp
    deactivate
    cd ..
    pkill -f "uv run -m raspberry_pi.run_service"
done

# Run baseline
echo "=============================="
echo "Running overhead experiment (baseline)"
echo "=============================="
mkdir -p logs/7_4_baseline_logs
rm logs/7_4_baseline_logs/*.log
# 1. Start the simulated devices
./scripts/start_device_services.sh entity_ids_all.txt logs/7_4_baseline_logs

# 2. Start home assistant
cd home-assistant-core
source .venv/bin/activate
rm ./logs/7_4_logs/home_assistant_baseline.log
mkdir -p ./config_tmp
cp ../rasc_configs/automations.yaml ./config_tmp/automations.yaml
cp ../rasc_configs/configuration.yaml ./config_tmp/configuration.yaml
cp ../rasc_configs/routine_setup.yaml ./config_tmp/routine_setup.yaml
cp ../rasc_configs/rasc_7_4_baseline.yaml ./config_tmp/rasc.yaml
hass -c ./config_tmp --log-file ../logs/7_4_logs/home_assistant_baseline.log
rm -rf ./config_tmp
deactivate
cd ..
pkill -f "uv run -m raspberry_pi.run_service"

# 2. Scheduling performance
echo "Running scheduling performance experiments"
scheduling_policies=(jit rv sjfw fcfs fcfs_post)

for i in ${!scheduling_policies[@]}
do
    echo "=============================="
    echo "Running scheduling experiment: ${scheduling_policies[$i]}"
    echo "=============================="
    mkdir -p logs/7_4_logs/device_${scheduling_policies[$i]}_logs
    rm logs/7_4_logs/device_${scheduling_policies[$i]}_logs/*.log
    # 1. Start the simulated devices
    ./scripts/start_device_services.sh entity_ids_all.txt logs/7_4_logs/device_${scheduling_policies[$i]}_logs

    # 2. Start home assistant
    cd home-assistant-core
    source .venv/bin/activate
    rm .,/logs/7_4_logs/home_assistant_${scheduling_policies[$i]}.log
    mkdir -p ./config_tmp
    cp ../rasc_configs/automations.yaml ./config_tmp/automations.yaml
    cp ../rasc_configs/configuration.yaml ./config_tmp/configuration.yaml
    cp ../rasc_configs/routine_setup.yaml ./config_tmp/routine_setup.yaml
    cp ../rasc_configs/rasc_7_4_${scheduling_policies[$i]}.yaml ./config_tmp/rasc.yaml
    hass -c ./config_tmp --log-file ../logs/7_4_logs/home_assistant_${scheduling_policies[$i]}.log
    rm -rf ./config_tmp
    deactivate
    cd ..
    pkill -f "uv run -m raspberry_pi.run_service"
done

# 3. Scalability
# echo "=============================="
# echo "Running scalability experiments"
# echo "=============================="
# mkdir -p logs/7_4_logs/scalability_logs
# rm logs/7_4_logs/scalability_logs/*.log
# # 1. Start the simulated devices
# ./scripts/start_device_services.sh entity_ids_large.txt logs/7_4_logs/scalability_logs
# # 2. Start home assistant
# cd home-assistant-core
# source .venv/bin/activate
# rm ./logs/7_4_logs/home_assistant_scalability.log
# mkdir -p ./config_tmp
# cp ../rasc_configs/automations_large.yaml ./config_tmp/automations.yaml
# cp ../rasc_configs/configuration.yaml ./config_tmp/configuration.yaml
# cp ../rasc_configs/routine_setup.yaml ./config_tmp/routine_setup.yaml
# cp ../rasc_configs/rasc_7_4_large.yaml ./config_tmp/rasc.yaml
# hass -c ./config_tmp --log-file ../logs/7_4_logs/home_assistant_scalability.log
# rm -rf ./config_tmp
# deactivate
# cd ..
# pkill -f "uv run -m raspberry_pi.run_service"

# 3. Parse the logs to extract
uv run experiments/parse_7_4_result.py