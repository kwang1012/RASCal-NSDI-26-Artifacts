import json
import matplotlib.pyplot as plt
import numpy as np
from functools import cmp_to_key

def _plot_result(ax, actions, result, index, label):

    ind = np.arange(len(actions))*1.2
    # Width of a bar
    width = 0.25

    # Plotting
    bar = ax.bar(ind + (width + 0.05) * index, result, width, label=label)

    ax.set_xticks(ind + width + 0.05, actions, fontsize=16)

    return [bar]


def _parse_7_2_training():

    actions = [
        "thermo.\n68,68",
        "thermo.\n68,70",
        "door\nclose",
        "elevator\n1 F",
        "shade\nup",
        "projector\nscreen up"
    ]
    with open("results/7_2_training.json", "r", encoding="utf-8") as f:
        results = json.load(f)
    means = [result["mean"] for result in results.values()]
    medians = [result["median"] for result in results.values()]
    stds = [result["std"] for result in results.values()]

    # Figure size
    fig, ax = plt.subplots(figsize=(8, 3))

    ax.set_ylabel("# Data points", fontsize=20)
    ax.tick_params(axis="y", labelsize=16)

    bar1 = _plot_result(ax, actions, means, 0, "mean")
    bar2 = _plot_result(ax, actions, medians, 1, "median")
    bar3 = _plot_result(ax, actions, stds, 2, "std")

    bars = bar1 + bar2 + bar3
    labs = [b.get_label() for b in bars]

    ax.legend(bars, labs, loc="best", fontsize=14)

    fig.savefig("results/7_2_training.pdf", bbox_inches="tight")


def _plot_trial(ax, data):

    data_points = []
    for d in data:
        start = d["start"]
        start_trials = d["trials"]
        to_list = d["to"]
        for to in to_list:
            target = to["target"]
            distance = to["distance"]
            trials = to["trials"]
            data_points.append(
                (f"{start},{target}", distance, trials, start_trials))

    data_points = sorted(data_points, key=cmp_to_key(
        lambda d1, d2: d1[1] - d2[1]))

    x = [data[1] for data in data_points]
    y1 = [data[2] for data in data_points]
    y2 = [data[3] for data in data_points]

    # coef = np.polyfit(x, y1, 1)
    # poly1d_fn = np.poly1d(coef)
    # y_pred_1d = poly1d_fn(x)
    # mse_1d = ((y_pred_1d - y1)**2).mean()

    coef = np.polyfit(x, y1, 2)
    poly2d_fn = np.poly1d(coef)
    # y_pred_2d = poly2d_fn(x)
    # mse_2d = ((y_pred_2d - y1)**2).mean()

    ax.set_ylabel("# Data points", fontsize=20)
    ax.tick_params(axis="both", labelsize=16)
    # ax.set_ylim((0, 30))

    ax.plot(x, poly2d_fn(x), "--", color="tab:red")
    l1 = ax.scatter(x, y2, label="Original", s=30)
    l2 = ax.scatter(x, y1, label="Shift", s=30)

    lns = [l1] + [l2]
    labs = [l.get_label() for l in lns]

    ax.legend(lns, labs, loc="best", fontsize=14)

def _parse_7_2_shifting():
    with open("results/7_2_shifting.json", "r", encoding="utf-8") as f:
        data = json.load(f)["data"]

    # Figure size
    fig, axs = plt.subplots(1, 1, figsize=(8, 3), sharex=True)
    fig.tight_layout(w_pad=0)
    fig.text(
        0.5, -0.04, "Wasserstein distance", fontsize=20, ha="center", va="center"
    )

    _plot_trial(axs, data)

    fig.savefig("results/7_2_shifting.pdf", bbox_inches="tight")


def parse_result():
    _parse_7_2_training()
    _parse_7_2_shifting()


parse_result()
