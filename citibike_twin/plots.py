"""Black and white charts used in the README and the reports."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

plt.rcParams.update({"font.family": "DejaVu Serif", "font.size": 9})


def _clean(ax):
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)


def hourly_profile(rates, station, path):
    fig, ax = plt.subplots(figsize=(7, 2.9))
    x = np.arange(24)
    ax.bar(x - 0.2, rates["dep"], 0.4, color="#333333", label="Bikes taken")
    ax.bar(x + 0.2, rates["arr"], 0.4, color="#BBBBBB", edgecolor="black", lw=0.4, label="Bikes returned")
    ax.set_xticks(range(0, 24, 2)); ax.set_xlabel("Hour of day"); ax.set_ylabel("Average per weekday")
    ax.set_title(f"{station}: weekday demand", fontsize=9); ax.legend(frameon=False, fontsize=8); _clean(ax)
    fig.tight_layout(); fig.savefig(path, dpi=200); plt.close(fig)


def cumulative_inflow(rates, capacity, path):
    cum = (rates["arr"] - rates["dep"]).cumsum()
    fig, ax = plt.subplots(figsize=(7, 2.8))
    ax.plot(range(1, 25), cum.values, "k-o", ms=3)
    ax.axhline(capacity, color="black", ls="--", lw=1)
    ax.text(1, capacity + 2, f"{capacity} docks (assumed)", fontsize=8)
    ax.set_xticks(range(0, 25, 2)); ax.set_xlabel("End of hour"); ax.set_ylabel("Extra bikes vs midnight")
    ax.set_title(f"Cumulative net inflow (peak: about {cum.max():.0f} bikes)", fontsize=9); _clean(ax)
    fig.tight_layout(); fig.savefig(path, dpi=200); plt.close(fig)


def validation(observed, simulated, path):
    fig, ax = plt.subplots(figsize=(6.5, 2.8))
    bins = np.arange(observed.min() // 10 * 10 - 30, observed.max() // 10 * 10 + 50, 10)
    ax.hist(simulated, bins=bins, density=True, color="#CCCCCC", edgecolor="black", lw=0.5,
            label=f"Twin (mean {simulated.mean():.0f}, sd {simulated.std():.0f})")
    ax.hist(observed, bins=bins, density=True, histtype="step", color="black", lw=2,
            label=f"Real data (mean {observed.mean():.0f}, sd {observed.std():.0f})")
    ax.set_yticks([]); ax.set_ylim(0, ax.get_ylim()[1] * 1.45); ax.set_xlabel("Bikes taken per weekday")
    ax.set_title("Validation: twin versus real data", fontsize=9); ax.legend(frameon=False, fontsize=7.5, loc="upper left"); _clean(ax)
    fig.tight_layout(); fig.savefig(path, dpi=200); plt.close(fig)


def kpi_bars(table, path):
    fig, ax = plt.subplots(figsize=(7, 3))
    y = np.arange(len(table))
    ax.barh(y - 0.2, table["Failed rentals/day"], 0.4, color="#333333", label="Failed rentals (empty)")
    ax.barh(y + 0.2, table["Failed returns/day"], 0.4, color="#BBBBBB", edgecolor="black", lw=0.4, label="Failed returns (full)")
    ax.set_yticks(y); ax.set_yticklabels(table.index, fontsize=8); ax.invert_yaxis()
    ax.set_xlabel("Riders affected per weekday"); ax.legend(frameon=False, fontsize=7.5, loc="lower right"); _clean(ax)
    fig.tight_layout(); fig.savefig(path, dpi=200); plt.close(fig)


def trajectories(paths, capacity, path):
    fig, ax = plt.subplots(figsize=(7, 2.9))
    hours = np.arange(len(next(iter(paths.values())))) / 60
    styles = [("#999999", 1.5), ("black", 1.2)]
    for (name, p), (color, lw) in zip(paths.items(), styles):
        ax.plot(hours, p, color=color, lw=lw, label=name)
    ax.axhline(capacity, ls="--", color="black", lw=0.8); ax.axhline(0, ls="--", color="black", lw=0.8)
    ax.set_xlim(0, 24); ax.set_ylim(-2, capacity * 1.3); ax.set_xticks(range(0, 25, 2))
    ax.set_xlabel("Hour of day"); ax.set_ylabel("Bikes at the station")
    ax.legend(frameon=False, fontsize=7.5, loc="upper left", ncol=2); _clean(ax)
    fig.tight_layout(); fig.savefig(path, dpi=200); plt.close(fig)
