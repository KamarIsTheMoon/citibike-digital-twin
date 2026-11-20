# Data

This folder is where the raw trip file goes. It is not included in the repository.

1. Go to https://citibikenyc.com/system-data and open the trip history files.
2. Download the Jersey City file for June 2023: `JC-202306-citibike-tripdata.csv.zip`.
3. Unzip it and place `JC-202306-citibike-tripdata.csv` in this folder.

Any other month works too: pass its path with `--data` when you run `scripts/run_analysis.py`.

For `scripts/deep_analysis.py`, also download `JC-202301-citibike-tripdata.csv.zip` (January 2023).
