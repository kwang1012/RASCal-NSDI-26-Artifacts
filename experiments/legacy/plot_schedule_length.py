from functools import cmp_to_key
import os

import matplotlib.pyplot as plt
import numpy as np
import yaml


def main():

    results = [f for f in os.listdir("results") if not os.path.isfile(os.path.join("results", f))]
    results = sorted(results)

    schedule_length = {}
    dataset = "arrival_all.csv"

    for result in results:
        with open(f"results/{result}/rasc_config.yaml") as file:
            config = yaml.load(file, Loader=yaml.FullLoader)

        if not os.path.exists(f"results/{result}/schedule_metrics.yaml"):
            continue

        with open(f"results/{result}/schedule_metrics.yaml") as file:
            schedule_metrics = yaml.load(file, Loader=yaml.FullLoader)

        if config["routine_arrival_filename"] != dataset:
            continue

        if config["scheduling_policy"] != "tl":
            continue

        if config["rescheduling_policy"] != "sjfw":
            continue

        estimation = config["action_length_estimation"]

        schedule_length[estimation] = schedule_metrics["Schedule Length"]

    headers = schedule_length.keys()
    headers = sorted(headers, key=cmp_to_key(lambda x, y: x < y if x == "mean" else 1))
    data = []
    for header in headers:
        data.append(schedule_length[header])
    ylim = max(data) * 1.5

    fig, ax = plt.subplots()

    X = np.arange(len(headers))
    width = 0.6
    plt.bar(X, data, width=width, label="Schedule Length")

    ax.set_ylabel("Schedule Length (s)", fontsize=18)
    ax.set_ylim((0, ylim*1.5))
    ax.legend(fontsize=14)
    ax.set_yticks(ax.get_yticks(), [round(tick) if tick.is_integer() else tick for tick in ax.get_yticks()], fontsize=16)
    ax.set_xticks(X, headers, fontsize=16)
    fig.savefig("schedule_length.pdf", bbox_inches="tight")

if __name__ == "__main__":
    main()
