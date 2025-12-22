
uv run -m raspberry_pi.run_service $1 &

sleep 1

uv run -m raspberry_pi.devices.${1}

pkill -f "uv run -m raspberry_pi.run_service"