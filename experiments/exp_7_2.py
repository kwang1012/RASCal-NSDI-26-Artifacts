import json
import numpy as np
from scipy.stats import wasserstein_distance

from rasc.rasc_polling import get_best_distribution, get_polls, get_uniform_polls
from rasc.datasets import Device, load_dataset


class VirtualDevice:
    def __init__(self, data) -> None:
        # dist = get_best_distribution(data)
        # self.rvs = list(dist.rvs(size=1000))
        self.rvs = data
        self.i = -1
        # with open("action_distributions/door.json", "r") as f:
        #     data = json.load(f)["close"]
        #     self.rvs = data

    def action(self):
        self.i += 1
        # return self.rvs[self.i % len(self.rvs)]
        return np.random.choice(self.rvs)


def run(rasc_setting):
    d = rasc_setting["device"]
    uniform = rasc_setting.get("uniform", False)
    worst_q = rasc_setting.get("worst_q", 1)
    data = []
    data.append(d.action())
    data_points = 1
    last_10_mean_avg = []
    last_10_var_avg = []
    polls = []
    detection_times = []
    while data_points < 1000:
        dist = get_best_distribution(data)
        if uniform:
            L = get_uniform_polls(
                dist.ppf(0.99), worst_case_delta=worst_q)  # type: ignore
        else:
            L = get_polls(dist, worst_case_delta=worst_q, SLO=0.9)
        for i in range(100):
            if uniform:
                L.append(L[-1] + worst_q)
            else:
                L.append(L[-1] + min(2**i, worst_q))
        avg_detection_time = []
        avg_used_polls = []
        action_length = None
        for _ in range(100):
            action_length = d.action()
            for i, l in enumerate(L):
                if action_length < l:
                    # print(l - action_length)
                    avg_used_polls.append(i+1)
                    avg_detection_time.append(l - action_length)
                    break
        polls.append(sum(avg_used_polls) / len(avg_used_polls))
        detection_times.append(
            sum(avg_detection_time) / len(avg_detection_time))

        data.append(action_length)
        mean_avg = sum(last_10_mean_avg) / \
            len(last_10_mean_avg) if last_10_mean_avg else 0
        var_avg = sum(last_10_var_avg) / \
            len(last_10_var_avg) if last_10_var_avg else 0
        mean, var = dist.stats()
        cv = np.sqrt(var)/mean
        mean_diff = (mean - mean_avg) / mean_avg if mean_avg else 1
        var_diff = (var - var_avg) / var_avg if var_avg else 1
        # print((mean_avg, var_avg), (mean, var), (mean_diff, var_diff), len(L))
        last_10_mean_avg.append(mean)
        last_10_var_avg.append(var)
        if len(last_10_mean_avg) > 10:
            last_10_mean_avg.pop(0)
        if len(last_10_var_avg) > 10:
            last_10_var_avg.pop(0)

        if len(last_10_mean_avg) == 10 and abs(mean_diff) < 0.05 and (abs(var_diff) < 0.05 or cv < 0.05):
            break
        data_points += 1
    return data_points


def training():
    thermostat_dataset = load_dataset(Device.THERMOSTAT)
    door_dataset = load_dataset(Device.DOOR)
    elevator_dataset = load_dataset(Device.ELEVATOR)
    shade_dataset = load_dataset(Device.SHADE)
    projector_dataset = load_dataset(Device.PROJECTOR)
    rasc_settings = [
        {
            "name": "thermostat.68,68",
            "device": VirtualDevice(thermostat_dataset["68,68"]),
            "worst_q": 30
        },
        {
            "name": "thermostat.68,70",
            "device": VirtualDevice(thermostat_dataset["68,70"]),
            "worst_q": 30
        },
        {
            "name": "door.close",
            "device": VirtualDevice(door_dataset["close"]),
            "worst_q": 1
        },
        {
            "name": "elevator.up",
            "device": VirtualDevice(elevator_dataset["up"]),
            "worst_q": 1
        },
        {
            "name": "shade.up",
            "device": VirtualDevice(shade_dataset["up"]),
            "worst_q": 1
        },
        {
            "name": "projector.up",
            "device": VirtualDevice(projector_dataset["screen_up"]),
            "worst_q": 1
        },
    ]
    results = {}
    for setting in rasc_settings:
        trial_avg = []
        for _ in range(10):
            num_data_points = run(setting)
            trial_avg.append(num_data_points)
        print(setting["name"], {
            "mean": sum(trial_avg) / len(trial_avg),
            "median": np.median(trial_avg),
            "std": np.sqrt(np.var(trial_avg)),
        })
        results[setting["name"]] = {
            "mean": sum(trial_avg) / len(trial_avg),
            "median": np.median(trial_avg),
            "std": np.sqrt(np.var(trial_avg)),
        }

    with open("results/7_2_training.json", "w") as f:
        json.dump(results, f)


DATA = [
    {
        "start": 66,
        "to": [67, 68, 69, 70],
    },
    {
        "start": 67,
        "to": [68, 69, 70, 71, 72],
    },
    {
        "start": 68,
        "to": [69, 70, 71, 72, 73],
    },
    {
        "start": 69,
        "to": [70, 71, 72, 73, 74, 75],
    },
    {
        "start": 73,
        "to": [74, 75, 76, 77],
    },
    {
        "start": 74,
        "to": [75, 76, 77, 78],
    },
]


