# use matplotlib to plot a figure

import json
import matplotlib.pyplot as plt
import numpy as np


def plot_overhead(data, dataset: str):

    fig, ax = plt.subplots(figsize=(8, 4))
    ax_r = ax.twinx()

    lns = []
    for label, (cpu, mem) in data.items():
        min_mem = min(mem)
        mem = [m - min_mem for m in mem]
        ln1 = ax.plot(cpu, label=label)
        ln2 = ax_r.plot(mem, color=ln1[0].get_color(
        ), linestyle="--", label=f"{label} (mem)")
        lns += ln1 + ln2

    min_length = min([len(cpu) for cpu, _ in data.values()])
    ax.set_ylim((0, 30))
    ax.set_xlim((0, min_length))
    ax_r.set_ylim((0, 30))
    ax_r.set_xlim((0, min_length))

    ax.set_ylabel("CPU Utilization (%)")
    ax_r.set_ylabel("Memory Usage (MB)")

    labs = [l.get_label() for l in lns]
    ax.legend(lns, labs)

    fig.savefig(f"results/overhead_{dataset}.png", bbox_inches="tight")


def parse_data(filename):
    with open(
        f"results/{filename}.json",
        "r",
        encoding="utf-8",
    ) as f:
        result = json.load(f)

    cpu = result["cpu"]
    mem = result["mem"]

    return cpu, mem


def main():

    reschedule_policy = "sjfw"
    estimation = "mean"
    datasets = [
        "all",
        "all_hybrid",
        "all_bursty"
    ]
    policy = "proactive"
    for dataset in datasets:
        data = {}
        data[f"rasc--{dataset}"] = parse_data(
            f"om_tl_{reschedule_policy}_{policy}_{estimation}_arrival_{dataset}")
        data[f"uniform--{dataset}"] = parse_data(
            f"om_static_tl_{reschedule_policy}_{policy}_{estimation}_arrival_{dataset}")
        data["w/o rasc"] = parse_data(f"om_arrival_{dataset}")
        plot_overhead(data, dataset)


if __name__ == "__main__":
    main()
