#!/bin/bash

# Experiment 7.3: RASCal interruption detection performance
mkdir -p logs/7_3_logs
rm -f logs/7_3_logs/*.log

# 1. Start the simulated devices
./scripts/start_device_services.sh entity_ids_7_3.txt logs/7_3_logs &

# 2. Start home assistant
cd home-assistant-core
rm -f ../logs/7_3_logs/home_assistant.log
source .venv/bin/activate
mkdir -p ./config_tmp
cp ../rasc_configs/automations.yaml ./config_tmp/automations.yaml
cp ../rasc_configs/configuration.yaml ./config_tmp/configuration.yaml
cp ../rasc_configs/routine_setup.yaml ./config_tmp/routine_setup.yaml
cp ../rasc_configs/rasc_7_3.yaml ./config_tmp/rasc.yaml
RASC_DEBUG=1 hass -c ./config_tmp --log-file ../logs/7_3_logs/home_assistant.log
rm -rf ./config_tmp
deactivate
cd ..

pkill -f "uv run -m raspberry_pi.run_service"

# Run simulated experiments
uv run -m experiments.exp_7_3_simulated

# 3. Parse the logs to extract detection times
uv run experiments/parse_7_3_result.py