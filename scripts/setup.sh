mkdir -p logs
mkdir -p results

uv sync

cd home-assistant-core
script/setup
cd ..