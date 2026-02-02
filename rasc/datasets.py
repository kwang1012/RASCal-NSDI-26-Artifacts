""" Module for loading action datasets. """
import csv
from enum import StrEnum
import json
import math


class Device(StrEnum):
    """Dataset enum."""

    THERMOSTAT = "thermostat"
    DOOR = "door"
    COVER = "cover"
    ELEVATOR = "elevator"
    PROJECTOR = "projector"
    SHADE = "shade"
    LIGHT = "light"
    SWITCH = "switch"
    LOCK = "lock"
    FAN = "fan"

def load_dataset(name: Device, action: str | None = None):
    """Load dataset."""
    if name.value == "thermostat":
        dataset = _get_thermo_datasets()
    else:
        with open(
            f"datasets/{name.value}.json",
            encoding="utf-8",
        ) as f:
            dataset: dict[str, list[float]] = json.load(f)

    if action is None:
        return dataset

    if action not in dataset:
        print(
            "Action not found! Available actions:\n%s", "\n".join(list(dataset.keys()))
        )
        return None
    return dataset[action]


def _get_thermo_datasets() -> dict[str, list[float]]:
    with open(
        "datasets/hvac-actions.csv", encoding="utf-8"
    ) as f:
        reader = csv.reader(f)

        src_dst_map = {}

        for row in reader:
            start, target, length = row
            if start == "temp_start":
                continue
            key = f"{math.floor(float(start))},{math.floor(float(target))}"

            if key not in src_dst_map:
                src_dst_map[key] = []

            src_dst_map[key].append(float(length))

        datasets = {}
        for key, values in src_dst_map.items():
            src_dst_map[key] = list(filter(lambda value: value < 3600, values))
            if len(values) > 50:
                datasets[key] = src_dst_map[key]
    return datasets
