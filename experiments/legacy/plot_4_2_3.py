from functools import cmp_to_key
import json
import matplotlib.pyplot as plt
import numpy as np

def plot_trial(ax, data):

    data_points = []
    for d in data:
        start = d["start"]
        start_trials = d["trials"]
        to_list = d["to"]
        for to in to_list:
            target = to["target"]
            distance = to["distance"]
            trials = to["trials"]
            data_points.append((f"{start},{target}", distance, trials, start_trials))

    data_points = sorted(data_points, key=cmp_to_key(lambda d1, d2: d1[1] - d2[1]))

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


def plot_diff(ax, result):

    ax.set_ylabel("Mean", fontsize=20)
    ax.tick_params(axis="both", labelsize=16)

    distances = [r["distance"] for r in result]
    old_means = [r["old_mean"] for r in result]
    old_stds = [r["old_std"] for r in result]
    new_means = [r["new_mean"] for r in result]
    new_stds = [r["new_std"] for r in result]
    # means_ratio = [new_mean - old_mean for old_mean, new_mean in zip(old_means, new_means)]
    # stds = np.std(means_ratio)

    ax.errorbar(
        distances,
        old_means,
        old_stds,
        linestyle="None",
        marker="o",
        mfc="white",
        mec="black",
        lw=1,
        capsize=8,
        label="Original",
    )
    ax.errorbar(
        distances,
        new_means,
        new_stds,
        linestyle="None",
        marker="o",
        mfc="white",
        mec="black",
        lw=1,
        capsize=8,
        label="Shift",
    )
    ax.yaxis.set_label_position("right")
    ax.yaxis.tick_right()

    ax.legend(loc="upper left", fontsize=14)


def main():
    with open("experiments/4_2_3_result.json", "r", encoding="utf-8") as f:
        data = json.load(f)["data"]

    with open("experiments/4_2_4_result.json", "r", encoding="utf-8") as f:
        result = json.load(f)

    # Figure size
    fig, axs = plt.subplots(1, 1, figsize=(8, 3), sharex=True)
    fig.tight_layout(w_pad=0)
    fig.text(
        0.5, -0.04, "Wasserstein distance", fontsize=20, ha="center", va="center"
    )

    plot_trial(axs, data)
    # plot_diff(axs[1], result)

    fig.savefig("results/4_2_3.pdf", bbox_inches="tight")


if __name__ == "__main__":
    main()
