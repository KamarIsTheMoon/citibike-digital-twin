"""Load Citi Bike trip data and turn it into the inputs of the twin."""
import pandas as pd


def load_trips(path):
    """Read a monthly Citi Bike trip file and parse the two time columns."""
    return pd.read_csv(path, parse_dates=["started_at", "ended_at"], low_memory=False)


def _weekdays(trips, column):
    """Keep only trips whose time in `column` falls on Monday to Friday."""
    return trips[trips[column].dt.dayofweek < 5]


def hourly_rates(trips, station):
    """Average bikes taken (dep) and returned (arr) per weekday hour at one station.

    Returns a DataFrame with 24 rows (hours 0 to 23) and two columns: dep, arr.
    """
    starts = _weekdays(trips, "started_at")
    ends = _weekdays(trips, "ended_at")
    n_days = starts["started_at"].dt.date.nunique()
    dep = starts[starts["start_station_name"] == station].groupby(starts["started_at"].dt.hour).size()
    arr = ends[ends["end_station_name"] == station].groupby(ends["ended_at"].dt.hour).size()
    rates = pd.DataFrame({"dep": dep, "arr": arr}).reindex(range(24), fill_value=0).fillna(0)
    rates.index.name = "hour"
    return rates / n_days


def daily_departures(trips, station):
    """Bikes taken at the station on each weekday (used to validate the twin)."""
    starts = _weekdays(trips, "started_at")
    mine = starts[starts["start_station_name"] == station]
    return mine.groupby(mine["started_at"].dt.date).size()


def system_summary(trips):
    """A few headline numbers about the whole system for the month."""
    duration = (trips["ended_at"] - trips["started_at"]).dt.total_seconds() / 60
    per_day = trips.groupby(trips["started_at"].dt.date).size()
    return {
        "trips": len(trips),
        "days": int(per_day.size),
        "stations": int(trips["start_station_name"].nunique()),
        "avg_trips_per_day": round(per_day.mean(), 0),
        "member_share": round((trips["member_casual"] == "member").mean(), 3),
        "classic_share": round((trips["rideable_type"] == "classic_bike").mean(), 3),
        "median_minutes": round(duration.median(), 1),
    }
