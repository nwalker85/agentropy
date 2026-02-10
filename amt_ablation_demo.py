#!/usr/bin/env python3
"""
Agent Mass Theory — Ablation Study Demo
=========================================

Runs the full ablation study: three conditions × four experiments.
Produces a comparison table showing that conservation is causal.

Run: python3 amt_ablation_demo.py [--seed N]
"""

import sys
import time
import argparse

from amt_ablation import run_full_ablation, format_comparison


def main():
    parser = argparse.ArgumentParser(description="AMT Ablation Study")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()

    print()
    print("▓" * 78)
    print("  AGENT MASS THEORY — ABLATION STUDY")
    print("  Does the conservation law CAUSE emergent behavior?")
    print("▓" * 78)
    print()
    print("  Three conditions:")
    print("    CONTROL:  Standard interact() — conservation ON, class-selective")
    print("    IMMORTAL: Layers matched, NOT consumed — no depletion")
    print("    RANDOM:   Random layers consumed — depletion without structure")
    print()
    print("  Four experiments:")
    print("    1. Scarcity       — Do agents die?")
    print("    2. Stratification — Do rich and poor diverge?")
    print("    3. Selectivity    — Do mass profiles create niches?")
    print("    4. Accountability — Does conservation enable audit?")
    print()

    t0 = time.time()

    print("  Running ablation (seed={})...".format(args.seed))
    print()

    results = run_full_ablation(seed=args.seed)

    elapsed = time.time() - t0

    print(format_comparison(results))
    print()
    print(f"  Completed in {elapsed:.2f}s")
    print()


if __name__ == "__main__":
    main()
