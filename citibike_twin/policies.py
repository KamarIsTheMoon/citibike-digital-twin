"""The AS IS baseline and the four redesign options tested in the project."""
from .simulation import Policy

POLICIES = {
    "AS IS (no intervention)": Policy(),
    "A. Scheduled trucks": Policy(schedule={7 * 60 + 30: 0.2, 9 * 60: 0.2, 16 * 60 + 30: 0.8, 18 * 60: 0.8}, truck_size=30),
    "B. Sensor triggered trucks": Policy(threshold=(0.15, 0.85), delay=20),
    "C. Rider incentives only": Policy(nudge=0.3),
    "D. Sensor trucks + incentives": Policy(threshold=(0.15, 0.85), delay=20, nudge=0.3),
}
