#!/bin/bash

# Experiment 7.2: RASCal convergence time
# 1. Training time
# 2. Shift distribution convergence time
uv run -m experiments.exp_7_2


uv run experiments/parse_7_2_result.py