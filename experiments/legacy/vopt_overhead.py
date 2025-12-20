import time
import json

from rasc.rasc_polling import get_best_distribution, get_polls, get_uniform_polls

actions = [
    "cover.rpi_device_door,open_cover,0",
    "cover.rpi_device_door,close_cover,0",
    "climate.rpi_device_thermostat,set_temperature,68,69",
    "cover.rpi_device_shade,open_cover,0",
    "cover.rpi_device_shade,close_cover,0"
]

with open("experiments/vopt_overhead.json") as f:
    data = json.load(f)

for action in actions:
    print(f"Action: {action}")
    action_data = data[action]['ct_history']
    print(f"Average length: {sum(action_data) / len(action_data)}")
    dist = get_best_distribution(action_data)
    
    # uniform
    start_time = time.time()
    polls = get_uniform_polls(dist.ppf(0.99))
    end_time = time.time()
    print(f"Time taken for uniform polls: {end_time - start_time} seconds")
    
    # rasc
    start_time = time.time()
    polls = get_polls(dist)
    end_time = time.time()
    print(f"Time taken for Rasc polls: {end_time - start_time} seconds")

    # vopt
    # start_time = time.time()
    # polls = get_polls(dist, use_vopt=True)
    # print(polls)
    # end_time = time.time()
    # print(f"Time taken for VOPT polls: {end_time - start_time} seconds")