#!/bin/bash

# Experiment 7.1: RASCal detection time on different devices
mkdir -p logs/7_1_logs

# 1. Start the simulated devices
./scripts/start_device_services.sh entity_ids_7_1.txt logs/7_1_logs &

# 2. Start home assistant
cd home-assistant-core
source .venv/bin/activate
rm ../logs/7_1_logs/home_assistant_uniform.log
hass -c ./config_7_1_uniform --log-file ../logs/7_1_logs/home_assistant_uniform.log
rm ../logs/7_1_logs/home_assistant_rasc.log
hass -c ./config_7_1_rasc --log-file ../logs/7_1_logs/home_assistant_rasc.log
rm ../logs/7_1_logs/home_assistant_vopt.log
hass -c ./config_7_1_vopt --log-file ../logs/7_1_logs/home_assistant_vopt.log
deactivate
cd ..

pkill -f "uv run -m raspberry_pi.run_service"
# 3. Parse the logs to extract detection times
uv run experiments/parse_7_1_result.py