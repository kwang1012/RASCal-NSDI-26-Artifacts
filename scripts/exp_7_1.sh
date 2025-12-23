#!/bin/bash

# Experiment 7.1: RASCal detection time on different devices
mkdir -p logs/7_1_logs

for MODE in uniform rasc vopt; do
    echo "=============================="
    echo "Running mode: $MODE"
    echo "=============================="
    mkdir -p logs/7_1_logs/device_${MODE}_logs
    rm logs/7_1_logs/device_${MODE}_logs/*.log
    # 1. Start the simulated devices
    ./scripts/start_device_services.sh entity_ids_7_1.txt logs/7_1_logs/device_${MODE}_logs &

    # 2. Start home assistant
    cd home-assistant-core
    source .venv/bin/activate
    rm ../logs/7_1_logs/home_assistant_${MODE}.log
    RASC_DEBUG=1 hass -c ./config_7_1_${MODE} --log-file ../logs/7_1_logs/home_assistant_${MODE}.log
    deactivate
    cd ..
    pkill -f "uv run -m raspberry_pi.run_service"
done

# 3. Parse the logs to extract detection times
uv run experiments/parse_7_1_result.py