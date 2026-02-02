from datetime import datetime
import json
from typing import Any
import matplotlib.pyplot as plt
import numpy as np


def _plot_failed_rate(result, ax, level, show_y_label=False, show_x_label=False):
    failed_rate = [r * 100 for r in result["failed_rate"]]
    polls = np.array(result["used_polls"])
    x = np.linspace(0, (len(polls) - 1) * 5, len(polls))
    ax.bar(x, failed_rate, color="black", label="FP rate")

    ax.set_yticks(np.arange(0, 81, 40))
    if show_y_label:
        ax.set_ylabel("False Positive\nRate (%)", fontsize=20)
    else:
        ax.tick_params(
            axis="y",  # changes apply to the x-axis
            which="both",  # both major and minor ticks are affected
            left=False,
            right=False,
            labelleft=False,
        )
    if show_x_label:
        ax.set_xlabel("Interruption length (%)", fontsize=22)
    ax.tick_params(axis="both", labelsize=18)

    ax.set_ylim((0, 80))
    # ax.legend(loc="upper left", fontsize=16)


def parse_simulated_result():

    levels = [50, 80, 90]

    # Figure size
    fig, axs = plt.subplots(1, 3, figsize=(24, 2))
    with open(f"results/7_3_simulated.json", "r", encoding="utf-8") as f:
        results = json.load(f)

    for i, level in enumerate(levels):
        _plot_failed_rate(
            results[f"interruption_{level}"], axs[i], level, i == 0, i == 1)

    fig.subplots_adjust(wspace=0.05, hspace=0)
    print("Saving figure to results/7_3_simulated.pdf")
    fig.savefig("results/7_3_simulated.pdf", bbox_inches="tight")


def _parse_ha(ha_lines):
    runs = []
    current_run: dict[str, Any] | None = None
    for line in ha_lines:
        if "DEBUG" not in line:
            continue
        if "RASC config" in line:
            continue
        if "Max polls" in line and current_run is None:
            current_run = {"status": "up_start", "up_start": int(line[line.find(
                "Max polls:") + len("Max polls:"):].strip().strip("\x1b[0m\n"))}
        elif "Max polls" in line and current_run and current_run["status"] == "up_start":
            current_run["status"] = "up_complete"
            current_run["up_complete"] = {
                "max": int(line[line.find("Max polls:") + len("Max polls:"):].strip().strip("\x1b[0m\n")),
            }
        elif "Max polls" in line and current_run and current_run["status"] == "up_complete":
            current_run["status"] = "down_start"
            current_run["down_start"] = int(line[line.find(
                "Max polls:") + len("Max polls:"):].strip().strip("\x1b[0m\n"))
        elif "Max polls" in line and current_run and current_run["status"] == "down_start":
            current_run["status"] = "down_complete"
            current_run["down_complete"] = {
                "max": int(line[line.find("Max polls:") + len("Max polls:"):].strip()),
            }
        elif "# polls used" in line and current_run and current_run["status"] == "down_complete":
            used_str, time_str = line[line.find(
                "# polls used:"):].strip().strip("\x1b[0m\n").split(",")
            current_run["down_complete"]["used"] = int(
                used_str[used_str.find("# polls used:") + len("# polls used:"):]) - 1
            ts = time_str[time_str.find(
                "current_time:") + len("current_time:"):]
            current_run["down_complete"]["time"] = datetime.strptime(  # type: ignore
                ts.strip(), "%Y-%m-%d %H:%M:%S.%f")
            runs.append(current_run)
            current_run = None
        elif "# polls used" in line and current_run and current_run["status"] == "up_complete":
            used_str, time_str = line[line.find(
                "# polls used:"):].strip().strip("\x1b[0m\n").split(",")
            current_run["up_complete"]["used"] = int(
                used_str[used_str.find("# polls used:") + len("# polls used:"):]) - 1
            ts = time_str[time_str.find(
                "current_time:") + len("current_time:"):]
            current_run["up_complete"]["time"] = datetime.strptime(  # type: ignore
                ts.strip(), "%Y-%m-%d %H:%M:%S.%f")

    return runs



