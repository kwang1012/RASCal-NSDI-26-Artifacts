import os
import json
import math
import sys
import matplotlib.pyplot as plt
import numpy as np
import yaml


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
        f"home-assistant-core/results/{filename}.json",
        "r",
        encoding="utf-8",
    ) as f:
        result = json.load(f)

    cpu = result["cpu"]
    mem = result["mem"]

    return {
        "cpu_mean": np.mean(cpu),
        "cpu_p50": np.percentile(cpu, 50),
        "cpu_p99": np.percentile(cpu, 99),
        "mem_mean": np.mean(mem),
        "mem_p50": np.percentile(mem, 50),
        "mem_p99": np.percentile(mem, 99),
    }


def parse_result():
    reschedule_policy = "sjfw"
    estimation = "mean"
    datasets = [
        "scalability_10",
        "scalability_50",
        "scalability_100",
        "scalability_200",
    ]
    policy = "proactive"
    results = {}
    for dataset in datasets:
        data = {}
        data["adaptive"] = parse_data(
            f"om_tl_{reschedule_policy}_{policy}_{estimation}_arrival_{dataset}")
        data["none"] = parse_data(f"om_arrival_{dataset}")
        results[dataset] = data
    print(results)

parse_result()
