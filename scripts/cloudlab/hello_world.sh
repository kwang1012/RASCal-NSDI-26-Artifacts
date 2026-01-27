#!/bin/bash

# ==============================
# CloudLab Hello World Example
# ==============================

DEVICE_NODE=kw37@c220g2-011002.wisc.cloudlab.us
DEVICE_BASE_DIR=RASCal-NSDI-26-Artifacts
echo "=============================="
echo "Running Hello World Example (cloudlab)"
echo "=============================="

# --------------------------------------------------
# 1. Start the simulated devices on DEVICE_NODE
# --------------------------------------------------
echo "[Node A] Starting simulated devices..."

ssh $DEVICE_NODE "bash -l -c '
    set -e
    cd $DEVICE_BASE_DIR
    ./scripts/start_device_services.sh entity_ids_all.txt
'" &

DEVICE_SSH_PID=$!

# (Optional) give devices a moment to come up
sleep 2

# --------------------------------------------------
# 2. Start Home Assistant on THIS node
# --------------------------------------------------
echo "[Node B] Starting Home Assistant..."

cd home-assistant-core || exit 1
source .venv/bin/activate

mkdir -p ./config_tmp
cp ../rasc_configs/automations.yaml ./config_tmp/automations.yaml
cp ../rasc_configs/configuration_cloudlab.yaml ./config_tmp/configuration.yaml
cp ../rasc_configs/routine_setup.yaml ./config_tmp/routine_setup.yaml
cp ../rasc_configs/rasc_sched_example.yaml ./config_tmp/rasc.yaml

hass -c ./config_tmp

# --------------------------------------------------
# 3. Cleanup
# --------------------------------------------------
echo "Cleaning up..."

rm -rf ./config_tmp
deactivate
cd ..

# Kill device services on node A
ssh $DEVICE_NODE "pkill -f 'raspberry_pi.run_service'"

wait $DEVICE_SSH_PID

echo "Hello World Example Completed."
