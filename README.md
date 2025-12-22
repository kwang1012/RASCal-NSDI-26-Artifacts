# RASCal NSDI'26 Artifacts

The experiments in the papers use multiple Raspberry PIs and real devices. For the reproducability purpose, in this repo we simulate all the devices in a single node setting.

### TODOs
- [ ] 7_1 parsing script
- [ ] 7_3 deployed parsing script
- [ ] 7_4


### 1. Setup Environment
We use [uv](https://docs.astral.sh/uv/getting-started/installation/) to manage Python environment.

```bash
./scripts/setup.sh
```

### 2. Reproduce the results

To start the experiments included in the papers, please run the scripts under `scripts` folder. The results will be saved to `results`.

To reproduce the results from Section 7.1, for example:
```bash
./scripts/exp_7_1.sh
```