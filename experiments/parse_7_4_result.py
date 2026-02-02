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


def parse_overhead():
    reschedule_policy = "sjfw"
    estimation = "mean"
    datasets = [
        "all",
        "all_hybrid",
    ]
    policy = "proactive"
    results = {}
    for dataset in datasets:
        data = {}
        data["adaptive"] = parse_data(
            f"om_tl_{reschedule_policy}_{policy}_{estimation}_arrival_{dataset}")
        data["periodic"] = parse_data(
            f"om_static_tl_{reschedule_policy}_{policy}_{estimation}_arrival_{dataset}")
        data["none"] = parse_data(f"om_arrival_{dataset}")
    
    print(f"Saving overhead results to results/7_4_overhead.json")
    print("Visualizing overhead results...")
    with open("results/7_4_overhead.json", "w") as f:
        json.dump(results, f, indent=4)
        
    # Column widths
    col_widths = [16, 16, 8, 6, 6, 12, 6, 6]

    # Header
    headers = ["Dataset", "Strategy",
               "CPU (%)", "q50", "q99", "Memory (MB)", "q50", "q99"]
    header_line = "".join(f"{h:<{w}}" for h, w in zip(headers, col_widths))
    print(header_line)
    print("-" * sum(col_widths))

    # Rows
    for dataset, strategies in results.items():
        first = True
        for strat, metrics in strategies.items():
            row = [
                dataset if first else "",
                strat,
                f"{metrics['cpu_mean']:.2f}",
                f"{metrics['cpu_p50']:.2f}",
                f"{metrics['cpu_p99']:.2f}",
                f"{metrics['mem_mean']:.2f}",
                f"{metrics['mem_p50']:.2f}",
                f"{metrics['mem_p99']:.2f}"
            ]
            print("".join(f"{c:<{w}}" for c, w in zip(row, col_widths)))
            first = False


def parse_reschedule_overhead():

    is_time = True

    estimations = ["mean", "p50", "p70", "p80", "p90", "p95", "p99"]
    datasets = ["all", "all_hybrid"]

    results = {}
    for dataset in datasets:
        results[dataset] = {}
        for estimation in estimations:
            with open(
                f"home-assistant-core/results/om_tl_sjfw_proactive_{estimation}_arrival_{dataset}.json",
                "r",
                encoding="utf-8",
            ) as f:
                result = json.load(f)
                results[dataset][estimation] = {
                    "reschedule": (
                        len([r for r in result["reschedule"] if r[2] > 0]),
                        len([r for r in result["reschedule"] if r[2] < 0]),
                    )
                }

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.set_ylabel(
        "Total reschedule time" if is_time else "Reschedule count", fontsize=20)
    ax.set_xlabel("Action length estimation percentile", fontsize=20)
    ax.tick_params(axis="both", labelsize=16)

    max_count = 0
    x = np.arange(len(estimations))
    width = 0.45
    for i, (dataset, dataset_results) in enumerate(results.items()):
        overtime_schedule = [dataset_result["reschedule"][0]
                             for dataset_result in dataset_results.values()]
        undertime_schedule = [dataset_result["reschedule"][1]
                              for dataset_result in dataset_results.values()]
        b_under = ax.bar(
            x + i * width, undertime_schedule, width=width, alpha=0.7,
            label=f"{dataset} (under)",
        )
        ax.bar(
            x + i * width,
            overtime_schedule,
            bottom=undertime_schedule,
            color=b_under.patches[0].get_facecolor(),
            alpha=1,
            width=width,
            label=f"{dataset} (over)",
        )
        max_count = max(
            max_count, max(
                o + u for o, u in zip(overtime_schedule, undertime_schedule))
        )

    flat_results = [result for dataset_result in results.values()
                    for result in dataset_result.values()]
    for i, bar in enumerate(ax.patches):
        item = flat_results[(0 if i < 14 else 7) + i % 7]
        overtime = item["reschedule"][0]
        undertime = item["reschedule"][1]
        percentage = round(100 * (overtime if math.floor(i/7) %
                           2 == 1 else undertime) / (undertime + overtime), 1)
        ax.text(bar.get_x()+bar.get_width()/2, bar.get_y() +
                bar.get_height()/2,  f"{percentage}\n(%)", ha='center', va='center', fontsize=15)

    ax.set_xticks(
        x + width/2, [estimation for estimation in estimations], fontsize=18)
    ax.legend(fontsize=18)
    ax.set_ylim(0, max_count * 1.6)

    print("Saving figure to results/7_4_reschedule_overhead.pdf")
    fig.savefig(
        f"results/7_4_reschedule_overhead.pdf")


