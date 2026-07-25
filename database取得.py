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

def is_xpath_present(driver, xpath):
    return len(driver.find_elements(By.XPATH, xpath)) > 0

def extract_style_values(style_str):
    """
    style文字列からtopとleftの数値を抽出する関数
    """
    # 正規表現の解説:
    # -?    : マイナス記号があってもなくても良い
    # [\d\.]+ : 数字またはドットが1回以上続く
    # ()    : このカッコ内の部分を抽出する
    top_match = re.search(r"top:\s*(-?[\d\.]+)%", style_str)
    left_match = re.search(r"left:\s*(-?[\d\.]+)%", style_str)
    # 抽出した文字列をfloatに変換
    top_val = float(top_match.group(1)) if top_match else None
    left_val = float(left_match.group(1)) if left_match else None
    # 戻り値
    return top_val, left_val

@log_step
def login_netkeiba(driver):
    try:
        driver.get(LOGIN_URL)
    except:
        print("タイムアウトしたが処理を継続")
        driver.execute_script("window.stop();")
    driver.find_element(By.NAME, "login_id").send_keys(LOGIN_ID)
    pw_field = driver.find_element(By.NAME, "pswd")
    pw_field.send_keys(LOGIN_PASSWORD)
    pw_field.send_keys(Keys.ENTER)
    time.sleep(3)

@log_step
def get_wether_and_track_condition(condition_data):

    weather = next((k for k in LIST_WEATHER if k in condition_data), "")
    track_condition = next((k for k in LIST_TRACK_CONDITION if k in condition_data), "")

    return weather, track_condition

@log_step
def get_data_from_database(driver, list_race_info):

    list_horse_data = []
    for race_id, race_date, race_number, racecourse in list_race_info:
        # レースページのURL
        url_race = f"https://db.netkeiba.com/race/{race_id}/"
        # リトライ回数の上限を設定
        max_retries = 5
        # 失敗した場合は上限までリトライする
        flg_success = False
        for attempt in range(1, max_retries + 1):
            try:
                # レースページに遷移
                driver.get(url_race)
                # レース単位のデータを取得
                condition_data = driver.find_element(By.XPATH, "//*[@id='main']/div/div/div/diary_snap/div/div/dl/dd/p/diary_snap_cut/span").text
                weather_name, track_condition_name = get_wether_and_track_condition(condition_data)
                # 馬単位のデータを取得
                for i in range(19):
                    if is_xpath_present(driver, f"//*[@id='contents_liquid']/table/tbody/tr[{str(i + 2)}]/td[3]"):
                        horse_number = driver.find_element(By.XPATH, f"//*[@id='contents_liquid']/table/tbody/tr[{str(i + 2)}]/td[3]").text
                        time_index = driver.find_element(By.XPATH, f"//*[@id='contents_liquid']/table/tbody/tr[{str(i + 2)}]/td[10]").text
                        position = driver.find_element(By.XPATH, f"//*[@id='contents_liquid']/table/tbody/tr[{str(i + 2)}]/td[15]").text
                        position_parts = position.split('-')
                        position_parts = (position_parts + [""] * 4)[:4]
                        position_1, position_2, position_3, position_4 = position_parts
                        horse_data = {
                            "race_id": race_id,
                            "race_date": race_date,
                            "race_number": race_number,
                            "racecourse": racecourse,
                            "horse_number": horse_number,
                            "time_index": time_index,
                            "position_1": position_1,
                            "position_2": position_2,
                            "position_3": position_3,
                            "position_4": position_4,
                            "weather_name": weather_name,
                            "track_condition_name": track_condition_name
                        }
                        list_horse_data.append(horse_data)
                    else:
                        # 馬単位のデータを取得ループを抜ける
                        break
                # 成功
                print(f"【〇】レースID：{race_id} {attempt}回目")
                flg_success = True
                # リトライループを抜ける
                break
            except:
                # 失敗
                if attempt < max_retries:
                    print(f"【✕】レースID：{race_id} {attempt}回目")
                elif attempt == max_retries:
                    print(f"【✕】レースID：{race_id} リトライ回数の上限に到達")
                    driver.quit()
                    return pd.DataFrame(list_horse_data)
                
    return pd.DataFrame(list_horse_data)

# %%
#########################
# historyファイルを開く
#########################

path_history = Path.cwd().parent.parent / "data" / "history" / "history.csv"
df_history = pd.read_csv(path_history, encoding="cp932")

# %%
#########################
# databaseファイルを開く
#########################

path_database = Path.cwd().parent.parent / "data" / "database" / "database.csv"
df_database = pd.read_csv(path_database, encoding="cp932")
df_database = df_database.iloc[0:0]

# %%
###################################################
# netkeibaから最新データを取得してdatabaseを更新する
###################################################

# 更新対象のレコードを切り出す
last_idx = df_history['time_index'].last_valid_index()
df_to_update = df_history.loc[last_idx + 1:].copy()
# レースID
list_race_info = df_to_update[['race_id', 'race_date', 'race_number', 'racecourse']].drop_duplicates().values.tolist()
# 更新すべきrace_idが存在する場合はnetkeibaからデータ取得
if list_race_info:
    # スクレイピング準備
    service = Service(PATH_CHROME_DRIVER)
    options = webdriver.ChromeOptions()
    # options.add_argument('--headless')
    driver = webdriver.Chrome(service=service, options=options)
    # タイムアウト設定
    driver.set_page_load_timeout(30)
    # ログイン
    login_netkeiba(driver)
    # データベースからデータ取得
    df_database_new = get_data_from_database(driver, list_race_info)
    # スクレイピング終了
    driver.quit()
    # 型変換
    df_database_new["race_id"] = df_database_new["race_id"].astype(str)
    df_database_new["horse_number"] = df_database_new["horse_number"].astype(str)
    df_database_new['time_index'] = pd.to_numeric(df_database_new['time_index'], errors='coerce')
    # マージ
    df_merged = pd.concat([df_database, df_database_new], axis=0, ignore_index=True)
    # CSV出力
    df_merged.to_csv(path_database, index=False, encoding="cp932")


