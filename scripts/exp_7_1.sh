#!/bin/bash

# Experiment 7.1: RASCal detection time on different devices

# 1. Start the simulated devices
./scripts/start_device_services.sh entity_ids_7_1.txt &

# 2. Start home assistant
hass -c ./config-7_1


# 3. Parse the logs to extract detection times
uv run experiments/parse_log.py