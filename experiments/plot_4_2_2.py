import json
import matplotlib.pyplot as plt
import numpy as np


def plot(ax, ax_r, result, label):

    times = result["time"][:19]
    polls = result["polls"][:19]

    ax.set_ylabel("# Polls (avg.)", fontsize=20)
    ax.set_xlabel("# Data points", fontsize=20)
    ax.tick_params(axis="both", labelsize=16)
    ax.set_ylim((0, 30))

    color = "tab:blue"
    ax_r.set_ylabel("Detection time (s)", color=color, fontsize=20)
    ax_r.tick_params(axis="y", labelcolor=color, labelsize=16)
    # ax_r.set_ylim((0, 30))

    width = 0.3

    x = np.arange(len(times))
    l1 = ax.bar(
        x + (width if label == "Uniform" else 0),
        polls,
        width,
        color="tab:green" if label == "Uniform" else "tab:orange",
        label=f"# Polls({label})",
    )
    l2 = ax_r.plot(
        x,
        times,
        "o-",
        color="black" if label == "Uniform" else "tab:red",
        label=f"Detection time({label})",
    )
    ax.set_xticks(x + width / 2, x, fontsize=16)

    lns = [l1] + l2
    return lns


def main():
    with open("experiments/4_2_2_result.json", "r", encoding="utf-8") as f:
        result = json.load(f)

    # Figure size
    fig, ax = plt.subplots(figsize=(8, 4))
    ax_r = ax.twinx()

    lns1 = plot(ax, ax_r, result["rasc"], "RASC")
    lns2 = plot(ax, ax_r, result["uniform"], "Uniform")

    lns = lns1 + lns2
    labs = [l.get_label() for l in lns]
    ax.legend(lns, labs, loc="best", fontsize=14)

    fig.savefig("results/4_2_2.pdf", bbox_inches="tight")


if __name__ == "__main__":
    main()
