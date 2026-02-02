#!/bin/bash

PARSE_ONLY=0
if [[ "$1" == "--parse-only" ]]; then
    PARSE_ONLY=1
fi

if [[ "$PARSE_ONLY" -eq 0 ]]; then
    # Experiment 7.4: RASCal scheduling performance
    mkdir -p logs/7_4_logs

    # 1. Overhead
    for DATASET in all hybrid; do
        for MODE in uniform rasc none; do
            echo "=============================="
            echo "Running overhead experiment (dataset: $DATASET, mode: $MODE)"
            echo "=============================="
            mkdir -p logs/7_4_logs/device_${DATASET}_${MODE}_logs
            rm -f logs/7_4_logs/device_${DATASET}_${MODE}_logs/*.log
            # 1. Start the simulated devices
            ./scripts/start_device_services.sh entity_ids_all.txt logs/7_4_logs/device_${DATASET}_${MODE}_logs

            # 2. Start home assistant
            cd home-assistant-core
            source .venv/bin/activate
            rm -f ../logs/7_4_logs/home_assistant_${DATASET}_${MODE}.log
            mkdir -p ./config_tmp
            cp ../rasc_configs/automations.yaml ./config_tmp/automations.yaml
            cp ../rasc_configs/configuration.yaml ./config_tmp/configuration.yaml
            cp ../rasc_configs/routine_setup.yaml ./config_tmp/routine_setup.yaml
            cp ../rasc_configs/rasc_7_4_${DATASET}_${MODE}.yaml ./config_tmp/rasc.yaml
            hass -c ./config_tmp --log-file ../logs/7_4_logs/home_assistant_${DATASET}_${MODE}.log
            rm -rf ./config_tmp
            deactivate
            cd ..
            pkill -f "uv run -m raspberry_pi.run_service"
        done
    done

    # 2. Reschedule Overhead
    # Run reschedule overhead experiments
    estimations=(mean p50 p70 p80 p90 p95 p99)

    for DATASET in all hybrid; do
        for i in ${!estimations[@]}
        do
            echo "=============================="
            echo "Running reschedule overhead experiment (dataset: $DATASET, estimation: ${estimations[$i]})"
            echo "=============================="
            mkdir -p logs/7_4_logs/device_${DATASET}_${estimations[$i]}_logs
            rm -f logs/7_4_logs/device_${DATASET}_${estimations[$i]}_logs/*.log
            # 1. Start the simulated devices
            ./scripts/start_device_services.sh entity_ids_all.txt logs/7_4_logs/device_${DATASET}_${estimations[$i]}_logs

            # 2. Start home assistant
            cd home-assistant-core
            source .venv/bin/activate
            rm -f ../logs/7_4_logs/home_assistant_${DATASET}_${estimations[$i]}.log
            mkdir -p ./config_tmp
            cp ../rasc_configs/automations.yaml ./config_tmp/automations.yaml
            cp ../rasc_configs/configuration.yaml ./config_tmp/configuration.yaml
            cp ../rasc_configs/routine_setup.yaml ./config_tmp/routine_setup.yaml
            cp ../rasc_configs/rasc_7_4_${estimations[$i]}_${DATASET}.yaml ./config_tmp/rasc.yaml
            hass -c ./config_tmp --log-file ../logs/7_4_logs/home_assistant_${DATASET}_${estimations[$i]}.log
            rm -rf ./config_tmp
            deactivate
            cd ..
            pkill -f "uv run -m raspberry_pi.run_service"
        done
    done

    # 3. Scheduling performance
    echo "Running scheduling performance experiments"
    scheduling_policies=(jit fcfs fcfs_post rv sjfw)

    for i in ${!scheduling_policies[@]}
    do
        echo "=============================="
        echo "Running scheduling experiment: ${scheduling_policies[$i]}"
        echo "=============================="
        mkdir -p logs/7_4_logs/device_${scheduling_policies[$i]}_logs
        rm -f logs/7_4_logs/device_${scheduling_policies[$i]}_logs/*.log
        # 1. Start the simulated devices
        ./scripts/start_device_services.sh entity_ids_all.txt logs/7_4_logs/device_${scheduling_policies[$i]}_logs

        # 2. Start home assistant
        cd home-assistant-core
        source .venv/bin/activate
        rm -f ../logs/7_4_logs/home_assistant_${scheduling_policies[$i]}.log
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

fi

uv run experiments/parse_7_4_result.py