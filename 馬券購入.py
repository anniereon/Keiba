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
import numpy as np
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import List, TypeVar, Generic
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pathlib import Path
import sys

# %%
# =====
# 設定
# =====

### 設定ファイル ###
config_path = Path.cwd().parent / "config.xlsx"
df_config_racecourse = pd.read_excel(config_path, sheet_name="racecourse", header=0)
df_config_style = pd.read_excel(config_path, sheet_name="style", header=0)
df_spat4 = pd.read_excel(config_path, sheet_name="spat4", header=0)
df_purchase = pd.read_excel(config_path, sheet_name="purchase", header=0)
df_config_scrape = pd.read_excel(config_path, sheet_name="scrape", header=None, index_col=0)
df_config_netkeiba = pd.read_excel(config_path, sheet_name="netkeiba", header=None, index_col=0)
df_config_gmail = pd.read_excel(config_path, sheet_name="gmail", header=0)
# 対象競馬場とレース
PLACE_MAP = df_config_racecourse.set_index('key')['value'].to_dict()
print(f"競馬場: {df_config_gmail}")
# 脚質
STYLE_MAP = df_config_style.set_index('key')['value'].to_dict()
print(f"脚質: {STYLE_MAP}")
# spat4
SPAT4_MAP = df_spat4.set_index('key')['value'].to_dict()
# 購入フラグ
PURCHASE_MAP = df_purchase.set_index('key')['value'].to_dict()
print(f'購入フラグ: {PURCHASE_MAP}')
# gmail
GMAIL_MAP = df_config_gmail.set_index('key')['value'].to_dict()
# print(f'gmail設定: {GMAIL_MAP}')
# スクレイピング
PATH_CHROME_DRIVER = df_config_scrape.loc["PATH_CHROME_DRIVER"].iloc[0]
# netkeiba
MODE_NETKEIBA = "shutuba"
LOGIN_URL = df_config_netkeiba.loc["LOGIN_URL"].iloc[0]
LOGIN_ID = df_config_netkeiba.loc["LOGIN_ID"].iloc[0]
LOGIN_PASSWORD = df_config_netkeiba.loc["LOGIN_PASSWORD"].iloc[0]
RACE_LIST_URL = df_config_netkeiba.loc["RACE_LIST_URL"].iloc[0]
MAX_RETRY_NUM = df_config_netkeiba.loc["MAX_RETRY_NUM"].iloc[0]
# レース単位
print(f"MODE_NETKEIBA: {MODE_NETKEIBA}")
if MODE_NETKEIBA == "shutuba":
    SELECTOR_RACECOURSE = df_config_netkeiba.loc["SELECTOR_RACECOURSE_SHUTUBA"].iloc[0]
    SELECTOR_RACE_NUMBER = df_config_netkeiba.loc["SELECTOR_RACE_NUMBER_SHUTUBA"].iloc[0]
    SELECTOR_NUM_HORSES = df_config_netkeiba.loc["SELECTOR_NUM_HORSES_SHUTUBA"].iloc[0]
    XPATH_RACE_INFO = df_config_netkeiba.loc["XPATH_RACE_INFO_SHUTUBA"].iloc[0]
elif MODE_NETKEIBA == "result":
    SELECTOR_RACECOURSE = df_config_netkeiba.loc["SELECTOR_RACECOURSE_RESULT"].iloc[0]
    SELECTOR_RACE_NUMBER = df_config_netkeiba.loc["SELECTOR_RACE_NUMBER_RESULT"].iloc[0]
    SELECTOR_NUM_HORSES = df_config_netkeiba.loc["SELECTOR_NUM_HORSES_RESULT"].iloc[0]
    XPATH_RACE_INFO = df_config_netkeiba.loc["XPATH_RACE_INFO_RESULT"].iloc[0]
