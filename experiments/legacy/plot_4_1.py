import json
import matplotlib.pyplot as plt
import numpy as np


def plot_result(ax, ax_r, actions, result, index):

    bar_max_colors = ["#ff7f0e70", "#3ca02c70", "#1f77b470"]
    bar_used_colors = ["#ff7f0e", "#3ca02c", "#1f77b4"]
    line_time_colors = ["tab:red", "black", "tab:blue"]
    legend_labels = [" (RASC)", " (Uniform)", " (VOPT)"]

    ind = np.arange(len(actions))
    # Width of a bar
    width = 0.3

    # Plotting
    bar_max = ax.bar(ind + (width + 0.05) * index, result["Max"], width, label="Max" + legend_labels[index], color=bar_max_colors[index])
    bar_used = ax.bar(ind + (width + 0.05) * index, result["Used"], width, label="Used" + legend_labels[index], color=bar_used_colors[index])

    ax.set_xticks(ind + width / 2 + 0.025, actions, fontsize=16)

    line_time = ax_r.plot(
        ind + width / 2 + 0.05,
        result["Detection time (s)"],
        label="Detection time\n" + legend_labels[index],
        marker="o",
        linewidth=2,
        color=line_time_colors[index]
    )

    lns = [bar_max]+[bar_used]+line_time
    labs = [l.get_label() for l in lns]
    return (lns, labs)


def main():
    with open("experiments/4_1_result.json", "r", encoding="utf-8") as f:
        result = json.load(f)
    actions = result["actions"]
    rasc_results = result["rasc"]
    uni_results = result["uniform"]

    # Figure size
    fig, ax = plt.subplots(figsize=(8,3.5))
    ax_r = ax.twinx()

    ax.set_ylabel("# Polls (avg.)", fontsize=20)
    ax.tick_params(axis="y", labelsize=18)

    color = "tab:blue"
    ax_r.set_ylabel("Detection time (s)", color=color, fontsize=20)
    ax_r.tick_params(axis="y", labelcolor=color, labelsize=18)

    lns1, labs1 = plot_result(ax, ax_r, actions, rasc_results, 0)
    lns2, labs2 = plot_result(ax, ax_r, actions, uni_results, 1)

    ax.legend(lns1 + lns2, labs1 + labs2, loc="best", fontsize=14, ncol=2)

    fig.savefig("results/4_1.pdf", bbox_inches="tight")


if __name__ == "__main__":
    main()
