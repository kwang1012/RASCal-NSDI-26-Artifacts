#!/bin/bash

# Experiment 7.3: RASCal interruption detection performance
mkdir -p logs/7_3_logs
rm logs/7_3_logs/*.log

# 1. Start the simulated devices
./scripts/start_device_services.sh entity_ids_7_3.txt logs/7_3_logs &

# 2. Start home assistant
cd home-assistant-core
rm ../logs/7_3_logs/home_assistant.log
source .venv/bin/activate
RASC_DEBUG=1 hass -c ./config_7_3 --log-file ../logs/7_3_logs/home_assistant.log
deactivate
cd ..

pkill -f "uv run -m raspberry_pi.run_service"

# Run simulated experiments
uv run -m experiments.exp_7_3_simulated

# 3. Parse the logs to extract detection times
uv run experiments/parse_7_3_result.py