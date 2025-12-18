import itertools
import numpy as np
import matplotlib.pyplot as plt
import multiprocessing as mp

from rasc.rasc_polling import get_polls, get_uniform_polls, get_detection_time
from legacy.eval_dist import get_best_distribution
from parse_thermostat_data import get_thermo_datasets


def worker(params):
    dist, delta, SLO = params
    L = get_polls(
        dist,
        worst_case_delta=delta,
        SLO=SLO,
    )
    # L = get_uniform_polls(dist.ppf(0.99), worst_case_delta=delta, SLO=SLO)
    # Q = get_detection_time(dist, L)
    return len(L)


def main():
    num = 20
    SLOs = np.linspace(0.8, 0.99, num)
    worst_case_delta = [30, 40, 50, 60, 70, 80, 90]
    print(SLOs)
    colors = ["g", "r", "b"]

    datasets = get_thermo_datasets()
    dist = get_best_distribution(datasets["68,68"])
    fig, ax = plt.subplots()

    paramlist = [
        (dist, delta, SLO) for delta, SLO in itertools.product(worst_case_delta, SLOs)
    ]
    pool = mp.Pool()
    data = pool.map(worker, paramlist)


    print(data)
    # for i, delta in enumerate(worst_case_delta):
    #     print(data[i*num: (i+1)*num])
    #     ax.plot(SLOs, data[i*num: (i+1)*num], colors[i], label=f"Qw = {delta}")

    # ax.legend(loc="upper left")
    # ax.set_title("Confidence experiment")
    # ax.set_xlim((min(SLOs), max(SLOs)))

    # fig.tight_layout()
    # fig.savefig(f"confidence_detection_time.png")


if __name__ == "__main__":
    main()
