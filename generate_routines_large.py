import json
import copy
import yaml
import csv

INPUT_FILE = "rasc_configs/automations.yaml"
OUTPUT_FILE = "rasc_configs/automations_large.yaml"


def suffix_entity(entity, n):
    if isinstance(entity, str):
        return f"{entity}{n}"
    if isinstance(entity, list):
        return [f"{e}{n}" for e in entity]
    return entity


def walk(obj, n):
    if isinstance(obj, dict):
        new = {}
        for k, v in obj.items():
            if k == "entity_id":
                new[k] = suffix_entity(v, n)
            else:
                new[k] = walk(v, n)
        return new
    elif isinstance(obj, list):
        return [walk(i, n) for i in obj]
    return obj


with open(INPUT_FILE) as f:
    automations = yaml.safe_load(f)

expanded = []

for auto in automations:
    expanded.append(auto)

    for n in [1, 2, 3]:
        clone = copy.deepcopy(auto)
        clone["id"] = f"{auto['id']}{n}"
        clone["alias"] = f"{auto.get('alias', 'Automation')} ({n})"
        clone = walk(clone, n)
        expanded.append(clone)

with open(OUTPUT_FILE, "w") as f:
    yaml.dump(expanded, f, sort_keys=False)

print(f"Generated {len(expanded)} automations")


INPUT_FILE = "rasc_configs/routine_setup.yaml"
OUTPUT_FILE = "rasc_configs/routine_setup_large.yaml"

with open(INPUT_FILE) as f:
    data = yaml.safe_load(f)

expanded = {}

for entity, actions in data.items():
    # original
    expanded[entity] = actions

    # duplicates
    for n in [1, 2, 3]:
        expanded[f"{entity}{n}"] = copy.deepcopy(actions)

with open(OUTPUT_FILE, "w") as f:
    yaml.dump(expanded, f, sort_keys=False)

print(f"Generated {len(expanded)} entity entries")

INPUT_FILE = "raspberry_pi/entity_ids_all.txt"
OUTPUT_FILE = "raspberry_pi/entity_ids_large.txt"

with open(INPUT_FILE) as f:
    lines = [line.strip() for line in f if line.strip()]

expanded = []

for entity in lines:
    # original
    expanded.append(entity)

    # duplicates
    for n in (1, 2, 3):
        expanded.append(f"{entity}{n}")

with open(OUTPUT_FILE, "w") as f:
    f.write("\n".join(expanded) + "\n")

print(f"Expanded {len(lines)} entities → {len(expanded)} total")


INPUT_FILE = "home-assistant-core/homeassistant/components/rasc/datasets/rasc_history_exp.json"
OUTPUT_FILE = "home-assistant-core/homeassistant/components/rasc/datasets/rasc_history_exp_large.json"

with open(INPUT_FILE) as f:
    data = json.load(f)

history = data["data"]["history"]
expanded_history = {}

for key, value in history.items():
    # split only on the first comma
    entity, rest = key.split(",", 1)

    # original
    expanded_history[key] = value

    # duplicates
    for n in (1, 2, 3):
        new_key = f"{entity}{n},{rest}"
        expanded_history[new_key] = copy.deepcopy(value)

data["data"]["history"] = expanded_history

with open(OUTPUT_FILE, "w") as f:
    json.dump(data, f, indent=2)

print(f"Expanded {len(history)} keys → {len(expanded_history)} keys")


INPUT_FILE = "home-assistant-core/homeassistant/components/rasc/datasets/arrival_scalability_50.csv"
OUTPUT_FILE = "home-assistant-core/homeassistant/components/rasc/datasets/arrival_scalability_100.csv"

with open(INPUT_FILE, newline="", encoding="utf-8") as f_in, \
        open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f_out:

    reader = csv.reader(f_in)
    writer = csv.writer(f_out)

    for ts, id_, alias in reader:
        writer.writerow([
            ts,
            id_,
            alias
        ])
        for i in range(1, 2):  # double
            writer.writerow([
                ts,
                f"{id_}{i}",
                f"{alias} ({i})"
            ])


INPUT_FILE = "home-assistant-core/homeassistant/components/rasc/datasets/arrival_scalability_50.csv"
OUTPUT_FILE = "home-assistant-core/homeassistant/components/rasc/datasets/arrival_scalability_200.csv"

with open(INPUT_FILE, newline="", encoding="utf-8") as f_in, \
        open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f_out:

    reader = csv.reader(f_in)
    writer = csv.writer(f_out)

    for ts, id_, alias in reader:
        writer.writerow([
            ts,
            id_,
            alias
        ])
        for i in range(1, 4):  # double
            writer.writerow([
                ts,
                f"{id_}{i}",
                f"{alias} ({i})"
            ])