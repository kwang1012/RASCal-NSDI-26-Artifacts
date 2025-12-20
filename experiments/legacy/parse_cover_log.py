import json
from logging import fatal
from dateutil.parser import parse

def parse_ha(key = "cover"):
    with open(f"experiments/ha_{key}.log", "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    runs = []
    current_run = None
    for line in lines:
        if "DEBUG" not in line:
            continue
        if "RASC config" in line:
            continue
        if "Max polls" in line and current_run is None:
            current_run = {"status": "up_start", "up_start": int(line[line.find("Max polls:") + len("Max polls:"):].strip().strip("\x1b[0m\n"))}
        elif "Max polls" in line and current_run["status"] == "up_start":
            current_run["status"] = "up_complete"
            current_run["up_complete"] = {
                "max": int(line[line.find("Max polls:") + len("Max polls:"):].strip().strip("\x1b[0m\n")),
            }
        elif "Max polls" in line and current_run["status"] == "up_complete":
            current_run["status"] = "down_start"
            current_run["down_start"] = int(line[line.find("Max polls:") + len("Max polls:"):].strip().strip("\x1b[0m\n"))
        elif "Max polls" in line and current_run["status"] == "down_start":
            current_run["status"] = "down_complete"
            current_run["down_complete"] = {
                "max": int(line[line.find("Max polls:") + len("Max polls:"):].strip()),
            }
        elif "# polls used" in line and current_run["status"] == "down_complete":
            used_str, time_str = line[line.find("# polls used:"):].strip().strip("\x1b[0m\n").split(",")
            current_run["down_complete"]["used"] = int(used_str[used_str.find("# polls used:") + len("# polls used:"):]) - 1
            current_run["down_complete"]["time"] = parse(time_str[time_str.find("current_time:") + len("current_time:"):])
            runs.append(current_run)
            current_run = None
        elif "# polls used" in line and current_run["status"] == "up_complete":
            used_str, time_str = line[line.find("# polls used:"):].strip().strip("\x1b[0m\n").split(",")
            current_run["up_complete"]["used"] = int(used_str[used_str.find("# polls used:") + len("# polls used:"):]) - 1
            current_run["up_complete"]["time"] = parse(time_str[time_str.find("current_time:") + len("current_time:"):])

    return runs

def parse_device(key = "cover"):
    with open(f"experiments/{key}.log", "r", encoding="utf-8") as f:
        lines = f.readlines()

    runs = []
    current_run = None
    for line in lines:
        line = line.strip()
        if "Transition open starts" in line and current_run is None:
            current_run = {"status": "up"}
        elif current_run is not None and current_run["status"] == "up" and "action finished at" in line:
            current_run["up_time"] = parse(line[line.find("action finished at") + len("action finished at"):])
        elif "Transition close starts" in line:
            current_run["status"] = "down"
        elif "action finished at" in line and current_run["status"] == "down":
            current_run["down_time"] = parse(line[line.find("action finished at") + len("action finished at"):])
            runs.append(current_run)
            current_run = None

    return runs

def get_stats(ha_runs, device_runs, up=True):
    detection_times = []
    polls_list = []
    additional_polls_list = []
    max_polls_list = []
    ha_key = "up_complete" if up else "down_complete"
    dev_key = "up_time" if up else "down_time"
    for ha_run, device_run in zip(ha_runs, device_runs):
        detection_time = (ha_run[ha_key]["time"] - device_run[dev_key]).total_seconds()
        polls = ha_run[ha_key]["used"]
        additional_polls = max(0, ha_run[ha_key]["used"] - ha_run[ha_key]["max"])
        max_polls = ha_run[ha_key]["max"]
        # print(f"{detection_time}, {polls}, {additional_polls}, {max_polls}")
        detection_times.append(detection_time)
        polls_list.append(polls)
        additional_polls_list.append(additional_polls)
        max_polls_list.append(max_polls)

    print(detection_times)
    print(polls_list)
    print(additional_polls_list)
    print(max_polls_list)

def main():
    key = "shade_vopt"
    ha_runs = parse_ha(key)
    device_runs = parse_device(key)
    if len(ha_runs) != len(device_runs):
        fatal("Length does not equal!")
    
    get_stats(ha_runs, device_runs)
    get_stats(ha_runs, device_runs, False)

if __name__ == "__main__":
    main()