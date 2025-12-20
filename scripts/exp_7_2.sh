#!/bin/bash

# Experiment 7.2: RASCal convergence time
# 1. Training time
uv run -m experiments.training
# 2. Shift distribution convergence time
uv run -m experiments.shift_dist


uv run experiments/parse_7_2_result.py