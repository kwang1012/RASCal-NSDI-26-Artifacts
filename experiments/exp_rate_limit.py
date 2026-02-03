import os
import json
from matplotlib.cm import ScalarMappable
from matplotlib.colors import Normalize
from matplotlib.lines import Line2D
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
        ("cover.rpi_device_door,open_cover,0", "door_open"),
        ("cover.rpi_device_door,close_cover,0", "door_close"),
        ("climate.rpi_device_thermostat,set_temperature,68,69", "thermostat_68,69"),
        ("cover.rpi_device_shade,open_cover,0", "shade_up"),
        ("cover.rpi_device_shade,close_cover,0", "shade_down"),
    ]

    qw_range = 0.6
    rate_limit_range = 0.4
    y_step = 20
    x_step = 10

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
            qws = np.linspace(
                0,
                avg_action_length * qw_range,
                y_step + 1
            )[1:]

            rate_limits = np.linspace(
                0,
                avg_action_length * rate_limit_range,
                x_step + 1
            )[1:]

            values = []
            avg = []
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
                        avg.append(action_length)
                        for l in polls:
                            if action_length < l:
                                avg_detection_time.append(l - action_length)
                                break

                    values.append(
                        sum(avg_detection_time) / len(avg_detection_time)
                    )

            results[action[1]] = {
                "avg_action_length": np.mean(avg),
                "values": values
            }

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
    legend_ax = None

    for r in range(nrows):
        for c in range(ncols):
            idx = r * ncols + c
            ax = fig.add_subplot(gs[r, c])

            if idx < n_actions:
                heatmap_axes.append(ax)
            else:
                legend_ax = ax

    legend_ax.axis("off")

    left = -0.1
    top = 0.95
    # Title as explicit text
    legend_ax.text(
        left, top,
        "Avg. Action Length",
        fontsize=24,
        ha="left",
        va="top",
        fontweight="bold",
        transform=legend_ax.transAxes,
    )

    # Legend entries as text
    y = top - 0.15
    line_gap = 0.12
    
    action_order = [
        "door_close", "door_open", "shade_up", "shade_down", "thermostat_68,69"]

    for a in action_order:
        if a == "thermostat_68,69":
            label = "thermo_68,69"
        else:
            label = a
        legend_ax.text(
            left, y,
            f"{label}: {results[a]['avg_action_length']:.2f}s",
            fontsize=24,
            ha="left",
            va="top",
            transform=legend_ax.transAxes,
        )
        y -= line_gap


    # ---------- PLOTTING ----------
    for idx, action in enumerate(actions):
        data = history["data"]["history"][action[0]]["ct_history"]

        avg_action_length = np.mean(data)

        qws = np.linspace(
            0,
            avg_action_length * qw_range,
            y_step + 1
        )[1:]

        rate_limits = np.linspace(
            0,
            avg_action_length * rate_limit_range,
            x_step + 1
        )[1:]

        values = results[action[1]]["values"]
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
            square=False,
            cbar=False,
            ax=ax,
        )

        # ----- formatting -----
        ax.invert_yaxis()
        ax.invert_xaxis()
        ax.set_title(action[1], fontsize=28, pad=10)

        xtick_idx = np.linspace(
            0, len(rate_limits) - 1, 10, dtype=int)
        ytick_idx = np.linspace(
            0, len(qws) - 1, min(5, len(qws)), dtype=int)

        ax.set_xticks(xtick_idx + 0.5)
        ax.set_yticks(ytick_idx + 0.5)

        if idx > 1:
            ax.set_xticklabels(
                [f"{int(rate_limits[i] / avg_action_length * 100)}"
                 for i in xtick_idx],
                fontsize=20
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
    fig.supxlabel(
        "Minimum Interarrival (MIA) gap (% of Avg. Action Length)", fontsize=32, y=0.01)
    fig.supylabel("Qw (% of Avg. Action Length)", fontsize=32, x=0.05)

    fig.savefig("results/MIA_results.pdf", bbox_inches="tight", dpi=300)


if __name__ == "__main__":
    main()
