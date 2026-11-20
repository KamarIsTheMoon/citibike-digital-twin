"""Station level analysis of the whole system: imbalance and station types."""
import numpy as np
import pandas as pd


def station_profiles(trips, min_trips=300):
    """Weekday hourly net flow (returns minus rentals) per station, per weekday.

    Returns (profiles, totals): profiles has one row per station and 24 columns.
    """
    s = trips[trips["started_at"].dt.dayofweek < 5]
    e = trips[trips["ended_at"].dt.dayofweek < 5]
    days = s["started_at"].dt.date.nunique()
    dep = s.groupby(["start_station_name", s["started_at"].dt.hour]).size().unstack(fill_value=0)
    arr = e.groupby(["end_station_name", e["ended_at"].dt.hour]).size().unstack(fill_value=0)
    idx = dep.index.union(arr.index)
    dep = dep.reindex(index=idx, columns=range(24), fill_value=0)
    arr = arr.reindex(index=idx, columns=range(24), fill_value=0)
    totals = pd.DataFrame({"dep": dep.sum(1) / days, "arr": arr.sum(1) / days})
    keep = (dep.sum(1) + arr.sum(1)) >= min_trips
    profiles = ((arr - dep) / days)[keep]
    totals = totals[keep]
    # rebalancing need: largest swing of the cumulative net flow during a day
    cum = profiles.cumsum(axis=1)
    totals["peak_swing"] = cum.max(1) - cum.min(1)
    return profiles, totals


def kmeans(X, k=3, n_init=20, seed=0, iters=100):
    """Small k-means implementation (no extra library needed)."""
    rng = np.random.default_rng(seed)
    best = None
    for _ in range(n_init):
        C = X[rng.choice(len(X), k, replace=False)]
        for _ in range(iters):
            lab = ((X[:, None, :] - C[None]) ** 2).sum(-1).argmin(1)
            newC = np.array([X[lab == j].mean(0) if (lab == j).any() else C[j] for j in range(k)])
            if np.allclose(newC, C):
                break
            C = newC
        inertia = ((X - C[lab]) ** 2).sum()
        if best is None or inertia < best[0]:
            best = (inertia, lab, C)
    return best[1], best[2]


def station_types(profiles, k=3):
    """Cluster stations by the shape of their morning and evening net flow."""
    morning = profiles[[6, 7, 8, 9]].sum(1)
    evening = profiles[[16, 17, 18, 19]].sum(1)
    X = np.column_stack([morning, evening])
    scale = X.std(0)
    lab, C = kmeans(X / scale, k=k)
    C = C * scale
    names = {}
    for j, (m, e) in enumerate(C):
        if m > 2 and e < -2:
            names[j] = "Morning sink (commuter destination)"
        elif m < -2 and e > 2:
            names[j] = "Morning source (residential)"
        else:
            names[j] = "Balanced"
    out = pd.DataFrame({"morning_net": morning, "evening_net": evening,
                        "type": [names[l] for l in lab]}, index=profiles.index)
    return out, C
