import json
import matplotlib.pyplot as plt
import numpy as np


def main():

    with open("experiments/4_2_4_result.json", "r", encoding="utf-8") as f:
        result = json.load(f)

    # Figure size
    fig, ax = plt.subplots(figsize=(8, 4))

    ax.set_ylabel("Mean", fontsize=20)
    ax.set_xlabel("Wasserstein distance", fontsize=20)
    ax.tick_params(axis="both", labelsize=18)

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
        label="Old dataset",
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
        label="New dataset",
    )

    ax.legend(loc="upper left", fontsize=18)

    fig.savefig(f"results/4_2_4.pdf", bbox_inches="tight")


if __name__ == "__main__":
    main()
