#!/bin/bash

# Experiment 7.1: RASCal detection time on different devices
mkdir -p logs/7_1_logs

# 1. Start the simulated devices
./scripts/start_device_services.sh entity_ids_7_1.txt logs/7_1_logs &

# 2. Start home assistant
cd home-assistant-core
rm ../logs/7_1_logs/home_assistant.log
source .venv/bin/activate
hass -c ./config_7_1 --log-file ../logs/7_1_logs/home_assistant.log
deactivate
cd ..

pkill -f "uv run -m raspberry_pi.run_service"
# 3. Parse the logs to extract detection times
# uv run experiments/parse_log.py