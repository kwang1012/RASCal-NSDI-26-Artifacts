import json
import math
import sys
import matplotlib.pyplot as plt
import numpy as np


def main():

    is_time = "time" in sys.argv

    reschedule_policy = "sjfw"

    estimations = ["mean", "p50", "p70", "p80", "p90", "p95", "p99"]
    datasets = ["all", "all_hybrid"]
    policies = ["proactive"]

    results = {}
    for dataset in datasets:
        results[dataset] = {}
        for policy in policies:
            results[dataset][policy] = {}
            for estimation in estimations:
                with open(
                    f"experiments/om_tl_{reschedule_policy}_{policy}_{estimation}_arrival_{dataset}.json",
                    "r",
                    encoding="utf-8",
                ) as f:
                    result = json.load(f)
                    results[dataset][policy][estimation] = {
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
                             for dataset_result in dataset_results["proactive"].values()]
        undertime_schedule = [dataset_result["reschedule"][1]
                              for dataset_result in dataset_results["proactive"].values()]
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
                    for result in dataset_result["proactive"].values()]
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

    postfix = "time" if is_time else "count"
    fig.savefig(
        f"results/{reschedule_policy}_reschedule_overhead_{postfix}.pdf")


if __name__ == "__main__":
    main()
