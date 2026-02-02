import numpy as np
import json
import matplotlib.pyplot as plt

from rasc.rasc_polling import get_best_distribution, get_polls


class VirtualDevice:
    def __init__(self, data) -> None:
        self.rvs = data

    def action(self):
        return np.random.choice(self.rvs)


RUNS = 200


def main():
    with open("datasets/rasc_history_exp.json", "r") as f:
        history = json.load(f)

    actions = [
        ("cover.rpi_device_door,open_cover,0", "door_open", 2),
        ("cover.rpi_device_door,close_cover,0", "door_close", 2),
        ("cover.rpi_device_shade,open_cover,0", "shade_up", 3),
        ("cover.rpi_device_shade,close_cover,0", "shade_down", 3),
        ("climate.rpi_device_thermostat,set_temperature,68,69", "thermostat\n68,69", 30),
    ]
    results = {}
    for action in actions:
        results[action] = []
        print("Running action:", action[1])
        data = history["data"]["history"][action[0]]["ct_history"]
        d = VirtualDevice(data)

        dist = get_best_distribution(data)

        rate_limits = np.arange(0, action[2] * 2, action[2] * 2 / 20)
        for i, rate_limit in enumerate(rate_limits):
            print(f"  Rate limit: {rate_limit:.2f}")
            polls = get_polls(
                dist, worst_case_delta=action[2], SLO=0.9, rate_limit=rate_limit)

            avg_detection_time = []
            avg_action_length = []
            for _ in range(RUNS):
                action_length = d.action()
                avg_action_length.append(action_length)
                for _, l in enumerate(polls):
                    if action_length < l:
                        detection_time = l - action_length
                        avg_detection_time.append(detection_time)
                        break
            print("Average action length:", sum(
                avg_action_length) / len(avg_action_length))
            print("Average detection time:", sum(
                avg_detection_time) / len(avg_detection_time))
            results[action].append(
                (i*10, 100*sum(avg_detection_time) / len(avg_detection_time) / action[2]))
    
    plt.figure(figsize=(8, 2.5))
    plt.tick_params(axis='both', which='major', labelsize=14)
    # plot results
    for action in actions:
        rate_limits, detection_times = zip(*results[action])
        plt.plot(rate_limits, detection_times, label=action[1])
    plt.xlabel("Rate/inter-poll limit (% of Qw)", fontsize=16)
    plt.ylabel("Detection time\n(% of Qw)", fontsize=16)
    plt.legend(fontsize=14, ncol=2, columnspacing=0.3, handletextpad=0.3)
    plt.grid(True)
    plt.savefig("results/exp_rate_limit.pdf", bbox_inches="tight")


if __name__ == "__main__":
    main()
