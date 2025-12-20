import os

import matplotlib.pyplot as plt
import numpy as np
import yaml

name_map = {
    "jit": "JiT",
    "rv": "RV",
    "sjfw": "STF",
    "fcfs": "FCFS",
    "fcfs_post": "FCFS-Post",
    "tl": "tl",
}

def main():

    results = [f for f in os.listdir("results") if not os.path.isfile(os.path.join("results", f))]
    results = sorted(results)

    schedule_metrics_dict = {
        "FCFS": None,
        "FCFS-Post": None,
        "JiT": None,
        "DAG-TL+RV": None,
        "DAG-TL+STF": None,
    }
    dataset = "arrival_all.csv"

    key_filters = ["Wait Time", "Schedule Length", "Idle Time", "Latency", "Parallelism"]
    for key_filter in key_filters:
        for result in results:
            with open(f"results/{result}/rasc_config.yaml") as file:
                config = yaml.load(file, Loader=yaml.FullLoader)

            if not os.path.exists(f"results/{result}/schedule_metrics.yaml"):
                continue

            with open(f"results/{result}/schedule_metrics.yaml") as file:
                schedule_metrics = yaml.load(file, Loader=yaml.FullLoader)

            if config["routine_arrival_filename"] != dataset:
                continue

            policy = name_map[config["scheduling_policy"]]

            if policy == "tl":
                policy = "DAG-TL+" + name_map[config["rescheduling_policy"]]

            if policy.startswith("tl"):
                if config["action_length_estimation"] == "p90":
                    schedule_metrics_dict[policy] = schedule_metrics
            else:

            # if policy not in schedule_metrics_dict or schedule_metrics_dict[policy]["Schedule Length"] > schedule_metrics["Schedule Length"]:
                schedule_metrics_dict[policy] = schedule_metrics
                # print(policy, config["action_length_estimation"])

        headers = []
        data = {
            key: []
            for key in schedule_metrics_dict["FCFS"] if key_filter in key and key != "5th Percentile Parallelism"
        }
        ylim = 0
        for policy, schedule_metrics in schedule_metrics_dict.items():
            headers.append(policy)
            for key, metric in schedule_metrics.items():
                if key_filter not in key or key == "5th Percentile Parallelism":
                    continue
                data[key].append(metric)
                ylim = max(ylim, metric)

        fig, ax = plt.subplots(figsize=(8 if len(data) == 2 else 4.5, 3 if len(data) == 2 else 2.7))

        X = np.arange(len(headers))
        width = 0.8 / len(data)
        for i, (key, values) in enumerate(data.items()):
            plt.bar(X + width * i, values, width=width, label=key)

        if key_filter == "Schedule Length":
            label = "Schedule\nLength"
        else:
            label = key_filter
        ax.set_ylabel(f"{label} (s)", fontsize=18)
        ax.set_ylim((0, ylim*1.5))
        ax.legend(fontsize=14)
        ax.set_yticks(ax.get_yticks(), [round(tick) if tick.is_integer() else tick for tick in ax.get_yticks()], fontsize=16)
        ax.set_xticks(X + (width/2 if len(data) > 1 else 0), headers, fontsize=16, rotation=20)
        fig.savefig(f"schedule_metric_{key_filter}.pdf", bbox_inches="tight")

if __name__ == "__main__":
    main()
