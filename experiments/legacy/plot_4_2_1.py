import json
import matplotlib.pyplot as plt
import numpy as np


def plot_result(ax, actions, result, index, label):

    ind = np.arange(len(actions))*1.2
    # Width of a bar
    width = 0.25

    # Plotting
    bar = ax.bar(ind + (width + 0.05) * index, result, width, label=label)

    ax.set_xticks(ind + width + 0.05, actions, fontsize=16)

    return [bar]


def main():
    with open("experiments/4_2_1_result.json", "r", encoding="utf-8") as f:
        result = json.load(f)
    actions = result["actions"]
    means = result["mean"]
    medians = result["median"]
    stds = result["std"]

    # Figure size
    fig, ax = plt.subplots(figsize=(8,3))

    ax.set_ylabel("# Data points", fontsize=20)
    ax.tick_params(axis="y", labelsize=16)

    bar1 = plot_result(ax, actions, means, 0, "mean")
    bar2 = plot_result(ax, actions, medians, 1, "median")
    bar3 = plot_result(ax, actions, stds, 2, "std")

    bars = bar1 + bar2 + bar3
    labs = [b.get_label() for b in bars]

    ax.legend(bars, labs, loc="best", fontsize=14)

    fig.savefig("results/4_2_1.pdf", bbox_inches="tight")


if __name__ == "__main__":
    main()
