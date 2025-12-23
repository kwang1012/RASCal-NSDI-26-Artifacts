import json
from typing import Any
from datetime import datetime
import matplotlib.pyplot as plt
import pandas as pd

def _parse_ha(ha_lines):
    runs = []
    current_run: dict[str, Any] | None = None
    for line in ha_lines:
        if "DEBUG" not in line:
            continue
        if "RASC config" in line:
            continue
        if "Max polls" in line and current_run is None:
            current_run = {"status": "up_start", "up_start": int(line[line.find(
                "Max polls:") + len("Max polls:"):].strip().strip("\x1b[0m\n"))}
        elif "Max polls" in line and current_run and current_run["status"] == "up_start":
            current_run["status"] = "up_complete"
            current_run["up_complete"] = {
                "max": int(line[line.find("Max polls:") + len("Max polls:"):].strip().strip("\x1b[0m\n")),
            }
        elif "Max polls" in line and current_run and current_run["status"] == "up_complete":
            current_run["status"] = "down_start"
            current_run["down_start"] = int(line[line.find(
                "Max polls:") + len("Max polls:"):].strip().strip("\x1b[0m\n"))
        elif "Max polls" in line and current_run and current_run["status"] == "down_start":
            current_run["status"] = "down_complete"
            current_run["down_complete"] = {
                "max": int(line[line.find("Max polls:") + len("Max polls:"):].strip()),
            }
        elif "# polls used" in line and current_run and current_run["status"] == "down_complete":
            used_str, time_str = line[line.find(
                "# polls used:"):].strip().strip("\x1b[0m\n").split(",")
            current_run["down_complete"]["used"] = int(
                used_str[used_str.find("# polls used:") + len("# polls used:"):]) - 1
            ts = time_str[time_str.find("current_time:") + len("current_time:"):]
            current_run["down_complete"]["time"] = datetime.strptime(  # type: ignore
                ts.strip(), "%Y-%m-%d %H:%M:%S.%f")
            runs.append(current_run)
            current_run = None
        elif "# polls used" in line and current_run and current_run["status"] == "up_complete":
            used_str, time_str = line[line.find(
                "# polls used:"):].strip().strip("\x1b[0m\n").split(",")
            current_run["up_complete"]["used"] = int(
                used_str[used_str.find("# polls used:") + len("# polls used:"):]) - 1
            ts = time_str[time_str.find("current_time:") + len("current_time:"):]
            current_run["up_complete"]["time"] = datetime.strptime(  # type: ignore
                ts.strip(), "%Y-%m-%d %H:%M:%S.%f")

    return runs

def _parse_device(device_lines):
    runs = []
    current_run: dict[str, Any] | None = None
    for line in device_lines:
        line = line.strip()
        if current_run is None and ("Transition from 68 to 69" in line or "Transition open starts" in line):
            current_run = {"status": "up"}
        elif current_run is not None and current_run["status"] in ("up", "start") and "action finished at" in line:
            ts = line[line.find("action finished at") + len("action finished at"):].strip()
            current_run["up_time"] = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S.%f")
        elif current_run and ("Transition close starts" in line or "Transition from 69 to 68" in line):
            current_run["status"] = "down"
        elif "action finished at" in line and current_run and current_run["status"] == "down":
            ts = line[line.find("action finished at") + len("action finished at"):].strip()
            current_run["down_time"] = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S.%f")
            runs.append(current_run)
            current_run = None

    return runs


def _parse(ha_runs, device_runs, up=True):
    detection_times = []
    polls_list = []
    additional_polls_list = []
    max_polls_list = []
    ha_key = "up_complete" if up else "down_complete"
    dev_key = "up_time" if up else "down_time"
    for ha_run, device_run in zip(ha_runs, device_runs):
        detection_time = (ha_run[ha_key]["time"] -
                          device_run[dev_key]).total_seconds()
        polls = ha_run[ha_key]["used"]
        additional_polls = max(
            0, ha_run[ha_key]["used"] - ha_run[ha_key]["max"])
        max_polls = ha_run[ha_key]["max"]
        detection_times.append(detection_time)
        polls_list.append(polls)
        additional_polls_list.append(additional_polls)
        max_polls_list.append(max_polls)

    return {
        "detection_times": detection_times,
        "polls_list": polls_list,
        "additional_polls_list": additional_polls_list,
        "max_polls_list": max_polls_list,
    }


