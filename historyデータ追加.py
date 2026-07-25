# %%
### インポート ###

import numpy as np
import pandas as pd
from datetime import datetime
from pathlib import Path
import csv
# import sys

# %%
### ファイルを開く ###

today_str = datetime.now().strftime('%Y%m%d')
# today_str = "20260614"
path_history = Path.cwd().parent.parent / "data" / "history" / "history.csv"
path_shutuba = Path.cwd().parent.parent / "data" / "shutuba" / f"shutuba_{today_str}.csv"
path_result = Path.cwd().parent.parent / "data" / "result" / f"result_{today_str}.csv"
df_history_raw = pd.read_csv(path_history, encoding="cp932")
df_shutuba_raw = pd.read_csv(path_shutuba, encoding="cp932")
df_result_raw = pd.read_csv(path_result, encoding="cp932")
df_history = df_history_raw.copy()
df_shutuba = df_shutuba_raw.copy()
df_result = df_result_raw.copy()

# %%
### resultにnote列を追加 ###

df_result['finish_rank'] = df_result['finish_rank'].astype(str)
# note列に追加する文字列を設定
conditions = [
    df_result['finish_rank'].str.contains('取', na=False),
    df_result['finish_rank'].str.contains('中', na=False),
    df_result['finish_rank'].str.contains('失', na=False),
    df_result['finish_rank'].str.contains('除', na=False)
]
chars = ['取', '中', '失', '除']
# note列を追加する位置をfinish_rankの右に設定
idx_note = df_result.columns.get_loc('finish_rank') + 1
# note列を作成
df_result.insert(idx_note, 'note', np.select(conditions, chars, default=""))
# finish_rankから文字列を削除
df_result['finish_rank'] = np.select(conditions, ["", "", "", ""], default=df_result['finish_rank'])

# %%
### メイン処理 ###

# shutubaファイルとresultファイルを結合
target_cols_shutuba = [
"race_id",
"horse_number",
"position_1_top_pred",
"position_1_left_pred",
"position_2_top_pred",
"position_2_left_pred",
"position_3_top_pred",
"position_3_left_pred",
"position_4_top_pred",
"position_4_left_pred",
"position_1_top_pred_jockey_tendency",
"position_1_left_pred_jockey_tendency",
"position_2_top_pred_jockey_tendency",
"position_2_left_pred_jockey_tendency",
"position_3_top_pred_jockey_tendency",
"position_3_left_pred_jockey_tendency",
"position_4_top_pred_jockey_tendency",
"position_4_left_pred_jockey_tendency",
"style_pred",
"last_3_furlongs_pred",
]
df_result_and_shutuba = pd.merge(df_result, df_shutuba[target_cols_shutuba], on=['race_id', 'horse_number'])
# historyファイルと結合
df_merged = pd.concat([df_history, df_result_and_shutuba], axis=0, ignore_index=True)

# %%
### CSV出力 ###

df_merged.to_csv(path_history, index=False, encoding="cp932")


