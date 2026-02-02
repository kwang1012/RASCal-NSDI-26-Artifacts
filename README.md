# RASCal NSDI'26 Artifacts

The experiments in the papers use multiple Raspberry PIs and real devices. For the reproducability purpose, in this repo we simulate all the devices in a single node setting. Due to some dependencies of home assistant, the published code can only run on Linux machines.

### 1. Setup Environment
We use [uv](https://docs.astral.sh/uv/getting-started/installation/) to manage Python environment.

**(Optional) To install uv**
```
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**To setup the dependencies**
```bash
./scripts/setup.sh
```

### 2. Run the example
You can confirm the environment has been created successfully, by running:
```bash
./hello_world.sh
```

### 3. Reproduce the results

To start the experiments included in the papers, please run the scripts under `scripts` folder. The results will be saved to `results`.

To reproduce the results from Section 7.1, for example:
```bash
./scripts/exp_7_1.sh
```

### Approximate time for each experiment to finish
- 7.1: ~100 minutes
- 7.2: 
- 7.3: ~315 minutes
- 7.4: 