XPATH_RELIABILITY = df_config_netkeiba.loc["XPATH_RELIABILITY"].iloc[0]
XPATH_OPINION = df_config_netkeiba.loc["XPATH_OPINION"].iloc[0]
XPATH_CORNER_1 = df_config_netkeiba.loc["XPATH_CORNER_1"].iloc[0]
XPATH_CORNER_2 = df_config_netkeiba.loc["XPATH_CORNER_2"].iloc[0]
XPATH_CORNER_3 = df_config_netkeiba.loc["XPATH_CORNER_3"].iloc[0]
XPATH_RANK_1_CORNER = df_config_netkeiba.loc["XPATH_RANK_1_CORNER"].iloc[0]
XPATH_RANK_2_CORNER = df_config_netkeiba.loc["XPATH_RANK_2_CORNER"].iloc[0]
XPATH_RANK_3_CORNER = df_config_netkeiba.loc["XPATH_RANK_3_CORNER"].iloc[0]
XPATH_RANK_4_CORNER = df_config_netkeiba.loc["XPATH_RANK_4_CORNER"].iloc[0]
# 馬単位（shutuba）
XPATH_HORSE_NUMBER_1_SHUTUBA = df_config_netkeiba.loc["XPATH_HORSE_NUMBER_1_SHUTUBA"].iloc[0]
XPATH_HORSE_NUMBER_2_SHUTUBA = df_config_netkeiba.loc["XPATH_HORSE_NUMBER_2_SHUTUBA"].iloc[0]
XPATH_HORSE_LINK_1_1_SHUTUBA = df_config_netkeiba.loc["XPATH_HORSE_LINK_1_1_SHUTUBA"].iloc[0]
XPATH_HORSE_LINK_1_2_SHUTUBA = df_config_netkeiba.loc["XPATH_HORSE_LINK_1_2_SHUTUBA"].iloc[0]
XPATH_HORSE_LINK_2_1_SHUTUBA = df_config_netkeiba.loc["XPATH_HORSE_LINK_2_1_SHUTUBA"].iloc[0]
XPATH_HORSE_LINK_2_2_SHUTUBA = df_config_netkeiba.loc["XPATH_HORSE_LINK_2_2_SHUTUBA"].iloc[0]
XPATH_JOCKEY_LINK_1_SHUTUBA = df_config_netkeiba.loc["XPATH_JOCKEY_LINK_1_SHUTUBA"].iloc[0]
XPATH_JOCKEY_LINK_2_SHUTUBA = df_config_netkeiba.loc["XPATH_JOCKEY_LINK_2_SHUTUBA"].iloc[0]
XPATH_POPULARITY_1_SHUTUBA = df_config_netkeiba.loc["XPATH_POPULARITY_1_SHUTUBA"].iloc[0]
XPATH_POPULARITY_2_SHUTUBA = df_config_netkeiba.loc["XPATH_POPULARITY_2_SHUTUBA"].iloc[0]
XPATH_ODDS_1_SHUTUBA = df_config_netkeiba.loc["XPATH_ODDS_1_SHUTUBA"].iloc[0]
XPATH_ODDS_2_SHUTUBA = df_config_netkeiba.loc["XPATH_ODDS_2_SHUTUBA"].iloc[0]
XPATH_IMPOSE_1_SHUTUBA = df_config_netkeiba.loc["XPATH_IMPOSE_1_SHUTUBA"].iloc[0]
XPATH_IMPOSE_2_SHUTUBA = df_config_netkeiba.loc["XPATH_IMPOSE_2_SHUTUBA"].iloc[0]
XPATH_FRAME_1_SHUTUBA = df_config_netkeiba.loc["XPATH_FRAME_1_SHUTUBA"].iloc[0]
XPATH_FRAME_2_SHUTUBA = df_config_netkeiba.loc["XPATH_FRAME_2_SHUTUBA"].iloc[0]
XPATH_WEIGHT_1_SHUTUBA = df_config_netkeiba.loc["XPATH_WEIGHT_1_SHUTUBA"].iloc[0]
XPATH_WEIGHT_2_SHUTUBA = df_config_netkeiba.loc["XPATH_WEIGHT_2_SHUTUBA"].iloc[0]
XPATH_SEX_AND_AGE_1_SHUTUBA = df_config_netkeiba.loc["XPATH_SEX_AND_AGE_1_SHUTUBA"].iloc[0]
XPATH_SEX_AND_AGE_2_SHUTUBA = df_config_netkeiba.loc["XPATH_SEX_AND_AGE_2_SHUTUBA"].iloc[0]
XPATH_LAST_3_FURLONGS_PRED_1_SHUTUBA = df_config_netkeiba.loc["XPATH_LAST_3_FURLONGS_PRED_1_SHUTUBA"].iloc[0]
XPATH_LAST_3_FURLONGS_PRED_2_SHUTUBA = df_config_netkeiba.loc["XPATH_LAST_3_FURLONGS_PRED_2_SHUTUBA"].iloc[0]
# 馬単位（result）
XPATH_FINISH_RANK_1_RESULT = df_config_netkeiba.loc["XPATH_FINISH_RANK_1_RESULT"].iloc[0]
XPATH_FINISH_RANK_2_RESULT = df_config_netkeiba.loc["XPATH_FINISH_RANK_2_RESULT"].iloc[0]
XPATH_FRAME_NUMBER_1_RESULT = df_config_netkeiba.loc["XPATH_FRAME_NUMBER_1_RESULT"].iloc[0]
XPATH_FRAME_NUMBER_2_RESULT = df_config_netkeiba.loc["XPATH_FRAME_NUMBER_2_RESULT"].iloc[0]
XPATH_HORSE_NUMBER_1_RESULT = df_config_netkeiba.loc["XPATH_HORSE_NUMBER_1_RESULT"].iloc[0]
XPATH_HORSE_NUMBER_2_RESULT = df_config_netkeiba.loc["XPATH_HORSE_NUMBER_2_RESULT"].iloc[0]
XPATH_HORSE_LINK_1_RESULT = df_config_netkeiba.loc["XPATH_HORSE_LINK_1_RESULT"].iloc[0]
XPATH_HORSE_LINK_2_RESULT = df_config_netkeiba.loc["XPATH_HORSE_LINK_2_RESULT"].iloc[0]
XPATH_SEX_AND_AGE_1_RESULT = df_config_netkeiba.loc["XPATH_SEX_AND_AGE_1_RESULT"].iloc[0]
XPATH_SEX_AND_AGE_2_RESULT = df_config_netkeiba.loc["XPATH_SEX_AND_AGE_2_RESULT"].iloc[0]
XPATH_IMPOSE_1_RESULT = df_config_netkeiba.loc["XPATH_IMPOSE_1_RESULT"].iloc[0]
XPATH_IMPOSE_2_RESULT = df_config_netkeiba.loc["XPATH_IMPOSE_2_RESULT"].iloc[0]
XPATH_JOCKEY_LINK_1_RESULT = df_config_netkeiba.loc["XPATH_JOCKEY_LINK_1_RESULT"].iloc[0]
XPATH_JOCKEY_LINK_2_RESULT = df_config_netkeiba.loc["XPATH_JOCKEY_LINK_2_RESULT"].iloc[0]
XPATH_TIME_1_RESULT = df_config_netkeiba.loc["XPATH_TIME_1_RESULT"].iloc[0]
XPATH_TIME_2_RESULT = df_config_netkeiba.loc["XPATH_TIME_2_RESULT"].iloc[0]
XPATH_DIFF_1_RESULT = df_config_netkeiba.loc["XPATH_DIFF_1_RESULT"].iloc[0]
XPATH_DIFF_2_RESULT = df_config_netkeiba.loc["XPATH_DIFF_2_RESULT"].iloc[0]
XPATH_POPULARITY_1_RESULT = df_config_netkeiba.loc["XPATH_POPULARITY_1_RESULT"].iloc[0]
XPATH_POPULARITY_2_RESULT = df_config_netkeiba.loc["XPATH_POPULARITY_2_RESULT"].iloc[0]
XPATH_ODDS_1_RESULT = df_config_netkeiba.loc["XPATH_ODDS_1_RESULT"].iloc[0]
XPATH_ODDS_2_RESULT = df_config_netkeiba.loc["XPATH_ODDS_2_RESULT"].iloc[0]
XPATH_LAST_3_FURLONGS_1_RESULT = df_config_netkeiba.loc["XPATH_LAST_3_FURLONGS_1_RESULT"].iloc[0]
XPATH_LAST_3_FURLONGS_2_RESULT = df_config_netkeiba.loc["XPATH_LAST_3_FURLONGS_2_RESULT"].iloc[0]
XPATH_WEIGHT_1_RESULT = df_config_netkeiba.loc["XPATH_WEIGHT_1_RESULT"].iloc[0]
XPATH_WEIGHT_2_RESULT = df_config_netkeiba.loc["XPATH_WEIGHT_2_RESULT"].iloc[0]

# %%
### クラス ###

# 馬データ（Shutuba）
@dataclass
class Horse_Shutuba:
    """出走馬のデータを保持するデータクラス"""
    horse_id: str
    horse_name: str
    jockey_id: str
    jockey_name: str
    popularity: str
    odds: str
    sex_and_age: str
    weight: str
    horse_number: str
    frame_number: str
    position_1_top_pred: str
    position_1_left_pred: str
    position_2_top_pred: str
    position_2_left_pred: str
    position_3_top_pred: str
    position_3_left_pred: str
    position_4_top_pred: str
    position_4_left_pred: str 
    position_1_top_pred_jockey_tendency: str
    position_1_left_pred_jockey_tendency: str
    position_2_top_pred_jockey_tendency: str
    position_2_left_pred_jockey_tendency: str
    position_3_top_pred_jockey_tendency: str
    position_3_left_pred_jockey_tendency: str
    position_4_top_pred_jockey_tendency: str
    position_4_left_pred_jockey_tendency: str
    style_pred: str
    impost: str
    last_3_furlongs_pred: str

# 馬データ（Result）
@dataclass
class Horse_Result:
    """出走馬のデータを保持するデータクラス"""
    finish_rank: str
    frame_number: str
    horse_number: str
    horse_id: str
    horse_name: str
    sex_and_age: str
    impost: str    
    jockey_id: str
    jockey_name: str
    time: str
    diff: str    
    popularity: str
    odds: str
    last_3_furlongs: str
    weight: str

# レースデータ（Shutuba）
T = TypeVar('T')
@dataclass
class Race:
    """レースの基本情報と出走馬リストを保持するデータクラス"""
    race_id: str
#    race_name: str
    race_date: str
    race_time: str
    num_horses: str
    race_number: int
#    weather_name: str
#    track_condition_name: str
    racecourse: str
    ground: str
    distance: str
    direction:  str
    reliability: str
    opinion: str
    rank_1_corner: str
    rank_2_corner: str
    rank_3_corner: str
    rank_4_corner: str    
    horses: List[T] = field(default_factory=list)

