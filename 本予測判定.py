# %%
### インポート ###
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path

# %%
path_schedule = Path.cwd().parent.parent / "data" / "pred" / "schedule.csv"
df_schedule_raw = pd.read_csv(path_schedule, header=0, encoding='cp932', dtype={'race_id': str})
df_schedule = df_schedule_raw.copy()
now = datetime.now()
limit = now + timedelta(minutes=30)
date_time = pd.to_datetime(now.strftime("%Y-%m-%d ") + df_schedule["race_time"])
mask = ((now <= date_time) & (date_time <= limit) & (df_schedule["status"] == "仮予測完了"))
df_schedule.loc[mask, "status"] = "本予測待ち"
df_schedule.to_csv(path_schedule, index=False, encoding="cp932")


