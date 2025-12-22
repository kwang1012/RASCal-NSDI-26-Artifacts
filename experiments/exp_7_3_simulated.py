import numpy as np
import json

from rasc.datasets import load_dataset, Device
from rasc.rasc_polling import get_best_distribution, get_polls, get_uniform_polls

RUNS = 100


class VirtualDevice:
    def __init__(self, datasets) -> None:
        self.rvs = datasets["68,69"]

    def action(self):
        return np.random.choice(self.rvs)


def run(interruption_moment, interruption_interval, datasets, uniform=False):
    d = VirtualDevice(datasets)
    data = [
        426.6,
        386.0,
        402.7220780849457,
        401.15407729148865,
        399.91518902778625,
        142.67323192444763,
        713.6420514583588,
        470.8443745413858,
        354.6268392927061,
        466.71549574466354,
        700.5159847736359,
        436.8053950762571,
        263.35317546759694,
        693.656733757961,
        628.6432844649123,
        446.81944503335967,
        199.29804159745072,
        409.48339295855703,
        509.14030751084334,
        486.4950030346348,
        309.9383400641653,
        603.6287528138773,
        405.2079495969983,
        464.72987516761737,
        405.2455610439525,
        405.238643976813,
        405.23325462795407,
        440.5566040106894,
        434.4646002981388,
        434.4087708947217,
        434.3379116126164,
        434.25586792707855,
        394.061994240493,
        259.2533820837949,
        448.9449112530565,
        342.52056287646053,
        404.48293467458905,
        519.3764107210849,
        359.3246381578764,
        448.1031391086659,
        426.7052783737744,
    ]
    avg_action_length = np.mean(data)
    interruption_length = avg_action_length * interruption_interval / 100
    dist = get_best_distribution(data)
    worst_q = 30
    if uniform:
        L = get_uniform_polls(
            dist.ppf(0.99), worst_case_delta=worst_q)  # type: ignore
    else:
        L = get_polls(dist, worst_case_delta=worst_q, SLO=0.9)
    max_polls = len(L)
    for i in range(100):
        if uniform:
            L.append(L[-1] + worst_q)
        else:
            L.append(L[-1] + min(2**i, worst_q))
    avg_detection_time = []
    avg_used_polls = []
    failed_count = 0
    for _ in range(RUNS):
        action_length = d.action()
        new_action_length = action_length + interruption_length
        for i, l in enumerate(L):
            if new_action_length < l:
                # check if it is failed
                if i >= max_polls:
                    if (
                        action_length * interruption_moment +
                            interruption_length - L[max_polls - 1]
                        > 2 * worst_q + 1
                    ):
                        failed_count += 1
                # print(l - action_length)

                avg_used_polls.append(i + 1)
                avg_detection_time.append(l - new_action_length)
                break

    return (
        failed_count / RUNS,
        max_polls,
        sum(avg_used_polls) / len(avg_used_polls),
        sum(avg_detection_time) / len(avg_detection_time),
    )
    # print("Failed rate:", failed_count/RUNS)
    # print("Used polls:", sum(avg_used_polls) / len(avg_used_polls))
    # print("Detection time:", sum(avg_detection_time) / len(avg_detection_time))


def main():
    datasets = load_dataset(Device.THERMOSTAT)
    results = {}
    for interruption_moment in [0.5, 0.8, 0.9]:
        print(f"=== Interruption moment: {interruption_moment} ===")
        result = {
            "detection_time": [],
            "failed_rate": [],
            "max_polls": [],
            "used_polls": [],
        }
        for interruption_level in range(0, 105, 5):
            print(f"Interruption level: {interruption_level}")
            failed_rate, max_polls, used_polls, detection_time = run(
                interruption_moment,
                interruption_level,
                datasets
            )
            result["detection_time"].append(detection_time)
            result["failed_rate"].append(failed_rate)
            result["max_polls"].append(max_polls)
            result["used_polls"].append(used_polls)
        results[f"interruption_{int(interruption_moment*100)}"] = result

    with open("results/7_3_simulated.json", "w") as f:
        json.dump(results, f)


if __name__ == "__main__":
    main()