class VirtualShade:
    def __init__(self, old_dataset, new_dataset) -> None:
        self.old_dataset = old_dataset
        self.new_dataset = new_dataset
        self.old_dist = get_best_distribution(old_dataset)
        self.new_dist = get_best_distribution(new_dataset)
        self.old_rvs = list(self.old_dist.rvs(size=1000))  # type: ignore
        self.new_rvs = list(self.new_dist.rvs(size=1000))  # type: ignore
        self.data = []
        self.i = -1
        self.j = -1

    def get_distance(self):
        return wasserstein_distance(self.old_rvs, self.new_rvs)

    def action(self, new=False):
        if new:
            self.i += 1
            choice = self.new_rvs[self.i % len(self.new_rvs)]
            # choice = np.random.choice(self.new_dist)
        else:
            self.j += 1
            choice = self.old_rvs[self.j % len(self.old_rvs)]
            # choice = np.random.choice(self.old_dist)
        self.data.append(choice)

    def reset(self):
        self.old_rvs = list(self.old_dist.rvs(size=1000))  # type: ignore
        self.new_rvs = list(self.new_dist.rvs(size=1000))  # type: ignore
        self.data = []
        self.i = -1
        self.j = -1

    def diff(self):
        return {
            "distance": self.get_distance(),
            "old_mean": self.old_dist.mean(),
            "old_std": self.old_dist.std(),
            "new_mean": self.new_dist.mean(),
            "new_std": self.new_dist.std(),
        }

    def print_diff(self):
        print("distance:", self.get_distance())
        print(self.old_dist.mean(), self.new_dist.mean())
        print(self.old_dist.std(), self.new_dist.std())
        # print(skew(self.old_dataset), skew(self.new_dataset))


WINDOW_SIZE = 10


def _shifted_run(d, new=False):
    trial = 1
    last_10_mean_avg = []
    last_10_var_avg = []
    while trial < 1000:
        d.action(new)
        dist = get_best_distribution(d.data)
        # L = get_polls(dist, worst_case_delta=60)

        mean_avg = (
            sum(last_10_mean_avg) /
            len(last_10_mean_avg) if last_10_mean_avg else 0
        )
        var_avg = sum(last_10_var_avg) / \
            len(last_10_var_avg) if last_10_var_avg else 0
        mean, var = dist.stats()
        cv = np.sqrt(var) / mean
        mean_diff = (mean - mean_avg) / mean_avg if mean_avg else 1
        var_diff = (var - var_avg) / var_avg if var_avg else 1
        # print((mean_avg, var_avg), (mean, var), (mean_diff, var_diff), len(L))
        # print(mean_diff, var_diff)
        last_10_mean_avg.append(mean)
        last_10_var_avg.append(var)
        if len(last_10_mean_avg) > WINDOW_SIZE:
            last_10_mean_avg.pop(0)
        if len(last_10_var_avg) > WINDOW_SIZE:
            last_10_var_avg.pop(0)

        if (
            len(last_10_mean_avg) == WINDOW_SIZE
            and abs(mean_diff) < 0.05
            and (abs(var_diff) < 0.05 or cv < 0.05)
        ):

            # x = np.linspace(0, dist.ppf(0.99), 1001)
            # fig = plt.figure()
            # ax = fig.add_subplot(1, 1, 1)
            # plt.close(fig)
            # ax.plot(x, dist.pdf(x))
            # ax.vlines(L, 0, 1, "red", "dashed")
            # ax.set_xlim((0, dist.ppf(0.99) + 2))
            # ax.set_ylim((0, max(dist.pdf(x))))

            # fig.savefig(f"results/trials/trial_{trial}.png")
            break
        trial += 1
    return trial


def shifting():

    datasets = load_dataset(Device.THERMOSTAT)
    diff_list = []
    result = {"data": []}
    for data in DATA:
        start = data["start"]
        targets = data["to"]
        initial_dataset = datasets[f"{start},{start}"]
        shift_datasets = []
        result_data = {
            "start": start,
            "to": [],
        }
        for target in targets:
            shift_datasets.append((target, datasets[f"{start},{target}"]))
        for target, shift_dataset in shift_datasets:
            d = VirtualShade(initial_dataset, shift_dataset)
            # diff_list.append(d.diff())
            trial_avg = []
            trial_shift_avg = []
            for i in range(10):
                # print(i)
                trial = _shifted_run(d)
                trial_shift = _shifted_run(d, True)
                # print(trial, trial_shift)
                trial_avg.append(trial)
                trial_shift_avg.append(trial_shift)
                d.reset()

            result_data["trials"] = sum(trial_avg) / len(trial_avg)
            result_data["to"].append(
                {
                    "target": target,
                    "distance": d.get_distance(),
                    "trials": sum(trial_shift_avg) / len(trial_shift_avg),
                }
            )
            print(sum(trial_avg)/len(trial_avg),
                  sum(trial_shift_avg)/len(trial_shift_avg))
        result["data"].append(result_data)
    with open("results/7_2_shifting.json", "w") as f:
        json.dump(result, f)
    # diff_list = sorted(diff_list, key=cmp_to_key(lambda a, b: a["distance"] - b["distance"]))
    # print(json.dumps(diff_list))


if __name__ == "__main__":
    training()
    shifting()
