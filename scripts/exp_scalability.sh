#!/bin/bash

# This experiment needs a second node

DEVICE_NODE=amd245.utah.cloudlab.us
DEVICE_USER=kw37
DEVICE_BASE_DIR=/users/kw37/RASCal-NSDI-26-Artifacts

PARSE_ONLY=0
if [[ "$1" == "--parse-only" ]]; then
    PARSE_ONLY=1
fi

if [[ "$PARSE_ONLY" -eq 0 ]]; then
    # 4. Scalability
    # measure cpu/memory with 4 different concurrency levels of routines
    for mode in none; do
        for concurrency in 10 50 100 200; do
            echo "=============================="
            echo "Running scalability experiments (mode=$mode, concurrency=$concurrency)"
            echo "=============================="
            echo "[DEVICE NODE] Starting simulated devices..."
            ssh $DEVICE_USER@$DEVICE_NODE "bash -l -c '
                set -e
                cd $DEVICE_BASE_DIR
                ./scripts/start_device_services.sh \
                    entity_ids_large.txt
            '" &

            DEVICE_PID=$!

            echo "[LOCAL NODE] Starting Home Assistant..."
            # Start home assistant
            cd home-assistant-core
            source .venv/bin/activate
            rm -f ../logs/7_4_logs/home_assistant_scalability.log
            mkdir -p ./config_tmp
            cp ../rasc_configs/automations_large.yaml ./config_tmp/automations.yaml
            cp ../rasc_configs/configuration.yaml ./config_tmp/configuration.yaml
            cp ../rasc_configs/routine_setup_large.yaml ./config_tmp/routine_setup.yaml
            cp ../rasc_configs/rasc_7_4_scalability_${concurrency}_${mode}.yaml ./config_tmp/rasc.yaml
            hass -c ./config_tmp --log-file ../logs/7_4_logs/home_assistant_scalability.log
            rm -rf ./config_tmp
            deactivate
            cd ..

            echo "Cleaning up device node..."

            ssh $DEVICE_USER@$DEVICE_NODE "pkill -f raspberry_pi.run_service" || true
            wait $DEVICE_PID || true
        done
    done
fi

# uv run experiments/parse_scalability.py