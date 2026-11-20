"""Minute by minute simulation of one bike share station.

The idea in one sentence: every minute, a random number of riders try to take
a bike and a random number try to return one; the station can only hold
`capacity` bikes, so some of them fail. Operating policies (trucks, rider
incentives) change what happens, and we count the failures.
"""
from dataclasses import dataclass, field
import numpy as np
import pandas as pd

MINUTES_PER_DAY = 24 * 60


@dataclass
class Policy:
    """How the station is managed during the day.

    schedule:  {minute_of_day: target_fill} for trucks that come at fixed times
    truck_size: maximum number of bikes a scheduled truck can move
    threshold: (low, high) fill levels that trigger a truck, e.g. (0.15, 0.85)
    delay:     minutes between the alert and the truck arriving
    nudge:     share of riders who accept to use a nearby station when this one
               is above 80 percent full (returns) or below 20 percent (rentals)
    """
    schedule: dict = field(default_factory=dict)
    truck_size: int = 30
    threshold: tuple = None
    delay: int = 20
    nudge: float = 0.0


def simulate(rates, policy=None, capacity=40, n_days=500, start_fill=0.5,
             day_sigma=0.12, seed=7, keep_first_day=True):
    """Simulate `n_days` weekdays and return (results_per_day, first_day_trajectory).

    rates:     DataFrame from data.hourly_rates (24 rows, columns dep and arr)
    capacity:  number of docks at the station
    day_sigma: size of the random busy or quiet day effect
    """
    policy = policy or Policy()
    rng = np.random.default_rng(seed)
    # turn hourly averages into per minute averages (60 identical minutes per hour)
    lam_dep = np.repeat(rates["dep"].to_numpy() / 60, 60)
    lam_arr = np.repeat(rates["arr"].to_numpy() / 60, 60)

    days, trajectory = [], None
    for day in range(n_days):
        # one random factor per day: mean 1, so on average demand equals the data
        factor = rng.lognormal(-day_sigma ** 2 / 2, day_sigma)
        bikes = int(capacity * start_fill)
        kpi = dict(fail_rent=0, fail_ret=0, served_dep=0, served_arr=0,
                   min_empty=0, min_full=0, visits=0, moved=0, nudged=0.0,
                   longest_outage=0, outage_day=0)
        streak = 0
        truck_eta = None
        path = []
        for m in range(MINUTES_PER_DAY):
            # 1. a truck called earlier by an alert arrives and resets the station
            if truck_eta is not None and m >= truck_eta:
                target = int(capacity * 0.5)
                kpi["moved"] += abs(bikes - target)
                bikes = target
                kpi["visits"] += 1
                truck_eta = None
            # 2. a scheduled truck visit
            if m in policy.schedule:
                target = int(capacity * policy.schedule[m])
                move = min(abs(bikes - target), policy.truck_size)
                bikes += move if target > bikes else -move
                kpi["moved"] += move
                kpi["visits"] += 1
            # 3. demand this minute, reduced by incentives when the station is nearly full or empty
            la, ld = lam_arr[m] * factor, lam_dep[m] * factor
            if policy.nudge and bikes >= 0.8 * capacity:
                kpi["nudged"] += la * policy.nudge
                la *= 1 - policy.nudge
            if policy.nudge and bikes <= 0.2 * capacity:
                kpi["nudged"] += ld * policy.nudge
                ld *= 1 - policy.nudge
            # 4. riders taking bikes, then riders returning bikes
            for _ in range(rng.poisson(ld)):
                if bikes > 0:
                    bikes -= 1
                    kpi["served_dep"] += 1
                else:
                    kpi["fail_rent"] += 1
            for _ in range(rng.poisson(la)):
                if bikes < capacity:
                    bikes += 1
                    kpi["served_arr"] += 1
                else:
                    kpi["fail_ret"] += 1
            # 5. record the state of the station
            kpi["min_empty"] += bikes == 0
            kpi["min_full"] += bikes == capacity
            if m >= 360 and (bikes == 0 or bikes == capacity):
                kpi["outage_day"] += 1   # outage minutes between 6 am and midnight
            # longest continuous outage (station empty or full) between 6 am and 10 pm
            if 360 <= m < 1320 and (bikes == 0 or bikes == capacity):
                streak += 1
                kpi["longest_outage"] = max(kpi["longest_outage"], streak)
            else:
                streak = 0
            # 6. sensor rule: call a truck if the station passes a threshold
            if policy.threshold and truck_eta is None:
                low, high = policy.threshold
                if bikes >= high * capacity or bikes <= low * capacity:
                    truck_eta = m + policy.delay
            if keep_first_day and day == 0:
                path.append(bikes)
        if day == 0:
            trajectory = path
        days.append(kpi)
    return pd.DataFrame(days), trajectory
