import json
from rasc.rasc_polling import get_best_distribution, get_polls, get_uniform_polls
import numpy as np

from rasc.datasets import Device, load_dataset


class VirtualDevice:
    def __init__(self, datasets) -> None:
        # dist = get_best_distribution(datasets["68,68"])
        # self.rvs = list(dist.rvs(size=1000))
        self.rvs = datasets["68,68"]
        self.i = -1
        # with open("action_distributions/door.json", "r") as f:
        #     data = json.load(f)["close"]
        #     self.rvs = data

    def action(self):
        self.i += 1
        # return self.rvs[self.i % len(self.rvs)]
        return np.random.choice(self.rvs)

EXP_RUNS = 1

def run(datasets, i, uniform=False):
    d = VirtualDevice(datasets)
    data = []
    data.append(d.action())
    trial = 1
    last_10_mean_avg = []
    last_10_var_avg = []
    polls = []
    detection_times = []
    while trial < 1000:
        dist = get_best_distribution(data)
        worst_q = 30
        if uniform:
            L = get_uniform_polls(dist.ppf(0.99), worst_case_delta=worst_q) # type: ignore
        else:
            L = get_polls(dist, worst_case_delta=worst_q, SLO=0.9)
        # used_poll = 
        # print(get_detection_time(dist, L))
        # print(f"{get_detection_time(dist, L)}, {len(L)}")
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
        detection_times.append(sum(avg_detection_time) / len(avg_detection_time))
        
        data.append(action_length)
        mean_avg = sum(last_10_mean_avg) / len(last_10_mean_avg) if last_10_mean_avg else 0
        var_avg = sum(last_10_var_avg) / len(last_10_var_avg) if last_10_var_avg else 0
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
            print(trial)
            # x = np.linspace(0, dist.ppf(0.99), 1001)
            # fig = plt.figure()
            # ax = fig.add_subplot(1, 1, 1)
            # plt.close(fig)
            # ax.plot(x, dist.pdf(x))
            # ax.vlines(L, 0, 1, "red", "dashed")
            # ax.set_xlim((0, dist.ppf(0.99) + 2))
            # ax.set_ylim((0, max(dist.pdf(x))))

            # fig.savefig(f"results/trials/run_{i}.png")
            break
        trial += 1
    print(polls)
    print(detection_times)
    with open("experiments/4_2_2_result.json", "r") as f:
        data = json.load(f)
        if uniform:
            data["uniform"] = {"time": detection_times, "polls": polls}
        else:
            data["rasc"] = {"time": detection_times, "polls": polls}
            
    with open("experiments/4_2_2_result.json", "w") as f:
        json.dump(data, f)
    return trial

def main():
    datasets = load_dataset(Device.THERMOSTAT)
    run(datasets, 1)
    run(datasets, 1, True)
    # files = glob.glob('results/trials/*')
    # for f in files:
    #     os.remove(f)
    # trial_avg = []
    # for i in range(EXP_RUNS):
    #     trial = run(datasets, i)
    #     trial_avg.append(trial)

    # print(trial_avg)
    # print(np.mean(trial_avg), np.median(trial_avg), np.sqrt(np.var(trial_avg)))


if __name__ == "__main__":
    main()
