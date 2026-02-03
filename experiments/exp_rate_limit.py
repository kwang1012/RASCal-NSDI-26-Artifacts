import os
import json
from matplotlib.cm import ScalarMappable
from matplotlib.colors import Normalize
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import seaborn as sn
from colour import Color
from math import ceil
from matplotlib.gridspec import GridSpec

from rasc.rasc_polling import get_best_distribution, get_polls


class VirtualDevice:
    def __init__(self, data) -> None:
        self.rvs = data

    def action(self):
        return np.random.choice(self.rvs)


RUNS = 100


def main():
    with open("datasets/rasc_history_exp.json", "r") as f:
        history = json.load(f)

    actions = [
        ("cover.rpi_device_door,open_cover,0", "door_open", 0.19),
        ("cover.rpi_device_door,close_cover,0", "door_close", 0.19),
        ("climate.rpi_device_thermostat,set_temperature,68,69", "thermostat_68,69", 16.19),
        ("cover.rpi_device_shade,open_cover,0", "shade_up", 0.31),
        ("cover.rpi_device_shade,close_cover,0", "shade_down", 1.54),
    ]

    # ---------- LOAD OR COMPUTE RESULTS ----------
    if os.path.exists("results/MIA_results.json"):
        with open("results/MIA_results.json", "r") as f:
            results = json.load(f)
    else:
        results = {}
        for action in actions:
            print("Running action:", action[1])

            data = history["data"]["history"][action[0]]["ct_history"]

            d = VirtualDevice(data)
            dist = get_best_distribution(data)

            avg_action_length = np.mean(data)
            qws = np.arange(0, avg_action_length / 3,
                            avg_action_length / 30)[1:10]
            rate_limits = np.arange(0, avg_action_length * 0.4,
                                    avg_action_length * 0.04)[1:10]

            values = []
            for qw in qws:
                for rate_limit in rate_limits:
                    polls = get_polls(
                        dist,
                        worst_case_delta=qw,
                        SLO=0.95,
                        rate_limit=rate_limit,
                    )

                    avg_detection_time = []
                    for _ in range(RUNS):
                        action_length = d.action()
                        for l in polls:
                            if action_length < l:
                                avg_detection_time.append(l - action_length)
                                break

                    values.append(
                        sum(avg_detection_time) / len(avg_detection_time)
                    )

            results[action[1]] = values

        with open("results/MIA_results.json", "w") as f:
            json.dump(results, f, indent=4)

    # ---------- FIGURE LAYOUT (2 ROWS, PER-PLOT COLORBARS) ----------
    n_actions = len(actions)
    nrows = 2
    ncols = ceil(n_actions / nrows)
    fig = plt.figure(figsize=(5.6 * ncols, 5.2 * nrows))
    gs = GridSpec(
        nrows,
        ncols,  # heatmap + colorbar per column
        figure=fig,
        wspace=0.1,
        hspace=0.15,
    )

    heatmap_axes = []

    for r in range(nrows):
        for c in range(ncols):
            idx = r * ncols + c
            if idx >= n_actions:
                continue
            heatmap_axes.append(fig.add_subplot(gs[r, c]))

    # ---------- PLOTTING ----------
    for idx, action in enumerate(actions):
        data = history["data"]["history"][action[0]]["ct_history"]

        avg_action_length = np.mean(data)

        qws = np.arange(0, avg_action_length / 3,
                        avg_action_length / 30)[1:10]
        rate_limits = np.arange(0, avg_action_length * 0.4,
                                avg_action_length * 0.04)[1:10]

        values = results[action[1]]
        n_rate = len(rate_limits)
        n_qw = len(values) // n_rate

        heatmap_data = np.asarray(values, dtype=float).reshape(
            n_qw, n_rate) / qws[:, None]

        # ----- colormap -----
        green = Color("green")
        color_options = list(
            map(lambda c: c.hex,
                green.range_to(Color("red"), 256))
        )
        cmap = matplotlib.colors.LinearSegmentedColormap.from_list(
            "", color_options
        )

        ax = heatmap_axes[idx]

        norm = Normalize(vmin=0, vmax=1.0)
        sn.heatmap(
            heatmap_data,
            norm=norm,
            cmap=cmap,
            # annot=True,
            square=True,
            cbar=False,
            ax=ax,
        )

        # ----- formatting -----
        ax.invert_yaxis()
        ax.set_title(action[1], fontsize=28, pad=10)

        xtick_idx = np.linspace(
            0, len(rate_limits) - 1, min(5, len(rate_limits)), dtype=int)
        ytick_idx = np.linspace(
            0, len(qws) - 1, min(5, len(qws)), dtype=int)

        ax.set_xticks(xtick_idx + 0.5)
        ax.set_yticks(ytick_idx + 0.5)

        if idx > 1:
            ax.set_xticklabels(
                [f"{int(rate_limits[i] / avg_action_length * 100)}"
                 for i in xtick_idx],
                fontsize=28
            )
        else:
            ax.set_xticklabels([])

        if idx in (0, 3):
            ax.set_yticklabels(
                [f"{int(qws[i] / avg_action_length * 100)}"
                 for i in ytick_idx],
                fontsize=28,
                rotation=0,
            )
        else:
            ax.set_yticklabels([])

    sm = ScalarMappable(norm=norm, cmap=cmap)
    sm.set_array([])

    cbar = fig.colorbar(
        sm,
        ax=heatmap_axes,
        orientation="vertical",
        fraction=0.025,
        pad=0.02,
    )

    cbar.ax.tick_params(labelsize=28)
    # ---------- GLOBAL LABELS ----------
    fig.supxlabel("MIA (% of Action Length)", fontsize=32, y=0.01)
    fig.supylabel("Qw (% of Action Length)", fontsize=32, x=0.07)

    fig.savefig("results/MIA_results.pdf", bbox_inches="tight", dpi=300)


if __name__ == "__main__":
    main()
