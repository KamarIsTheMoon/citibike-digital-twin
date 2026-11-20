"""Turn the per day results of the simulation into one row of KPIs."""


def summarize(days):
    """Average the daily results into the KPIs reported in the project."""
    return {
        "Failed rentals/day": days["fail_rent"].mean(),
        "Failed returns/day": days["fail_ret"].mean(),
        "Riders affected/day": (days["fail_rent"] + days["fail_ret"]).mean(),
        "Minutes empty/day": days["min_empty"].mean(),
        "Minutes full/day": days["min_full"].mean(),
        "Truck visits/day": days["visits"].mean(),
        "Bikes moved/day": days["moved"].mean(),
        "Riders nudged/day": days["nudged"].mean(),
        "Outage share 6am to midnight (%)": 100 * days["outage_day"].mean() / 1080,
        "Longest outage (min)": days["longest_outage"].mean(),
    }


def confidence_interval(series, z=1.96):
    """95% confidence interval of the mean of a daily KPI."""
    m = series.mean()
    half = z * series.std(ddof=1) / len(series) ** 0.5
    return m - half, m + half
