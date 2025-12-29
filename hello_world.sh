#!/bin/bash

# 

echo "=============================="
echo "Running Hello World Example"
echo "=============================="
# 1. Start the simulated devices
./scripts/start_device_services.sh entity_ids_all.txt

# 2. Start home assistant
cd home-assistant-core
source .venv/bin/activate
mkdir -p ./config_tmp
cp ../rasc_configs/automations.yaml ./config_tmp/automations.yaml
cp ../rasc_configs/configuration.yaml ./config_tmp/configuration.yaml
cp ../rasc_configs/routine_setup.yaml ./config_tmp/routine_setup.yaml
cp ../rasc_configs/rasc_sched_example.yaml ./config_tmp/rasc.yaml
hass -c ./config_tmp
rm -rf ./config_tmp
deactivate
cd ..
pkill -f "uv run -m raspberry_pi.run_service"

echo "Hello World Example Completed."
