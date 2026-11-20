"""Run the whole project from the raw trip file to the figures and result tables.

Usage (from the repository root):
    python scripts/run_analysis.py --data data/JC-202306-citibike-tripdata.csv
"""
import argparse
import json
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from citibike_twin import (POLICIES, Policy, daily_departures, hourly_rates, load_trips,
                           simulate, summarize, system_summary)
from citibike_twin import plots


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data/JC-202306-citibike-tripdata.csv")
    ap.add_argument("--station", default="Grove St PATH")
    ap.add_argument("--capacity", type=int, default=40, help="docks at the station (assumption)")
    ap.add_argument("--days", type=int, default=500, help="simulated weekdays per policy")
    args = ap.parse_args()
    os.makedirs("results", exist_ok=True); os.makedirs("figures", exist_ok=True)

    print("1. Loading data")
    trips = load_trips(args.data)
    summary = system_summary(trips)
    print(json.dumps(summary, indent=2, default=float))

    print("2. Learning hourly demand at", args.station)
    rates = hourly_rates(trips, args.station)
    rates.round(2).to_csv("results/hourly_rates.csv")

    print("3. Validating the twin against real daily demand")
    observed = daily_departures(trips, args.station)
    val_days, _ = simulate(rates, Policy(), capacity=10 ** 6, n_days=args.days)
    simulated = val_days["served_dep"]
    print(f"   real:  mean {observed.mean():.1f}, sd {observed.std():.1f} over {len(observed)} weekdays")
    print(f"   twin:  mean {simulated.mean():.1f}, sd {simulated.std():.1f} over {args.days} simulated weekdays")

    print("4. Testing the policies")
    rows, paths = {}, {}
    for name, policy in POLICIES.items():
        days, path = simulate(rates, policy, capacity=args.capacity, n_days=args.days)
        rows[name] = summarize(days)
        paths[name] = path
    table = pd.DataFrame(rows).T.round(1)
    table.index.name = "Policy"
    print(table.to_string())
    table.to_csv("results/kpi_results.csv")

    print("5. Sensitivity to the number of docks")
    sens = []
    for cap in (30, 40, 50):
        for name in ("AS IS (no intervention)", "D. Sensor trucks + incentives"):
            days, _ = simulate(rates, POLICIES[name], capacity=cap, n_days=max(200, args.days // 2))
            sens.append({"Docks": cap, "Policy": name, **{k: round(v, 1) for k, v in summarize(days).items()}})
    pd.DataFrame(sens).to_csv("results/sensitivity.csv", index=False)

    print("6. Saving figures")
    plots.hourly_profile(rates, args.station, "figures/hourly_profile.png")
    plots.cumulative_inflow(rates, args.capacity, "figures/cumulative_inflow.png")
    plots.validation(observed, simulated, "figures/validation.png")
    plots.kpi_bars(table, "figures/kpi_comparison.png")
    plots.trajectories({"AS IS (no intervention)": paths["AS IS (no intervention)"],
                        "D. Sensor trucks + incentives": paths["D. Sensor trucks + incentives"]},
                       args.capacity, "figures/one_day.png")
    with open("results/system_summary.json", "w") as f:
        json.dump(summary, f, indent=2, default=float)
    print("Done. See the results/ and figures/ folders.")


if __name__ == "__main__":
    main()
