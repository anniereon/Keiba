# %%
### インポート ###

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from datetime import datetime
import time
from selenium.webdriver.common.keys import Keys
import re
import csv
import pandas as pd
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import List, TypeVar, Generic
import json
import os
import logging
import functools
from pathlib import Path
import sys

# %%
### 定数 ###

# ログ
# logging.basicConfig(
#     level=logging.INFO,
#     format='%(asctime)s - %(levelname)s - %(message)s',
#     filename=f"C:\\keiba\\tool\\log\\{datetime.now().strftime('%Y%m%d_app.log')}",
#     encoding='utf-8',
#     force=True
# )
# 設定ファイル読み込み
config_path = Path.cwd().parent / "config.xlsx"
df_config_racecourse = pd.read_excel(config_path, sheet_name="racecourse", header=0)
df_config_style = pd.read_excel(config_path, sheet_name="style", header=0)
df_config_scrape = pd.read_excel(config_path, sheet_name="scrape", header=None, index_col=0)
df_config_netkeiba = pd.read_excel(config_path, sheet_name="netkeiba", header=None, index_col=0)
# 対象競馬場とレース
PLACE_MAP = df_config_racecourse.set_index('key')['value'].to_dict()
print(f"競馬場: {PLACE_MAP}")
# 脚質
STYLE_MAP = df_config_style.set_index('key')['value'].to_dict()
print(f"脚質: {STYLE_MAP}")
# レース番号
RACE_NUMBERS = [f"{i:02d}" for i in range(1, 13)]
# スクレイピング
PATH_CHROME_DRIVER = df_config_scrape.loc["PATH_CHROME_DRIVER"].iloc[0]
# netkeiba
LOGIN_URL = df_config_netkeiba.loc["LOGIN_URL"].iloc[0]
LOGIN_ID = df_config_netkeiba.loc["LOGIN_ID"].iloc[0]
LOGIN_PASSWORD = df_config_netkeiba.loc["LOGIN_PASSWORD"].iloc[0]
# 天気
LIST_WEATHER = ["小雨", "小雪", "晴", "雨", "曇", "雪"]
# 馬場
LIST_TRACK_CONDITION = ["重", "不", "良", "稍"]

# %%
### 関数 ###
def log_step(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # メソッド開始のログ
        logging.info(f"[開始] {func.__name__} を実行します。")
        
        try:
            # 本来のメソッド（関数）を実行
            result = func(*args, **kwargs)
            
            # メソッド終了のログ
            logging.info(f"[完了] {func.__name__} が正常に終了しました。")
            return result
            
        except Exception as e:
            # エラー発生時のログ
            logging.error(f"[失敗] {func.__name__} でエラーが発生しました: {e}")
            raise  # エラーをそのまま上に投げる
            
    return wrapper

# %%
#########################
# historyファイルを開く
#########################

path_history = Path.cwd().parent.parent / "data" / "history" / "history.csv"
df_history = pd.read_csv(path_history, encoding="cp932")
# 型変換
df_history["race_id"] = df_history["race_id"].astype(str)

# %%
df_history["race_id"]

# %%
#########################
# databaseファイルを開く
#########################

# ファイルを開く
path_database = Path.cwd().parent.parent / "data" / "database" / "database.csv"
df_database = pd.read_csv(path_database, encoding="cp932")
# 型変換
df_database["race_id"] = df_database["race_id"].astype(str).str.replace(r'\.0$', '', regex=True)

# %%
df_database["race_id"]

# %%
###################################################
# databaseでhistoryを更新する
###################################################

# 更新対象のレコードを切り出す
last_idx = df_history['time_index'].last_valid_index()
df_to_update = df_history.loc[last_idx + 1:].copy()
# レースID
list_race_id = df_to_update['race_id'].unique().tolist()
print(list_race_id)
df_new_data = df_database[df_database["race_id"].isin(list_race_id)]

# %%
# 更新すべきrace_idが存在する場合はdatabaseを参照して更新
if len(df_new_data) > 0:
    # 型変換
    df_history['race_id'] = df_history['race_id'].astype(str)
    df_history['horse_number'] = df_history['horse_number'].astype(str)
    df_new_data['race_id'] = df_new_data['race_id'].astype(str)
    df_new_data['horse_number'] = df_new_data['horse_number'].astype(str)
    df_new_data['time_index'] = pd.to_numeric(df_new_data['time_index'], errors='coerce')
    # 更新
    df_history.set_index(['race_id', 'horse_number'], inplace=True)
    df_new_data.set_index(['race_id', 'horse_number'], inplace=True)
    df_history.update(df_new_data[['time_index', 'position_1', 'position_2', 'position_3', 'position_4', 'weather_name', 'track_condition_name']])
    df_history.reset_index(inplace=True)
    # CSV出力
    df_history.to_csv(path_history, index=False, encoding="cp932")


