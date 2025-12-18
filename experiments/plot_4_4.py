import json
import matplotlib.pyplot as plt
import numpy as np

def plot_4_4(result, ax, ax_r):
    
    detection_times = result["detection_time"]
    polls = np.array(result["polls"])
    m_polls = np.array(result["m_polls"])

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

def main():

    key = "50_fixed"

    with open("experiments/4_4_result.json", "r", encoding="utf-8") as f:
        result = json.load(f)[key]
    # with open("experiments/4_4_result.json", "r", encoding="utf-8") as f:
    #     result_uniform = json.load(f)[f"{key}_uniform"]

    # Figure size
    fig, ax = plt.subplots(figsize=(8, 4))
    ax_r = ax.twinx()

    l1, l2, l3 = plot_4_4(result, ax, ax_r)
    # l4, l5, l6 = plot_4_4(result_uniform, ax, ax_r)

    lns = l1 + l2 + l3
    labs = [l.get_label() for l in lns]

    ax.legend(lns, labs, loc="upper left", fontsize=14)

    fig.savefig(f"results/4_4_{key}.pdf", bbox_inches="tight")


if __name__ == "__main__":
    main()