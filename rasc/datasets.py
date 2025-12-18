""" Module for loading action datasets. """
import csv
import math


def get_thermo_datasets():
    """ Loads HVAC action datasets from CSV file. """
    with open("datasets/hvac-actions.csv", 'r', encoding='utf-8') as f:
        reader = csv.reader(f)

        src_dst_map = {}

        for row in reader:
            start, target, length = row
            if start == 'temp_start':
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
