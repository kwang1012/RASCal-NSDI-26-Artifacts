from logging import fatal
from dateutil.parser import parse

def parse_ha(key = "50"):
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
            current_run = {"status": "up_start", "start": int(line[line.find("Max polls:") + len("Max polls:"):].strip().strip("\x1b[0m\n"))}
        elif "Max polls" in line and current_run["status"] == "up_start":
            current_run["status"] = "up_complete"
            current_run["complete"] = {
                "max": int(line[line.find("Max polls:") + len("Max polls:"):].strip().strip("\x1b[0m\n")),
            }
        elif "Max polls" in line and current_run["status"] == "up_complete":
            current_run["status"] = "down_start"
        elif "Max polls" in line and current_run["status"] == "down_start":
            current_run["status"] = "down_complete"
        elif "# polls used" in line and current_run["status"] == "down_complete":
            runs.append(current_run)
            current_run = None
        elif "# polls used" in line and current_run["status"] == "up_complete":
            used_str, time_str = line[line.find("# polls used:"):].strip().strip("\x1b[0m\n").split(",")
            current_run["complete"]["used"] = int(used_str[used_str.find("# polls used:") + len("# polls used:"):])
            current_run["complete"]["time"] = parse(time_str[time_str.find("current_time:") + len("current_time:"):])

    return runs

def parse_device(key = "50"):
    with open(f"experiments/thermostat_{key}.log", "r", encoding="utf-8") as f:
        lines = f.readlines()

    runs = []
    current_run = None
    for line in lines:
        line = line.strip()
        if "Transition from 68 to 69" in line and current_run is None:
            current_run = {}
        elif current_run is not None and "action finished at" in line:
            current_run["time"] = parse(line[line.find("action finished at") + len("action finished at"):])
            runs.append(current_run)
            current_run = None
        else:
            continue

    return runs

def main():
    key = "tmp"
    ha_runs = parse_ha(key)
    device_runs = parse_device(key)
    if len(ha_runs) != len(device_runs):
        fatal("Length does not equal!")
    
    detection_times = []
    polls_list = []
    additional_polls_list = []
    max_polls_list = []
    for ha_run, device_run in zip(ha_runs, device_runs):
        detection_time = (ha_run["complete"]["time"] - device_run["time"]).total_seconds()
        polls = ha_run["complete"]["used"]
        additional_polls = max(0, ha_run["complete"]["used"] - ha_run["complete"]["max"])
        max_polls = ha_run["complete"]["max"]
        print(f"{detection_time}, {polls}, {additional_polls}, {max_polls}")
        detection_times.append(detection_time)
        polls_list.append(polls)
        additional_polls_list.append(additional_polls)
        max_polls_list.append(max_polls)

    print(detection_times)
    print(polls_list)
    print(additional_polls_list)
    print(max_polls_list)

if __name__ == "__main__":
    main()