def _partition_ha_lines(ha_lines):
    door_lines = []
    thermostat_lines = []
    shade_lines = []

    current_section = None
    for line in ha_lines:
        if "cover.rpi_device_door" in line:
            current_section = "door"
        elif "climate.rpi_device_thermostat" in line:
            current_section = "thermostat"
        elif "cover.rpi_device_shade" in line:
            current_section = "shade"

        if current_section == "door":
            door_lines.append(line)
        elif current_section == "thermostat":
            thermostat_lines.append(line)
        elif current_section == "shade":
            shade_lines.append(line)

    return door_lines, thermostat_lines, shade_lines


def _parse_result(polling_strategy):

    # the action sequence:
    # 1. door.open/door.close
    # 2. thermostat.set_temperature
    # 3. shade.up/shade.down

    ha_log_file = f"logs/7_1_logs/home_assistant_{polling_strategy}.log"
    with open(ha_log_file, "r") as f:
        ha_lines = f.readlines()

    door_log_file = f"logs/7_1_logs/device_{polling_strategy}_logs/cover.rpi_device_door.log"
    with open(door_log_file, "r") as f:
        door_lines = f.readlines()
    thermostat_log_file = f"logs/7_1_logs/device_{polling_strategy}_logs/climate.rpi_device_thermostat.log"
    with open(thermostat_log_file, "r") as f:
        thermostat_lines = f.readlines()
    shade_log_file = f"logs/7_1_logs/device_{polling_strategy}_logs/cover.rpi_device_shade.log"
    with open(shade_log_file, "r") as f:
        shade_lines = f.readlines()

    # split the ha_lines into three parts
    door_ha_lines, thermostat_ha_lines, shade_ha_lines = _partition_ha_lines(
        ha_lines)

    door_ha_runs = _parse_ha(door_ha_lines)
    door_runs = _parse_device(door_lines)
    thermostat_ha_runs = _parse_ha(thermostat_ha_lines)
    thermostat_runs = _parse_device(thermostat_lines)
    shade_ha_runs = _parse_ha(shade_ha_lines)
    shade_runs = _parse_device(shade_lines)
    return {
        "door open": _parse(door_ha_runs, door_runs),
        "door close": _parse(door_ha_runs, door_runs, False),
        "thermostat": _parse(thermostat_ha_runs, thermostat_runs),
        "shade up": _parse(shade_ha_runs, shade_runs),
        "shade down": _parse(shade_ha_runs, shade_runs, False)
    }

def parse_result():
    results = {}
    for strategy in ["uniform", "rasc", "vopt"]:
        result = _parse_result(strategy)
        results[strategy] = result
    with open(f"results/7_1.json", "w") as f:
        json.dump(results, f, indent=4)
        
    fig, ax = plt.subplots(figsize=(8, 3))

    # Plot adaptive (blue dots)
    for label, stats in results["rasc"].items():
        avg_detection_time = sum(stats["detection_times"]) / len(stats["detection_times"])
        avg_polls = sum(stats["polls_list"]) / len(stats["polls_list"])
        x = avg_polls
        y = avg_detection_time
        ax.scatter(x, y, color="blue", s=40)
        ax.text(x * 1.01, y * 1.01, label, fontsize=14)

    # Plot periodic (red x)
    for label, stats in results["uniform"].items():
        avg_detection_time = sum(stats["detection_times"]) / len(stats["detection_times"])
        avg_polls = sum(stats["polls_list"]) / len(stats["polls_list"])
        x = avg_polls
        y = avg_detection_time
        ax.scatter(x, y, color="red", marker="x", s=60)
        ax.text(x * 1.01, y * 1.01, label, fontsize=14)

    # Log scales
    ax.set_xscale("log")
    ax.set_yscale("log")

    # Labels
    ax.set_xlabel("# Used Polls", fontsize=16)
    ax.set_ylabel("Detection Time (s)", fontsize=16)

    # Grid
    ax.grid(True, which="major", linestyle="-", linewidth=0.5)

    # # Legend
    ax.scatter([], [], color="blue", label="adaptive")
    ax.scatter([], [], color="red", marker="x", label="periodic")
    ax.legend(fontsize=14)

    fig.savefig("results/7_1.pdf", bbox_inches="tight")

parse_result()
