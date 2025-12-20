import json
import matplotlib
from matplotlib.colors import LogNorm
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sn
from colour import Color


def main():
    with open("experiments/4_3_result.json", "r", encoding="utf-8") as f:
        result = json.load(f)["thermostat 68,68"]
        slos = result["slos"]
        worst_qs = result["worst_qs"]
        polls = result["polls"]

        red = Color("green")
        color_options = list(
            map(lambda color: color.hex, red.range_to(Color("red"), len(set(polls))))
        )

        plt.figure(figsize=(8, 8 * len(worst_qs) / (2 + len(slos))))
        cmap = matplotlib.colors.LinearSegmentedColormap.from_list("", color_options)
        data = []
        for i, _ in enumerate(worst_qs):
            data.append(polls[i * len(slos) : (i + 1) * len(slos) - 1])
        ax = sn.heatmap(
            data=data,
            cmap=cmap,
            annot=True,
            annot_kws={"fontsize": 12},
            square=True,
            yticklabels=worst_qs,
            xticklabels=slos[:-1],
            cbar=False,
            norm=LogNorm()
        )
        ax.invert_yaxis()
        ax.tick_params(axis="both", labelsize=12)
        ax.set_xlabel("SLO", fontsize=18)
        ax.set_ylabel("Worst detection time (s)", fontsize=18)
        
        plt.savefig("results/4_3.pdf", bbox_inches="tight")


if __name__ == "__main__":
    main()
