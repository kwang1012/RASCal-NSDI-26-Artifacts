# RASCal NSDI'26 Artifacts

The experiments in the papers use multiple Raspberry PIs and real devices. For the reproducability purpose, in this repo we simulate all the devices in a single node setting.

### 1. Setup Environment
We use [uv](https://docs.astral.sh/uv/getting-started/installation/) to manage Python environment.

```bash
uv sync
```

### 2. Reproduce the results

To start the experiments included in the papers, please run the scripts under `scripts` folder. The results will be saved to `results`.

To reproduce the results from Section 7.1, for example:
```bash
./scripts/exp_7_1.sh
```