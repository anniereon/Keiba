# %% [markdown]
# # インポート

# %%
import pandas as pd
from pathlib import Path
from netkeiba_scraper import NetkeibaScraper

# %% [markdown]
# # 設定

# %%
config_path = Path.cwd().parent / "config.xlsx"
df_config_netkeiba = pd.read_excel(config_path, sheet_name="netkeiba", header=None, index_col=0)
LOGIN_ID = df_config_netkeiba.loc["LOGIN_ID"].iloc[0]
PASSWORD = df_config_netkeiba.loc["LOGIN_PASSWORD"].iloc[0]
MODE = "shutuba"

# %% [markdown]
# # レースデータ取得

# %%
# 本予測待ちのレース確認
path_schedule = Path.cwd().parent.parent / "data" / "pred" / "schedule.csv"
df_schedule_raw = pd.read_csv(path_schedule, encoding="cp932")
df_schedule = df_schedule_raw.copy()
list_race_id = df_schedule.loc[df_schedule["status"] == "本予測待ち", "race_id"].tolist()
list_race_id = [str(x) for x in list_race_id]
print(list_race_id)
# レースデータ取得とファイル出力
if len(list_race_id) > 0:
    # レースデータ取得
    scraper = NetkeibaScraper()
    df_race_data = scraper.get_nar_race_data_by_race_id(login_id=LOGIN_ID, password=PASSWORD, mode=MODE, list_race_id=list_race_id)
    # ファイル出力
    for race_id in list_race_id:
        path_shutuba = Path.cwd().parent.parent / "data" / "shutuba" / f"shutuba_{race_id}.csv"
        df_race_data[df_race_data["race_id"] == race_id].to_csv(path_shutuba, index=False, encoding="cp932")


