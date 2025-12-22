import json
from typing import Any
from dateutil.parser import parse


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
            current_run["down_complete"]["time"] = parse(  # type: ignore
                time_str[time_str.find("current_time:") + len("current_time:"):])
            runs.append(current_run)
            current_run = None
        elif "# polls used" in line and current_run and current_run["status"] == "up_complete":
            used_str, time_str = line[line.find(
                "# polls used:"):].strip().strip("\x1b[0m\n").split(",")
            current_run["up_complete"]["used"] = int(
                used_str[used_str.find("# polls used:") + len("# polls used:"):]) - 1
            current_run["up_complete"]["time"] = parse(  # type: ignore
                time_str[time_str.find("current_time:") + len("current_time:"):])

    return runs


def _parse_device(device_lines):
    runs = []
    current_run: dict[str, Any] | None = None
    for line in device_lines:
        line = line.strip()
        if "Transition from 68 to 69" in line and current_run is None:
            current_run = {}
        elif "Transition open starts" in line and current_run is None:
            current_run = {"status": "up"}
        elif current_run is not None and current_run["status"] == "up" and "action finished at" in line:
            current_run["up_time"] = parse(
                line[line.find("action finished at") + len("action finished at"):])
        elif "Transition close starts" in line and current_run:
            current_run["status"] = "down"
        elif "action finished at" in line and current_run and current_run["status"] == "down":
            current_run["down_time"] = parse(
                line[line.find("action finished at") + len("action finished at"):])
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
        # print(f"{detection_time}, {polls}, {additional_polls}, {max_polls}")
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
        if "door.rpi_device_door" in line:
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


def parse_result(polling_strategy):

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
        "door.open": _parse(door_ha_runs, door_runs),
        "door.close": _parse(door_ha_runs, door_runs, False),
        "thermostat.set_temperature": _parse(thermostat_ha_runs, thermostat_runs),
        "shade.up": _parse(shade_ha_runs, shade_runs),
        "shade.down": _parse(shade_ha_runs, shade_runs, False)
    }


results = {}
for strategy in ["uniform", "rasc", "vopt"]:
    result = parse_result(strategy)
    results[strategy] = result
with open(f"results/7_1_result.json", "w") as f:
    json.dump(results, f, indent=4)
