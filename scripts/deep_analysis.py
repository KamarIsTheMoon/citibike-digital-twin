"""Deeper analysis: whole network, station types, winter vs summer, confidence intervals,
the 4 hour outage rule and sensitivity of the recommended policy."""
import json, os, sys
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from citibike_twin import *
plt.rcParams.update({"font.family": "DejaVu Serif", "font.size": 9})
os.makedirs("results", exist_ok=True); os.makedirs("figures", exist_ok=True)
ST = "Grove St PATH"; OUT = {}
jun = load_trips("data/JC-202306-citibike-tripdata.csv"); jan = load_trips("data/JC-202301-citibike-tripdata.csv")
OUT["june"] = system_summary(jun); OUT["january"] = system_summary(jan)
# 1. network and station types (June)
prof, tot = station_profiles(jun)
types, C = station_types(prof)
tbl = tot.join(types); tbl.to_csv("results/station_types.csv")
OUT["type_counts"] = types["type"].value_counts().to_dict()
OUT["top_swing"] = tbl.sort_values("peak_swing", ascending=False).head(8)[["dep", "arr", "peak_swing", "type"]].round(1).reset_index().values.tolist()
OUT["share_swing_over_20"] = float((tbl["peak_swing"] > 20).mean())
fig, ax = plt.subplots(figsize=(6.5, 3.6))
mk = {"Morning sink (commuter destination)": ("s", "black"), "Morning source (residential)": ("^", "#777777"), "Balanced": ("o", "#BBBBBB")}
for t, (m, c) in mk.items():
    d = types[types["type"] == t]; ax.scatter(d["morning_net"], d["evening_net"], marker=m, c=c, edgecolors="black", lw=0.4, s=28, label=f"{t} ({len(d)})")
g = types.loc[ST]; ax.annotate("Grove St PATH", (g["morning_net"], g["evening_net"]), xytext=(g["morning_net"] - 40, g["evening_net"] + 8), arrowprops=dict(arrowstyle="->"), fontsize=8)
ax.axhline(0, color="black", lw=0.5); ax.axvline(0, color="black", lw=0.5)
ax.set_xlabel("Morning net flow, 6 to 10 am (bikes per weekday)"); ax.set_ylabel("Evening net flow, 4 to 8 pm")
ax.legend(frameon=False, fontsize=7.5, loc="lower left"); [ax.spines[s].set_visible(False) for s in ("top", "right")]
ax.set_title("Station types in Jersey City and Hoboken, June 2023 (k-means)", fontsize=9)
plt.tight_layout(); fig.savefig("figures/station_types.png", dpi=200); plt.close()
# 2. seasons
rj, rw = hourly_rates(jun, ST), hourly_rates(jan, ST)
OUT["grove_june"] = {"dep": round(rj.dep.sum(), 1), "arr": round(rj.arr.sum(), 1), "peak_cum": round((rj.arr - rj.dep).cumsum().max(), 1)}
OUT["grove_january"] = {"dep": round(rw.dep.sum(), 1), "arr": round(rw.arr.sum(), 1), "peak_cum": round((rw.arr - rw.dep).cumsum().max(), 1)}
fig, ax = plt.subplots(figsize=(6.5, 2.8))
ax.plot(range(1, 25), (rj.arr - rj.dep).cumsum().values, "k-o", ms=3, label="June 2023")
ax.plot(range(1, 25), (rw.arr - rw.dep).cumsum().values, "--s", color="#777777", ms=3, label="January 2023")
ax.axhline(40, ls=":", color="black", lw=1); ax.text(1, 42, "40 docks (assumed)", fontsize=8)
ax.set_xlabel("End of hour"); ax.set_ylabel("Extra bikes vs midnight"); ax.legend(frameon=False, fontsize=8); [ax.spines[s].set_visible(False) for s in ("top", "right")]
ax.set_title("Grove St PATH: the morning wave exists in winter too", fontsize=9)
plt.tight_layout(); fig.savefig("figures/seasons.png", dpi=200); plt.close()
# 3. policies with confidence intervals and the 4 hour rule, summer and winter
rows = []
for season, rates, n in (("June", rj, 400), ("January", rw, 250)):
    for name, pol in POLICIES.items():
        days, _ = simulate(rates, pol, capacity=40, n_days=n, seed=11)
        aff = days.fail_rent + days.fail_ret; lo, hi = confidence_interval(aff); k = summarize(days)
        rows.append({"Season": season, "Policy": name, "Riders affected/day": round(aff.mean(), 1), "95% CI low": round(lo, 1), "95% CI high": round(hi, 1),
                     "Days breaking 4 h rule (%)": round(k["Days breaking 4 h outage rule (%)"], 1), "Truck visits/day": round(k["Truck visits/day"], 1),
                     "Bikes moved/day": round(k["Bikes moved/day"], 1), "Riders nudged/day": round(k["Riders nudged/day"], 1)})
pt = pd.DataFrame(rows); pt.to_csv("results/policies_ci_seasons.csv", index=False); OUT["policies"] = rows
# 4. sensitivity of option D (one factor at a time)
base = dict(threshold=(0.15, 0.85), delay=20, nudge=0.3); cap0 = 40
def run(cap=cap0, **kw):
    p = dict(base); p.update(kw); d, _ = simulate(rj, Policy(**p), capacity=cap, n_days=200, seed=5)
    return (d.fail_rent + d.fail_ret).mean()
b = run(); sens = {"Base case": b}
tests = {"Truck delay 10 / 40 min": (run(delay=10), run(delay=40)), "Rider reaction 10% / 50%": (run(nudge=0.5), run(nudge=0.1)),
         "Alert at 10/90% / 25/75%": (run(threshold=(0.25, 0.75)), run(threshold=(0.10, 0.90))), "Docks 50 / 30": (run(cap=50), run(cap=30))}
OUT["sensitivity_base"] = round(b, 2); OUT["sensitivity"] = {k: [round(v[0], 2), round(v[1], 2)] for k, v in tests.items()}
fig, ax = plt.subplots(figsize=(6.5, 2.6)); y = np.arange(len(tests))
for i, (k, (good, bad)) in enumerate(tests.items()):
    ax.barh(i, bad - b, left=b, color="#555555"); ax.barh(i, good - b, left=b, color="#BBBBBB", edgecolor="black", lw=0.4)
ax.axvline(b, color="black", lw=1); ax.set_yticks(y); ax.set_yticklabels(list(tests.keys()), fontsize=8)
ax.set_xlabel("Riders affected per weekday with option D (base case %.1f)" % b); [ax.spines[s].set_visible(False) for s in ("top", "right")]
ax.set_title("Sensitivity of option D (light: better case, dark: worse case)", fontsize=9)
plt.tight_layout(); fig.savefig("figures/sensitivity_tornado.png", dpi=200); plt.close()
json.dump(OUT, open("results/deep_summary.json", "w"), indent=1, default=float); print(json.dumps(OUT, indent=1, default=float)[:4000])