def _parse_device(device_lines):
    runs = []
    current_run: dict[str, Any] | None = None
    for line in device_lines:
        line = line.strip()
        if "Transition from 68 to 69" in line and current_run is None:
            current_run = {}
        elif current_run is not None and "action finished at" in line:
            ts = line[line.find("action finished at") +
                      len("action finished at"):].strip()
            current_run["time"] = datetime.strptime(
                ts, "%Y-%m-%d %H:%M:%S.%f")
            runs.append(current_run)
            current_run = None

    return runs


def _parse(ha_runs, device_runs):
    # Manually split the runs
    # 50%: First 21 runs
    # 80%: Next 21 runs
    results = {}
    for i, level in enumerate([50, 80]):
        detection_times = []
        polls_list = []
        additional_polls_list = []
        max_polls_list = []
        ha_key = "up_complete"
        dev_key = "time"
        local_ha_runs = ha_runs[i * 21:(i + 1) * 21]
        local_device_runs = device_runs[i * 21:(i + 1) * 21]
        for ha_run, device_run in zip(local_ha_runs, local_device_runs):
            detection_time = (ha_run[ha_key]["time"] -
                            device_run[dev_key]).total_seconds()
            polls = ha_run[ha_key]["used"]
            additional_polls = max(
                0, ha_run[ha_key]["used"] - ha_run[ha_key]["max"])
            max_polls = ha_run[ha_key]["max"]
            detection_times.append(detection_time)
            polls_list.append(polls)
            additional_polls_list.append(additional_polls)
            max_polls_list.append(max_polls)

        results[f"interruption_{level}"] = {
            "detection_times": detection_times,
            "polls_list": polls_list,
            "additional_polls_list": additional_polls_list,
            "max_polls_list": max_polls_list,
        }

    return results

def _plot_detection_time(result, ax, ax_r):

    detection_times = result["detection_times"]
    polls = np.array(result["polls_list"])
    m_polls = np.array(result["max_polls_list"])

    x = np.linspace(0, len(polls) * 5, len(polls))

    ax.set_ylabel("# Polls", fontsize=20)
    ax.tick_params(axis="both", labelsize=16)
    ax.set_ylim((0, 25))

    color = "tab:blue"
    ax_r.set_ylabel("Detection time (s)", color=color, fontsize=20)
    ax_r.set_ylim((0, 100))
    ax_r.tick_params(axis="y", labelcolor=color, labelsize=16)

    l1 = ax_r.plot(x, detection_times, "o-", label="Detection time")
    l2 = ax.plot(x, polls, "o-", color="tab:red", label="Used")
    l3 = ax.plot(x, m_polls, "o-", color="tab:green", alpha=0.4, label="Max")
    ax.fill_between(
        x,
        polls,
        m_polls,
        where=(m_polls < polls),
        color="tab:red",
        alpha=0.3,
        interpolate=True,
    )
    return l1, l2, l3


def parse_deployed_result():
    ha_log_file = f"logs/7_3_logs/home_assistant.log"
    with open(ha_log_file, "r") as f:
        ha_lines = f.readlines()
    device_log_file = f"logs/7_3_logs/climate.rpi_device_thermostat.log"
    with open(device_log_file, "r") as f:
        device_lines = f.readlines()
    ha_runs = _parse_ha(ha_lines)
    device_runs = _parse_device(device_lines)
    results = _parse(ha_runs, device_runs)

    for key, result in results.items():
        # Figure size
        fig, ax = plt.subplots(figsize=(8, 4))
        ax_r = ax.twinx()

        l1, l2, l3 = _plot_detection_time(result, ax, ax_r)

        lns = l1 + l2 + l3
        labs = [l.get_label() for l in lns]

        ax.legend(lns, labs, loc="upper left", fontsize=14)

        print(f"Saving figure to results/7_3_{key}.pdf")
        fig.savefig(f"results/7_3_{key}.pdf", bbox_inches="tight")


def parse_result():
    parse_deployed_result()
    parse_simulated_result()


parse_result()
