import json
import matplotlib.pyplot as plt
import numpy as np


def plot_4_4(result, ax, level, show_y_label=False):

    polls = np.array(result["used_polls"])
    m_polls = np.array(result["max_polls"])

    if show_y_label:
        ax.set_ylabel("# Polls", fontsize=22)
        ax.tick_params(axis="y", labelsize=18)
        ax.tick_params(
            axis="x",  # changes apply to the x-axis
            which="both",  # both major and minor ticks are affected
            bottom=False,  # ticks along the bottom edge are off
            top=False,  # ticks along the top edge are off
            labelbottom=False,
        )
    else:
        ax.tick_params(
            axis="both",  # changes apply to the x-axis
            which="both",  # both major and minor ticks are affected
            bottom=False,  # ticks along the bottom edge are off
            top=False,
            left=False,
            right=False,
            labelbottom=False,
            labelleft=False,
        )
    ax.set_ylim((5, 25))

    x = np.linspace(0, (len(polls) - 1) * 5, len(polls))

    ax.plot(x, polls, "o-", color="tab:red", label="Used")
    ax.plot(x, m_polls, "o-", color="tab:green", label="Max")
    ax.vlines(100 - level, 0, 1, "red", "dashed")
    ax.fill_between(
        x,
        polls,
        m_polls,
        where=(m_polls < polls),
        color="tab:red",
        alpha=0.3,
        interpolate=True,
    )

    ax.legend(ncol=2, loc="upper left", fontsize=16)


def plot_detection_time(result, ax, level, show_y_label=False):
    detection_times = result["detection_time"]
    polls = np.array(result["used_polls"])
    x = np.linspace(0, (len(polls) - 1) * 5, len(polls))
    ax.plot(x, detection_times, "o-", label="Detection time")
    ax.set_ylim((10, 30))

    if show_y_label:
        ax.set_ylabel("Time", fontsize=22)
        ax.tick_params(axis="y", labelsize=18)
        ax.tick_params(
            axis="x",  # changes apply to the x-axis
            which="both",  # both major and minor ticks are affected
            bottom=False,  # ticks along the bottom edge are off
            top=False,  # ticks along the top edge are off
            labelbottom=False,
        )
    else:
        ax.tick_params(
            axis="both",  # changes apply to the x-axis
            which="both",  # both major and minor ticks are affected
            bottom=False,  # ticks along the bottom edge are off
            top=False,
            left=False,
            right=False,
            labelbottom=False,
            labelleft=False,
        )

    ax.set_ylim((0, None))
    ax.legend(loc="upper left", fontsize=16)


def plot_failed_rate(result, ax, level, show_y_label=False, show_x_label=False):
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
        # plot_4_4(results[f"interruption_{level}"], axs[0][i], level, i == 0)
        # plot_detection_time(results[f"interruption_{level}"], axs[1][i], level, i == 0)
        plot_failed_rate(results[f"interruption_{level}"], axs[i], level, i == 0, i == 1)

    fig.subplots_adjust(wspace=0.05, hspace=0)
    fig.savefig("results/7_3_simulated.pdf", bbox_inches="tight")

def parse_deployed_result():
    pass

def parse_result():
    parse_deployed_result()
    parse_simulated_result()

parse_result()
