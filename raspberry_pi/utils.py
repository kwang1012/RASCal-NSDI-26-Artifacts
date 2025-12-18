
import csv
from enum import StrEnum
import json
import math
import sys
import logging

class CustomFormatter(logging.Formatter):

    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    green = "\x1b[32;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    format = "[%(levelname)s] %(message)s"

    FORMATS = {
        logging.DEBUG: yellow + format + reset,
        logging.INFO: green + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)

def get_logger(name: str):
    logger = logging.getLogger(name)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(CustomFormatter())
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    return logger

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
            f"raspberry_pi/datasets/{name.value}.json",
            encoding="utf-8",
        ) as f:
            dataset = json.load(f)

    if action is None:
        return dataset

    if action not in dataset:
        print(
            "Action not found! Available actions:\n%s", "\n".join(list(dataset.keys()))
        )
    return dataset[action]


def _get_thermo_datasets():
    with open(
        "raspberry_pi/datasets/hvac-actions.csv", encoding="utf-8"
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