name_map = {
    "jit": "JiT",
    "tl_rv": "DAG-TL+RV",
    "tl_sjfw": "DAG-TL+STF",
    "fcfs": "FCFS",
    "fcfs_post": "FCFS-Post",
}


def parse_metric():

    schedulers = ["fcfs", "fcfs_post", "jit", "tl_rv", "tl_sjfw"]
    scheduler_labels = [name_map[s] for s in schedulers]
    parsed = {}
    for scheduler in schedulers:
        results_dir = f"home-assistant-core/results/arrival_all_{scheduler}"
        if not os.path.exists(f"{results_dir}/schedule_metrics.yaml"):
            parsed[scheduler] = {
                "Wait Time": {"avg": 0, "p95": 0},
                "Schedule Length": {"avg": 0},
                "Idle Time": {"avg": 0, "p95": 0},
                "Latency": {"avg": 0, "p95": 0},
                "Parallelism": {"avg": 0},
            }
            continue
        with open(f"{results_dir}/schedule_metrics.yaml") as file:
            schedule_metrics = yaml.load(file, Loader=yaml.FullLoader)

        parsed[scheduler] = {
            "Wait Time": {
                "avg": schedule_metrics["Average Wait Time"],
                "p95": schedule_metrics["95th Percentile Wait Time"],
            },
            "Schedule Length": {
                "avg": schedule_metrics["Schedule Length"],
            },
            "Idle Time": {
                "avg": schedule_metrics["Average Idle Time"],
                "p95": schedule_metrics["95th Percentile Idle Time"],
            },
            "Latency": {
                "avg": schedule_metrics["Average Latency"],
                "p95": schedule_metrics["95th Percentile Latency"],
            },
            "Parallelism": {
                # skip 5th percentile
                "avg": schedule_metrics["Average Parallelism"],
            },
        }

    metrics = ["Wait Time", "Schedule Length",
               "Idle Time", "Latency", "Parallelism"]
    data = {m: {"avg": [], "p95": []} for m in metrics}

    for sched in schedulers:
        for m in metrics:
            data[m]["avg"].append(parsed[sched][m]["avg"])
            if "p95" in parsed[sched][m]:
                data[m]["p95"].append(parsed[sched][m].get("p95"))

    for metric in metrics:
        x = np.arange(len(schedulers))
        double = len(data[metric]["p95"]) == len(schedulers)
        if double:
            width = 0.4
        else:
            width = 0.8

        fig, ax = plt.subplots(
            figsize=(8 if double else 4.5, 3 if double else 2.7))
        ax.bar(x, data[metric]["avg"], width, label="Average")

        if double:
            ax.bar(x + width, data[metric]["p95"],
                   width, label="95th Percentile")
            ax.set_xticks(x + width / 2)
            ax.set_xticklabels(scheduler_labels)
        else:
            ax.set_xticks(x)
            ax.set_xticklabels(scheduler_labels)

        if metric == "Schedule Length":
            label = "Schedule\nLength"
        else:
            label = metric
        ax.set_ylabel(f"{label} (s)", fontsize=18)
        ylim = max(data[metric]["avg"])
        if double:
            ylim = max(ylim, max(data[metric]["p95"]))
        ax.set_ylim((0, ylim*1.5))
        ax.legend(fontsize=14)
        ax.set_yticks(ax.get_yticks(), [round(tick) if tick.is_integer(
        ) else tick for tick in ax.get_yticks()], fontsize=16)
        X = np.arange(len(scheduler_labels))
        ax.set_xticks(X + (width/2 if double else 0),
                      scheduler_labels, fontsize=16, rotation=20)
        print(f"Saving figure to results/7_4_{metric.replace(' ', '_')}.pdf")
        fig.savefig(
            f"results/7_4_{metric.replace(' ', '_')}.pdf", bbox_inches="tight")


def parse_result():
    parse_overhead()
    # parse_reschedule_overhead()
    # parse_metric()


parse_result()
