"""Basic checks that the simulation behaves like a real station should."""
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from citibike_twin import Policy, simulate


def flat_rates(dep, arr):
    return pd.DataFrame({"dep": [dep] * 24, "arr": [arr] * 24})


def test_no_demand_means_nothing_happens():
    days, path = simulate(flat_rates(0, 0), Policy(), capacity=20, n_days=3)
    assert days[["fail_rent", "fail_ret", "served_dep", "served_arr"]].sum().sum() == 0
    assert set(path) == {10}  # stays half full all day


def test_station_never_goes_beyond_its_limits():
    _, path = simulate(flat_rates(30, 30), Policy(), capacity=15, n_days=1)
    assert min(path) >= 0 and max(path) <= 15


def test_bikes_are_conserved():
    days, path = simulate(flat_rates(5, 6), Policy(), capacity=40, n_days=1)
    d = days.iloc[0]
    assert 20 + d.served_arr - d.served_dep == path[-1]


def test_only_arrivals_fill_the_station_and_cause_failed_returns():
    days, _ = simulate(flat_rates(0, 10), Policy(), capacity=10, n_days=2)
    assert (days["fail_ret"] > 0).all() and (days["fail_rent"] == 0).all()


def test_same_seed_gives_same_result():
    a, _ = simulate(flat_rates(4, 4), Policy(), n_days=5, seed=1)
    b, _ = simulate(flat_rates(4, 4), Policy(), n_days=5, seed=1)
    assert a.equals(b)


def test_sensor_trucks_reduce_failures():
    rates = flat_rates(1, 8)
    base, _ = simulate(rates, Policy(), capacity=20, n_days=20)
    trucks, _ = simulate(rates, Policy(threshold=(0.15, 0.85), delay=10), capacity=20, n_days=20)
    assert trucks["fail_ret"].mean() < base["fail_ret"].mean()