# %%
# ========
# メソッド
# ========

def is_xpath_present(driver, xpath):
    return len(driver.find_elements(By.XPATH, xpath)) > 0

def extract_style_values(style_str):
    """
    style文字列からtopとleftの数値を抽出する関数（マイナス対応版）
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
    
    return top_val, left_val

def get_position_pred(driver):
    # HorseIconクラスを持つすべての要素を取得（リスト形式で返ってくる）
    position_pred_elements = driver.find_elements(By.CLASS_NAME, "HorseIcon")
    # 結果を格納する辞書
    dic_position_pred = {}
    for element in position_pred_elements:
        horse_number = element.get_attribute("id")
        position_pred = element.get_attribute("style")
        top_val, left_val = extract_style_values(position_pred)
        dic_val = {}
        dic_val["top"] = top_val
        dic_val["left"] = left_val
        # idが空でない場合のみ追加
        if horse_number:
            dic_position_pred[horse_number] = dic_val
    # 戻り値
    return dic_position_pred

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

def login_spat4(driver):
    try:
        driver.get(SPAT4_MAP.get('LOGIN_URL'))
    except:
        print("タイムアウトしたが処理を継続")
        driver.execute_script("window.stop();")
    driver.find_element(By.XPATH, "//*[@id='MEMBERNUMR']").send_keys(SPAT4_MAP.get('加入者番号'))
    driver.find_element(By.XPATH, "//*[@id='MEMBERIDR']").send_keys(SPAT4_MAP.get('利用者ID'))
    driver.find_element(By.XPATH, "/html/body/div/div[1]/form/a/span/div").click()
    time.sleep(3)

def scrape_horse_shutuba_data(driver, num_horses):
    
    all_horses_data = []
    # 馬番・馬名取得
    # 馬番・馬名・馬名リンク取得
    for i in range(1, num_horses + 1):
        try:
            # 馬番
            xpath_horse_number = XPATH_HORSE_NUMBER_1_SHUTUBA + str(i) + XPATH_HORSE_NUMBER_2_SHUTUBA
            if is_xpath_present(driver, xpath_horse_number): # 通常通り出走
                horse_number = driver.find_element(By.XPATH, xpath_horse_number).text.strip()
            elif is_xpath_present(driver, f"//*[@id='Netkeiba_Race_Nar_Shutuba']/div[1]/div[3]/div[3]/table/tbody/tr[{str(i)}]/td[2]"): # 取消等
                horse_number = driver.find_element(By.XPATH, f"//*[@id='Netkeiba_Race_Nar_Shutuba']/div[1]/div[3]/div[3]/table/tbody/tr[{str(i)}]/td[2]").text.strip()
                horse_data = Horse_Shutuba(
                    horse_id = None,
                    horse_name = None,
                    jockey_id = None,
                    jockey_name = None,
                    popularity = None,
                    odds = None,
                    sex_and_age = None,
                    weight = None,
                    horse_number = horse_number,
                    frame_number = None,
                    position_1_top_pred = None,
                    position_1_left_pred = None,
                    position_2_top_pred = None,
                    position_2_left_pred = None,
                    position_3_top_pred = None,
                    position_3_left_pred = None,
                    position_4_top_pred = None,
                    position_4_left_pred = None,
                    position_1_top_pred_jockey_tendency = None,
                    position_1_left_pred_jockey_tendency = None,
                    position_2_top_pred_jockey_tendency = None,
                    position_2_left_pred_jockey_tendency = None,
                    position_3_top_pred_jockey_tendency = None,
                    position_3_left_pred_jockey_tendency = None,
                    position_4_top_pred_jockey_tendency = None,
                    position_4_left_pred_jockey_tendency = None,
                    style_pred = None,
                    impost = None,
                    last_3_furlongs_pred = None
                )
                all_horses_data.append(horse_data)
                continue
            else:
                break
            # 馬名と馬ID
            xpath_horse_link_1 = XPATH_HORSE_LINK_1_1_SHUTUBA + str(i) + XPATH_HORSE_LINK_1_2_SHUTUBA
            xpath_horse_link_2 = XPATH_HORSE_LINK_2_1_SHUTUBA + str(i) + XPATH_HORSE_LINK_2_2_SHUTUBA
            if is_xpath_present(driver, xpath_horse_link_1):
                xpath_horse_link = xpath_horse_link_1
            elif is_xpath_present(driver, xpath_horse_link_2):
                xpath_horse_link = xpath_horse_link_2
            horse_link_elem = driver.find_element(By.XPATH, xpath_horse_link)
            horse_name = horse_link_elem.text.strip()
            horse_href = horse_link_elem.get_attribute("href")
            horse_id = horse_href.rstrip("/").split("/")[-1]
            # 騎手名と騎手ID
            xpath_jockey_link = XPATH_JOCKEY_LINK_1_SHUTUBA + str(i) + XPATH_JOCKEY_LINK_2_SHUTUBA
            jockey_link_elem = driver.find_element(By.XPATH, xpath_jockey_link)
            jockey_name = jockey_link_elem.text.strip()
            jockey_href = jockey_link_elem.get_attribute("href")
            jockey_id = jockey_href.rstrip("/").split("/")[-1]
            # 人気
            xpath_popularity = XPATH_POPULARITY_1_SHUTUBA + str(i) + XPATH_POPULARITY_2_SHUTUBA
            popularity = driver.find_element(By.XPATH, xpath_popularity).text
            # オッズ
            xpath_odds = XPATH_ODDS_1_SHUTUBA + str(i) + XPATH_ODDS_2_SHUTUBA
            odds = driver.find_element(By.XPATH, xpath_odds).text
            # 性齢
            xpath_sex_and_age = XPATH_SEX_AND_AGE_1_SHUTUBA + str(i) + XPATH_SEX_AND_AGE_2_SHUTUBA
            sex_and_age = driver.find_element(By.XPATH, xpath_sex_and_age).text
            # 馬体重
            xpath_weight = XPATH_WEIGHT_1_SHUTUBA + str(i) + XPATH_WEIGHT_2_SHUTUBA
            weight = driver.find_element(By.XPATH, xpath_weight).text
            # 枠番
            xpath_frame_number = XPATH_FRAME_1_SHUTUBA + str(i) + XPATH_FRAME_2_SHUTUBA
            frame_number = driver.find_element(By.XPATH, xpath_frame_number).text
            # 斤量
            xpath_impost = XPATH_IMPOSE_1_SHUTUBA + str(i) + XPATH_IMPOSE_2_SHUTUBA
            impost = driver.find_element(By.XPATH, xpath_impost).text
            # 後半3F
            xpath_last_3_furlongs_pred = XPATH_LAST_3_FURLONGS_PRED_1_SHUTUBA + str(i) + XPATH_LAST_3_FURLONGS_PRED_2_SHUTUBA
            if is_xpath_present(driver, xpath_last_3_furlongs_pred):
                last_3_furlongs_pred = driver.find_element(By.XPATH, xpath_last_3_furlongs_pred).text
            else:
                last_3_furlongs_pred = None
            # 馬データ作成
            horse_data = Horse_Shutuba(
                horse_id = horse_id,
                horse_name = horse_name,
                jockey_id = jockey_id,
                jockey_name = jockey_name,
                popularity = popularity,
                odds = odds,
                sex_and_age = sex_and_age,
                weight = weight,
                horse_number = horse_number,
                frame_number = frame_number,
                position_1_top_pred = None,
                position_1_left_pred = None,
                position_2_top_pred = None,
                position_2_left_pred = None,
                position_3_top_pred = None,
                position_3_left_pred = None,
                position_4_top_pred = None,
                position_4_left_pred = None,
                position_1_top_pred_jockey_tendency = None,
                position_1_left_pred_jockey_tendency = None,
                position_2_top_pred_jockey_tendency = None,
                position_2_left_pred_jockey_tendency = None,
                position_3_top_pred_jockey_tendency = None,
                position_3_left_pred_jockey_tendency = None,
                position_4_top_pred_jockey_tendency = None,
                position_4_left_pred_jockey_tendency = None,
                style_pred = None,
                impost = impost,
                last_3_furlongs_pred = last_3_furlongs_pred
            )
            
            all_horses_data.append(horse_data)
        except Exception as e:
            print(f"  馬番{i}: データ取得失敗 ({e})")
    # 戻り値
    return all_horses_data

def scrape_race_data(driver, race_id, date):

    try:
        # 競馬場
        racecourse = driver.find_element(By.CSS_SELECTOR, SELECTOR_RACECOURSE).text
        # R
        race_number = driver.find_element(By.CSS_SELECTOR, SELECTOR_RACE_NUMBER).text
        # 頭数
        num_horses = driver.find_element(By.CSS_SELECTOR, SELECTOR_NUM_HORSES).text
        num_horses = int(num_horses.replace("頭", "").strip())
        # レース情報（発走時刻、グラウンド、距離、向き）
        race_info = driver.find_element(By.XPATH, XPATH_RACE_INFO).text
        race_info = race_info.strip()
        # "/"で分割
        parts = [p.strip() for p in race_info.split("/")]            
        # 発走時刻を抽出
        race_time = parts[0].replace("発走", "").strip()
        ground_info = parts[1]
        # グラウンドを抽出
        ground_match = re.search(r"(芝|ダ)", ground_info)
        ground = ground_match.group(1) if ground_match else "不明"
        # 距離を抽出
        distance_match = re.search(r"(\d+)m", ground_info)
        distance = int(distance_match.group(1)) if distance_match else -1
        # 向きを抽出
        direction_match = re.search(r"\((左|右)\)", ground_info)
        direction = direction_match.group(1) if direction_match else "不明"
        # 馬のデータを抽出
        if MODE_NETKEIBA == "shutuba":
            horse_list = scrape_horse_shutuba_data(driver, num_horses)
        elif MODE_NETKEIBA == "result":
            horse_list = scrape_horse_result_data(driver, num_horses)
        # 競馬場が帯広でない場合は予想データを取得する
        reliability = None
        opinion = None
        rank_1_corner = None
        rank_2_corner = None
        rank_3_corner = None
        rank_4_corner = None
        if MODE_NETKEIBA == "shutuba" and racecourse != "帯広(ば)":
            if is_xpath_present(driver, XPATH_CORNER_1):
                # 1人気信頼度
                if is_xpath_present(driver, XPATH_RELIABILITY):
                    reliability = driver.find_element(By.XPATH, XPATH_RELIABILITY).text
                # 見解
                if is_xpath_present(driver, XPATH_OPINION):
                    opinion = driver.find_element(By.XPATH, XPATH_OPINION).text
                # ポジション予想（1）
                corner = driver.find_element(By.XPATH, XPATH_CORNER_1).text
                dic_position_pred = get_position_pred(driver)
                match corner:
                    case "スタート後":
                        for horse in horse_list:
                            horse.position_1_top_pred = dic_position_pred[f'Horse{horse.horse_number}']["top"]
                            horse.position_1_left_pred = dic_position_pred[f'Horse{horse.horse_number}']["left"]
                    case "2コーナー":
                        for horse in horse_list:
                            horse.position_2_top_pred = dic_position_pred[f'Horse{horse.horse_number}']["top"]
                            horse.position_2_left_pred = dic_position_pred[f'Horse{horse.horse_number}']["left"]
                    case "3コーナー":
                        for horse in horse_list:
                            horse.position_3_top_pred = dic_position_pred[f'Horse{horse.horse_number}']["top"]
                            horse.position_3_left_pred = dic_position_pred[f'Horse{horse.horse_number}']["left"]
                    case "4コーナー":
                        for horse in horse_list:
                            horse.position_4_top_pred = dic_position_pred[f'Horse{horse.horse_number}']["top"]
                            horse.position_4_left_pred = dic_position_pred[f'Horse{horse.horse_number}']["left"]
                # ポジション予想（2）
                driver.find_element(By.XPATH, XPATH_CORNER_2).click()
                corner = driver.find_element(By.XPATH, XPATH_CORNER_2).text
                dic_position_pred = get_position_pred(driver)
                # ポジション予想を馬と紐づける
                match corner:
                    case "スタート後":
                        for horse in horse_list:
                            horse.position_1_top_pred = dic_position_pred[f'Horse{horse.horse_number}']["top"]
                            horse.position_1_left_pred = dic_position_pred[f'Horse{horse.horse_number}']["left"]
                    case "2コーナー":
                        for horse in horse_list:
                            horse.position_2_top_pred = dic_position_pred[f'Horse{horse.horse_number}']["top"]
                            horse.position_2_left_pred = dic_position_pred[f'Horse{horse.horse_number}']["left"]
                    case "3コーナー":
                        for horse in horse_list:
                            horse.position_3_top_pred = dic_position_pred[f'Horse{horse.horse_number}']["top"]
                            horse.position_3_left_pred = dic_position_pred[f'Horse{horse.horse_number}']["left"]
                    case "4コーナー":
                        for horse in horse_list:
                            horse.position_4_top_pred = dic_position_pred[f'Horse{horse.horse_number}']["top"]
                            horse.position_4_left_pred = dic_position_pred[f'Horse{horse.horse_number}']["left"]
                # ポジション予想（3）
                driver.find_element(By.XPATH, XPATH_CORNER_3).click()
                corner = driver.find_element(By.XPATH, XPATH_CORNER_3).text
                dic_position_pred = get_position_pred(driver)
                # ポジション予想を馬と紐づける
                match corner:
                    case "スタート後":
                        for horse in horse_list:
                            horse.position_1_top_pred = dic_position_pred[f'Horse{horse.horse_number}']["top"]
                            horse.position_1_left_pred = dic_position_pred[f'Horse{horse.horse_number}']["left"]
                    case "2コーナー":
                        for horse in horse_list:
                            horse.position_2_top_pred = dic_position_pred[f'Horse{horse.horse_number}']["top"]
                            horse.position_2_left_pred = dic_position_pred[f'Horse{horse.horse_number}']["left"]
                    case "3コーナー":
                        for horse in horse_list:
                            horse.position_3_top_pred = dic_position_pred[f'Horse{horse.horse_number}']["top"]
                            horse.position_3_left_pred = dic_position_pred[f'Horse{horse.horse_number}']["left"]
                    case "4コーナー":
                        for horse in horse_list:
                            horse.position_4_top_pred = dic_position_pred[f'Horse{horse.horse_number}']["top"]
                            horse.position_4_left_pred = dic_position_pred[f'Horse{horse.horse_number}']["left"]
                # 「騎手傾向を考慮」をチェック
                driver.find_element(By.XPATH, "//*[@id='dev_check_01_03']").click()
                # ポジション予想（1）
                driver.find_element(By.XPATH, XPATH_CORNER_1).click()
                corner = driver.find_element(By.XPATH, XPATH_CORNER_1).text
                dic_position_pred = get_position_pred(driver)
                match corner:
                    case "スタート後":
                        for horse in horse_list:
                            horse.position_1_top_pred_jockey_tendency = dic_position_pred[f'Horse{horse.horse_number}']["top"]
                            horse.position_1_left_pred_jockey_tendency = dic_position_pred[f'Horse{horse.horse_number}']["left"]
                    case "2コーナー":
                        for horse in horse_list:
                            horse.position_2_top_pred_jockey_tendency = dic_position_pred[f'Horse{horse.horse_number}']["top"]
                            horse.position_2_left_pred_jockey_tendency = dic_position_pred[f'Horse{horse.horse_number}']["left"]
                    case "3コーナー":
                        for horse in horse_list:
                            horse.position_3_top_pred_jockey_tendency = dic_position_pred[f'Horse{horse.horse_number}']["top"]
                            horse.position_3_left_pred_jockey_tendency = dic_position_pred[f'Horse{horse.horse_number}']["left"]
                    case "4コーナー":
                        for horse in horse_list:
                            horse.position_4_top_pred_jockey_tendency = dic_position_pred[f'Horse{horse.horse_number}']["top"]
                            horse.position_4_left_pred_jockey_tendency = dic_position_pred[f'Horse{horse.horse_number}']["left"]
                # ポジション予想（2）
                driver.find_element(By.XPATH, XPATH_CORNER_2).click()
                corner = driver.find_element(By.XPATH, XPATH_CORNER_2).text
                dic_position_pred = get_position_pred(driver)
                # ポジション予想を馬と紐づける
                match corner:
                    case "スタート後":
                        for horse in horse_list:
                            horse.position_1_top_pred_jockey_tendency = dic_position_pred[f'Horse{horse.horse_number}']["top"]
                            horse.position_1_left_pred_jockey_tendency = dic_position_pred[f'Horse{horse.horse_number}']["left"]
                    case "2コーナー":
                        for horse in horse_list:
                            horse.position_2_top_pred_jockey_tendency = dic_position_pred[f'Horse{horse.horse_number}']["top"]
                            horse.position_2_left_pred_jockey_tendency = dic_position_pred[f'Horse{horse.horse_number}']["left"]
                    case "3コーナー":
                        for horse in horse_list:
                            horse.position_3_top_pred_jockey_tendency = dic_position_pred[f'Horse{horse.horse_number}']["top"]
                            horse.position_3_left_pred_jockey_tendency = dic_position_pred[f'Horse{horse.horse_number}']["left"]
                    case "4コーナー":
                        for horse in horse_list:
                            horse.position_4_top_pred_jockey_tendency = dic_position_pred[f'Horse{horse.horse_number}']["top"]
                            horse.position_4_left_pred_jockey_tendency = dic_position_pred[f'Horse{horse.horse_number}']["left"]
                # ポジション予想（3）
                driver.find_element(By.XPATH, XPATH_CORNER_3).click()
                corner = driver.find_element(By.XPATH, XPATH_CORNER_3).text
                dic_position_pred = get_position_pred(driver)
                # ポジション予想を馬と紐づける
                match corner:
                    case "スタート後":
                        for horse in horse_list:
                            horse.position_1_top_pred_jockey_tendency = dic_position_pred[f'Horse{horse.horse_number}']["top"]
                            horse.position_1_left_pred_jockey_tendency = dic_position_pred[f'Horse{horse.horse_number}']["left"]
                    case "2コーナー":
                        for horse in horse_list:
                            horse.position_2_top_pred_jockey_tendency = dic_position_pred[f'Horse{horse.horse_number}']["top"]
                            horse.position_2_left_pred_jockey_tendency = dic_position_pred[f'Horse{horse.horse_number}']["left"]
                    case "3コーナー":
                        for horse in horse_list:
                            horse.position_3_top_pred_jockey_tendency = dic_position_pred[f'Horse{horse.horse_number}']["top"]
                            horse.position_3_left_pred_jockey_tendency = dic_position_pred[f'Horse{horse.horse_number}']["left"]
                    case "4コーナー":
                        for horse in horse_list:
                            horse.position_4_top_pred_jockey_tendency = dic_position_pred[f'Horse{horse.horse_number}']["top"]
                            horse.position_4_left_pred_jockey_tendency = dic_position_pred[f'Horse{horse.horse_number}']["left"]                
            # 「旧版の展開予想に切り替える」をクリックして脚質予想を取得
            driver.find_element(By.XPATH, "//*[@id='Netkeiba_Race_Nar_Shutuba']/div[1]/div[3]/div[14]/div/div/label/span").click()
            list_lead = []
            list_stalker = []
            list_chaser = []
            list_closer = []
            # 逃げ
            for i in range(1, num_horses + 1):
                if is_xpath_present(driver, "//*[@id='Netkeiba_Race_Nar_Shutuba']/div[1]/div[3]/div[16]/table/tbody/tr[1]/td/div[" + str(i) + "]/span[1]"):
                    list_lead.append(driver.find_element(By.XPATH, "//*[@id='Netkeiba_Race_Nar_Shutuba']/div[1]/div[3]/div[16]/table/tbody/tr[1]/td/div[" + str(i) + "]/span[1]").text)
                else:
                     break
            # 先行
            for i in range(1, num_horses + 1):
                if is_xpath_present(driver, "//*[@id='Netkeiba_Race_Nar_Shutuba']/div[1]/div[3]/div[16]/table/tbody/tr[2]/td/div[" + str(i) + "]/span[1]"):
                    list_stalker.append(driver.find_element(By.XPATH, "//*[@id='Netkeiba_Race_Nar_Shutuba']/div[1]/div[3]/div[16]/table/tbody/tr[2]/td/div[" + str(i) + "]/span[1]").text)
                else:
                     break
            # 差し
            for i in range(1, num_horses + 1):
                if is_xpath_present(driver, "//*[@id='Netkeiba_Race_Nar_Shutuba']/div[1]/div[3]/div[16]/table/tbody/tr[3]/td/div[" + str(i) + "]/span[1]"):
                    list_chaser.append(driver.find_element(By.XPATH, "//*[@id='Netkeiba_Race_Nar_Shutuba']/div[1]/div[3]/div[16]/table/tbody/tr[3]/td/div[" + str(i) + "]/span[1]").text)
                else:
                     break
            # 追込
            for i in range(1, num_horses + 1):
                if is_xpath_present(driver, "//*[@id='Netkeiba_Race_Nar_Shutuba']/div[1]/div[3]/div[16]/table/tbody/tr[4]/td/div[" + str(i) + "]/span[1]"):
                    list_closer.append(driver.find_element(By.XPATH, "//*[@id='Netkeiba_Race_Nar_Shutuba']/div[1]/div[3]/div[16]/table/tbody/tr[4]/td/div[" + str(i) + "]/span[1]").text)
                else:
                     break
            # 脚質予想を馬と紐づける
            for horse in horse_list:
                if horse.horse_number in list_lead:
                    horse.style_pred = STYLE_MAP.get(1)
                elif horse.horse_number in list_stalker:
                    horse.style_pred = STYLE_MAP.get(2)
                elif horse.horse_number in list_chaser:
                    horse.style_pred = STYLE_MAP.get(3)
                elif horse.horse_number in list_closer:
                    horse.style_pred = STYLE_MAP.get(4)
        elif MODE_NETKEIBA == "result" and racecourse != "帯広(ば)":
            if is_xpath_present(driver, XPATH_RANK_1_CORNER):
                rank_1_corner = driver.find_element(By.XPATH, XPATH_RANK_1_CORNER).text
            if is_xpath_present(driver, XPATH_RANK_2_CORNER):
                rank_2_corner = driver.find_element(By.XPATH, XPATH_RANK_2_CORNER).text
            if is_xpath_present(driver, XPATH_RANK_3_CORNER):
                rank_3_corner = driver.find_element(By.XPATH, XPATH_RANK_3_CORNER).text
            if is_xpath_present(driver, XPATH_RANK_4_CORNER):
                rank_4_corner = driver.find_element(By.XPATH, XPATH_RANK_4_CORNER).text
        # レースデータに格納
        race_data = Race(
            race_id = race_id,
            # race_name
            race_date = date,
            race_time = race_time,
            num_horses = num_horses,
            race_number = race_number,
            # weather_name
            # track_condition_name,
            racecourse = racecourse,
            ground = ground,
            distance = distance,
            direction = direction,
            reliability = reliability,
            opinion = opinion,
            rank_1_corner = rank_1_corner,
            rank_2_corner = rank_2_corner,
            rank_3_corner = rank_3_corner,
            rank_4_corner = rank_4_corner,
            horses = horse_list
        )
        # 出力確認
        print(f"\n📄 年月日: {race_data.race_date} | 競馬場: {race_data.racecourse} | R: {race_data.race_number}")
        for horse in race_data.horses:
            print(f"  馬番: {horse.horse_number} | 馬名: {horse.horse_name}")
    
    except Exception as e:
        print(f"❌ Race ID: {race_id} データ取得に失敗: {e}")
        return None
    # 戻り値
    return race_data

def create_html_body(df_buy, is_success):

    color_success = "#28a745"
    color_fail = "#dc3545"

    if df_buy.empty:
        return """
        <div style="font-family:sans-serif; max-width:800px; margin:auto; border:1px solid #ddd; padding:20px;">
            <h2>購入対象なし</h2>
            <p>購入条件を満たすレースがありませんでした。</p>
        </div>
        """

    status_color = color_success if is_success else color_fail
    status_text = "購入成功" if is_success else "購入失敗"

    tables = []

    # race_idごとにテーブルを作成
    for race_id, df_race in df_buy.groupby("race_id", sort=False):

        racecourse = df_race["racecourse"].iloc[0]
        race_number = df_race["race_number"].iloc[0]

        display_df = (
            df_race[
                [
                    "bet_type",
                    "horse_number_1",
                    "horse_number_2",
                    "horse_number_3",
                ]
            ]
            .rename(
                columns={
                    "bet_type": "券種",
                    "horse_number_1": "馬番1",
                    "horse_number_2": "馬番2",
                    "horse_number_3": "馬番3",
                }
            )
        )

        html = """
        <table style="border-collapse: collapse; width:100%; text-align:center; font-family:sans-serif;">
            <thead>
                <tr>
        """

        # ヘッダー
        for col in display_df.columns:
            html += f"""
                <th style="background:#f2f2f2; padding:8px; border:1px solid #ddd;">
                    {col}
                </th>
            """

        html += """
                </tr>
            </thead>
            <tbody>
        """

        # データ行
        for _, row in display_df.iterrows():

            html += "<tr>"

            for value in row:
                if pd.isna(value):
                    value = ""

                html += f"""
                    <td style="padding:8px; border:1px solid #ddd;">
                        {value}
                    </td>
                """

            html += "</tr>"

        html += """
            </tbody>
        </table>
        """

        tables.append(f"""
        <div style="margin-bottom:30px;">
            <h3 style="margin-bottom:10px;">
                {racecourse} {race_number}R（{race_id}）
            </h3>
            {html}
        </div>
        """)

    html_body = f"""
    <div style="font-family:sans-serif; max-width:800px; margin:auto; border:1px solid #ddd; padding:20px;">
        <h2 style="color:{status_color}; border-bottom:2px solid {status_color}; padding-bottom:10px;">
            {status_text}
        </h2>

        {''.join(tables)}

        <div style="font-size:12px; color:#888; margin-top:20px; text-align:center;">
            <hr>
            <p>このメールは競馬自動ツールから自動送信されています</p>
        </div>
    </div>
    """

    return html_body

def send_gmail(subject, body, to_address):
    # --- 設定項目 ---
    from_address = GMAIL_MAP.get('from')
    app_password = GMAIL_MAP.get('app_password')

    # --- メッセージの作成 ---
    msg = MIMEMultipart()
    msg['From'] = from_address
    msg['To'] = to_address
    msg['Subject'] = subject

    # --- 本文の追加 ---
    # もし body が <html> で始まっている場合は 'html' として、
    # そうでない場合は 'plain' として送る切り替えを入れる
    if body.strip().startswith('<'):
        msg.attach(MIMEText(body, 'html'))
    else:
        msg.attach(MIMEText(body, 'plain'))

    try:
        # --- SMTPサーバーへの接続と送信 ---
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        
        server.login(from_address, app_password)
        server.send_message(msg)
        server.quit()
        
        print("メールを送信しました")
        return True
    except Exception as e:
        print(f"送信失敗: {e}")
        return False

# %%
# ========================
# スケジュールデータ読み込み
# ========================

### スケジュールデータ読み込み ###
print("スケジュールデータ読み込み：開始")
path_schedule = Path.cwd().parent.parent / "data" / "pred" / "schedule.csv"
df_schedule_raw = pd.read_csv(path_schedule, header=0, encoding='cp932', dtype={'race_id': str})
print("スケジュールデータ読み込み：終了")

# %%
# =================
# 予想データ読み込み
# =================

### predデータ読み込み ###
print("predデータ読み込み：開始")
path_pred = Path.cwd().parent.parent / "data" / "pred" / "pred.csv"
df_pred_raw = pd.read_csv(path_pred, header=0, encoding='cp932', dtype={'race_id': str})
print("predデータ読み込み：終了")

# %%
df_schedule = df_schedule_raw.copy()
df_pred_all = df_pred_raw.copy()

# %%
df_schedule

# %%
df_pred_all

# %% [markdown]
# # 購入データ作成

# %%
# ===== 対象レースを絞る =====

list_race_id = df_schedule.loc[df_schedule["status"] == "本予測完了", "race_id"].tolist()
list_race_id = [str(x) for x in list_race_id]
if len(list_race_id) == 0:
    print("本予測：なし")
    sys.exit()
list_df_pred = []
for race_id in list_race_id:
    race_id = str(race_id)
    path_pred = Path.cwd().parent.parent / "data" / "pred" / f"pred_{race_id}.csv"
    if path_pred.exists():
        df = pd.read_csv(path_pred, encoding="cp932", dtype={"race_id": str})
    else:
        df = df_pred_all.loc[df_pred_all["race_id"] == race_id]
    list_df_pred.append(df)
df_pred = pd.concat(list_df_pred, ignore_index=True)
df_pred["horse_number"] = df_pred["horse_number"].astype("Int64")
target_race_ids = df_pred.loc[(df_pred["finish_rank_pred"] == 1) & (df_pred["style_pred"] == "追込"), "race_id"].unique()

# ===== 対象レースの上位馬で絞る =====

# 1着予想馬（対象レースのみ）
df_finish_rank_pred_1 = (
    df_pred.loc[df_pred["race_id"].isin(target_race_ids) & (df_pred["finish_rank_pred"] == 1), ["race_id", "horse_number"]]
    .rename(columns={"horse_number": "horse_number_1"})
)
# 2着予想馬（対象レースのみ）
df_finish_rank_pred_2 = (
    df_pred.loc[df_pred["race_id"].isin(target_race_ids) & (df_pred["finish_rank_pred"] == 2), ["race_id", "horse_number"]]
    .rename(columns={"horse_number": "horse_number_2"})
)
# 3着予想馬（対象レースのみ）
df_finish_rank_pred_3 = (
    df_pred.loc[df_pred["race_id"].isin(target_race_ids) & (df_pred["finish_rank_pred"] == 3), ["race_id", "horse_number"]]
    .rename(columns={"horse_number": "horse_number_3"})
)
# 2・3着予想馬（対象レースのみ）
df_finish_rank_pred_2_3 = (
    df_pred.loc[df_pred["race_id"].isin(target_race_ids) & df_pred["finish_rank_pred"].isin([2, 3]), ["race_id", "horse_number"]]
    .rename(columns={"horse_number": "horse_number_2"})
)

# ===== 馬券作成 =====

# 単勝・複勝
df_buy_win = df_finish_rank_pred_1.copy()
df_buy_win["bet_type"] = "単勝"
df_buy_place = df_finish_rank_pred_1.copy()
df_buy_place["bet_type"] = "複勝"
# ワイド・馬連・馬単
df_comb2 = df_finish_rank_pred_1.merge(df_finish_rank_pred_2_3, on="race_id", how="inner")
df_buy_quinella_place = df_comb2.copy()
df_buy_quinella_place["bet_type"] = "ワイド"
df_buy_quinella = df_comb2.copy()
df_buy_quinella["bet_type"] = "馬連"
df_buy_exacta = df_comb2.copy()
df_buy_exacta["bet_type"] = "馬単"
# 三連複・三連単
df_comb3 = (
    df_finish_rank_pred_1
    .merge(df_finish_rank_pred_2, on="race_id", how="inner")
    .merge(df_finish_rank_pred_3, on="race_id", how="inner")
)
df_buy_trio = df_comb3.copy()
df_buy_trio["bet_type"] = "三連複"
df_buy_trifecta = df_comb3.copy()
df_buy_trifecta["bet_type"] = "三連単"
# 全馬券を結合
df_buy = pd.concat(
    [df_buy_win, df_buy_place, df_buy_quinella_place, df_buy_quinella, df_buy_exacta, df_buy_trio, df_buy_trifecta],
    ignore_index=True
)
# ソート
df_buy["bet_type"] = pd.Categorical(df_buy["bet_type"], categories=["単勝", "複勝", "ワイド", "馬連", "馬単", "三連複", "三連単"], ordered=True)
df_buy = (df_buy.sort_values(by=["race_id", "bet_type"]).reset_index(drop=True))
# スケジュールファイル更新
df_schedule.loc[df_schedule["race_id"].isin(list_race_id) & ~df_schedule["race_id"].isin(target_race_ids), "status"] = "対象外"
# df_buyに競馬場とレース番号を追加
df_race_condition = df_pred_all.drop_duplicates(
    subset=["race_id", "racecourse", "race_number"]
).reset_index(drop=True)
df_buy = df_buy.merge(
    df_race_condition[["race_id", "racecourse", "race_number"]],
    on="race_id",
    how="left"
)

# %%
df_buy

# %%
##########
# 購入
##########

if len(df_buy) > 0:
    
    is_success = True
    # スクレイピング準備
    service = Service(PATH_CHROME_DRIVER)
    options = webdriver.ChromeOptions()
    # options.add_argument('--headless')
    # レースごとにループ
    for race_id, df_race in df_buy.groupby("race_id"):
        num_tickets = 0
        # 対象
        racecourse = df_race["racecourse"].iloc[0]
        race_number = df_race["race_number"].iloc[0]
        print(f"レースID：{race_id}")
        print(f"競馬場：{racecourse}")
        print(f"レース番号：{race_number}")
        # スクレイピング準備
        driver = webdriver.Chrome(service=service, options=options)
        driver.set_page_load_timeout(30)
        try:
            # ログイン
            login_spat4(driver)
            # お知らせが表示されたら閉じる
            xpath_notification = "//*[@id='popupscreen']/table/tbody/tr[3]/td/input"
            if is_xpath_present(driver, xpath_notification):
                try:
                    driver.find_element(By.XPATH, xpath_notification).click()
                except:
                    pass
            # オッズ投票画面に遷移
            xpath_1_odds = "/html/body/div[2]/div[1]/table/tbody/tr[2]/td[5]/a/span/div"
            xpath_2_odds = "/html/body/div[2]/div[1]/table[1]/tbody/tr[2]/td[5]/a/span/div"
            if is_xpath_present(driver, xpath_1_odds):
                driver.find_element(By.XPATH, xpath_1_odds).click()
            else :
                driver.find_element(By.XPATH, xpath_2_odds).click()
            # 競馬場とRを選択
            driver.switch_to.frame("LEFT")
            dropdown_element_racecourse = driver.find_element(By.NAME, "PLACE")
            dropdown_element_race_number = driver.find_element(By.NAME, "RACE")
            select_obj_racecourse = Select(dropdown_element_racecourse)
            select_obj_race_number = Select(dropdown_element_race_number)
            flg_racecourse_exists = racecourse in [o.text for o in select_obj_racecourse.options]
            flg_race_number_exists = f"{race_number}R" in [o.text for o in select_obj_race_number.options]
            if flg_racecourse_exists & flg_race_number_exists:
                select_obj_racecourse.select_by_visible_text(racecourse)
                dropdown_element_race_number = driver.find_element(By.NAME, "RACE")
                select_obj_race_number = Select(dropdown_element_race_number)
                select_obj_race_number.select_by_visible_text(f"{race_number}R")
                # プルダウンで「単勝複勝」を選択（最初から単勝複勝なので特に処理不要）
                # 単勝の馬券を選択
                df_win = df_race[df_race["bet_type"] == "単勝"]
                for _, row in df_win.iterrows():
                    horse_number_1 = row["horse_number_1"]
                    # 同枠の1行目は5列ある
                    # 1列目：枠番 2列目：馬番 3列目：馬名 4列目：単勝オッズ 5列目：複勝オッズ
                    if is_xpath_present(driver, f"/html/body/form[2]/table/tbody/tr[{str(horse_number_1 + 2)}]/td[5]"):
                        xpath_odds = f"/html/body/form[2]/table/tbody/tr[{str(horse_number_1 + 2)}]/td[4]"
                        odds_win = driver.find_element(By.XPATH, xpath_odds).text
                        # oddsが数字
                        if any(char.isdigit() for char in odds_win):
                            # 購入する馬のオッズをクリック
                            driver.find_element(By.XPATH, xpath_odds).click()
                            num_tickets = num_tickets + 1
                        # oddsが数字でない（取消等）
                        else:
                            # 対象外のためループを終了
                            df_schedule.loc[df_schedule["race_id"] == race_id, "status"] = "除外"
                            driver.quit()
                            continue
                    # 同枠の2行目は4列ある
                    # 1列目：馬番 2列目：馬名 3列目：単勝オッズ 4列目：複勝オッズ
                    else:
                        xpath_odds = f"/html/body/form[2]/table/tbody/tr[{str(horse_number_1 + 2)}]/td[3]"
                        odds_win = driver.find_element(By.XPATH, xpath_odds).text
                        # oddsが数字
                        if any(char.isdigit() for char in odds_win):
                            # 購入する馬のオッズをクリック
                            driver.find_element(By.XPATH, xpath_odds).click()
                            num_tickets = num_tickets + 1
                        # oddsが数字でない（取消等）
                        else:
                            # 対象外のためループを終了
                            df_schedule.loc[df_schedule["race_id"] == race_id, "status"] = "除外"
                            driver.quit()
                            continue
                # 複勝の馬券を選択
                df_win = df_race[df_race["bet_type"] == "複勝"]
                for _, row in df_win.iterrows():
                    horse_number_1 = row["horse_number_1"]
                    # 同枠の1行目は5列ある
                    # 1列目：枠番 2列目：馬番 3列目：馬名 4列目：単勝オッズ 5列目：複勝オッズ
                    if is_xpath_present(driver, f"/html/body/form[2]/table/tbody/tr[{str(horse_number_1 + 2)}]/td[5]"):
                        xpath_odds = f"/html/body/form[2]/table/tbody/tr[{str(horse_number_1 + 2)}]/td[5]"
                        driver.find_element(By.XPATH, xpath_odds).click()
                    # 同枠の2行目は4列ある
                    # 1列目：馬番 2列目：馬名 3列目：単勝オッズ 4列目：複勝オッズ
                    else:
                        xpath_odds = f"/html/body/form[2]/table/tbody/tr[{str(horse_number_1 + 2)}]/td[4]"
                        driver.find_element(By.XPATH, xpath_odds).click()
                    num_tickets = num_tickets + 1
                # プルダウンで「ワイド」を選択
                dropdown_element_bet_type = driver.find_element(By.NAME, "SHIKILINK")
                select_obj_bet_type = Select(dropdown_element_bet_type)
                select_obj_bet_type.select_by_visible_text("ワイド")
                # ワイドの馬券を選択
                df_win = df_race[df_race["bet_type"] == "ワイド"]
                for _, row in df_win.iterrows():
                    horse_number_A = min(row["horse_number_1"], row["horse_number_2"])
                    horse_number_B = max(row["horse_number_1"], row["horse_number_2"])
                    col = horse_number_A * 2
                    row = horse_number_B - horse_number_A + 2
                    print(horse_number_A)
                    print(horse_number_B)
                    print(col)
                    print(row)
                    xpath_odds = f"/html/body/form[2]/table/tbody/tr[{str(row)}]/td[{str(col)}]/a"
                    driver.find_element(By.XPATH, xpath_odds).click()
                    num_tickets = num_tickets + 1
                # プルダウンで「馬複」を選択
                dropdown_element_bet_type = driver.find_element(By.NAME, "SHIKILINK")
                select_obj_bet_type = Select(dropdown_element_bet_type)
                select_obj_bet_type.select_by_visible_text("馬複")
                # 馬連の馬券を選択
                df_win = df_race[df_race["bet_type"] == "馬連"]
                for _, row in df_win.iterrows():
                    horse_number_A = min(row["horse_number_1"], row["horse_number_2"])
                    horse_number_B = max(row["horse_number_1"], row["horse_number_2"])
                    col = horse_number_A * 2
                    row = horse_number_B - horse_number_A + 2
                    xpath_odds = f"/html/body/form[2]/table/tbody/tr[{str(row)}]/td[{str(col)}]/a"
                    driver.find_element(By.XPATH, xpath_odds).click()
                    num_tickets = num_tickets + 1
                # プルダウンで「馬単」を選択
                dropdown_element_bet_type = driver.find_element(By.NAME, "SHIKILINK")
                select_obj_bet_type = Select(dropdown_element_bet_type)
                select_obj_bet_type.select_by_visible_text("馬単")
                # 馬単の馬券を選択
                df_win = df_race[df_race["bet_type"] == "馬単"]
                for _, row in df_win.iterrows():
                    horse_number_1 = row["horse_number_1"]
                    horse_number_2 = row["horse_number_2"]
                    col = horse_number_1 * 2
                    row = horse_number_2 + 2
                    xpath_odds_show = f"/html/body/form[2]/table/tbody/tr[{str(row)}]/td[{str(col)}]/a"
                    driver.find_element(By.XPATH, xpath_odds_show).click()
                    num_tickets = num_tickets + 1
                # 馬券の数だけ金額入力
                driver.switch_to.default_content()
                driver.switch_to.frame("RIGHT")
                for i in range(1, num_tickets + 1):
                    driver.find_element(By.XPATH, f"//*[@id='TEXTMONEY_{str(i)}']").send_keys("1")
                # 「投票内容確認へ」をクリック
                driver.find_element(By.XPATH, "/html/body/form/center/table[3]/tbody/tr/td/font/nobr/input[1]").click()
                # 「投票内容確認へ移ります。よろしいですか？」を次に進むためにENTER
                wait = WebDriverWait(driver, 5)
                wait.until(EC.alert_is_present())
                alert = driver.switch_to.alert
                alert.accept()
                driver.switch_to.window(driver.window_handles[-1])
                driver.switch_to.default_content()
                # 暗証番号入力
                time.sleep(1)
                driver.find_element(By.NAME, "MEMBERPASSR").send_keys(SPAT4_MAP.get('暗証番号'))
                # 投票金額入力（単勝と複勝100ずつで合計200）
                driver.find_element(By.XPATH, "//*[@id='TOTALMONEYR']").send_keys(str(num_tickets * 100))
                # 投票する押下
                if SPAT4_MAP.get('MODE') == 'prod':
                    driver.find_element(By.XPATH, "/html/body/div/center/form/table/tbody/tr/td/input").click()
                    # 「投票を実行します。よろしいですか？」を次に進むためにENTER
                    wait = WebDriverWait(driver, 5)
                    wait.until(EC.alert_is_present())
                    alert = driver.switch_to.alert
                    alert.accept()
                    time.sleep(3)
                df_schedule.loc[df_schedule["race_id"] == race_id, "status"] = "購入成功"
            # 閉じる
            driver.quit()
            print("購入：成功")
        except Exception as e:
            print(e)
            is_success = False
            df_schedule.loc[df_schedule["race_id"] == race_id, "status"] = "購入失敗"
            print("購入：失敗")
else:
    is_success = True
    for race_id in list_race_id:
        df_schedule.loc[df_schedule["race_id"] == race_id, "status"] = "対象外"
    print("購入：対象外")

# %%
# ================
# メール送信
# ================
    
# --- メイン処理部分 ---
to_address = GMAIL_MAP.get('to')

if not df_buy.empty and is_success:
    subject = "【競馬ツール】購入完了【〇】"
elif not df_buy.empty and not is_success:
    subject = "【競馬ツール】購入失敗【×】"
else:
    subject = "【競馬ツール】対象外【－】"

body_html = create_html_body(df_buy, is_success)

# 送信（send_gmailの中でMIMETextの第二引数を'html'にする必要があります）
send_gmail(subject, body_html, to_address)

# %%
# ================
# ファイル出力
# ================

df_schedule.to_csv(path_schedule, index=False, encoding="cp932")


