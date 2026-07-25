# %%
### インポート ###

import platform
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import time
from selenium.webdriver.common.keys import Keys
import re
import pandas as pd
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, TypeVar
import os
import logging
import functools
from pathlib import Path
import sys
import shutil
from selenium.common.exceptions import TimeoutException

# %%
def is_jupyter():
    try:
        shell = get_ipython().__class__.__name__
        if shell == 'ZMQInteractiveShell':
            return True   # Jupyter notebook or qtconsole
        elif shell == 'TerminalInteractiveShell':
            return False  # Terminal IPython
        else:
            return False  # Other shell type
    except NameError:
        return False      # Probably standard Python interpreter

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
RACE_LIST_URL = df_config_netkeiba.loc["RACE_LIST_URL"].iloc[0]
if not is_jupyter() and len(sys.argv) > 1:
    MODE = sys.argv[1]
else:
    MODE = df_config_netkeiba.loc["MODE"].iloc[0]
if MODE == "shutuba":
    MODE_CAPITAL = "Shutuba"
elif MODE == "result":
    MODE_CAPITAL = "Result"
# レース単位
print(f"MODE: {MODE}")
if MODE == "shutuba":
    SELECTOR_RACECOURSE = df_config_netkeiba.loc["SELECTOR_RACECOURSE_SHUTUBA"].iloc[0]
    SELECTOR_RACE_NUMBER = df_config_netkeiba.loc["SELECTOR_RACE_NUMBER_SHUTUBA"].iloc[0]
    SELECTOR_NUM_HORSES = df_config_netkeiba.loc["SELECTOR_NUM_HORSES_SHUTUBA"].iloc[0]
    XPATH_RACE_INFO = df_config_netkeiba.loc["XPATH_RACE_INFO_SHUTUBA"].iloc[0]
elif MODE == "result":
    SELECTOR_RACECOURSE = df_config_netkeiba.loc["SELECTOR_RACECOURSE_RESULT"].iloc[0]
    SELECTOR_RACE_NUMBER = df_config_netkeiba.loc["SELECTOR_RACE_NUMBER_RESULT"].iloc[0]
    SELECTOR_NUM_HORSES = df_config_netkeiba.loc["SELECTOR_NUM_HORSES_RESULT"].iloc[0]
    XPATH_RACE_INFO = df_config_netkeiba.loc["XPATH_RACE_INFO_RESULT"].iloc[0]


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
    horses: List[T] = field(default_factory=list)
    payouts: List[T] = field(default_factory=list) 
    odds: List[T] = field(default_factory=list)

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

@log_step
def create_driver():

    options = webdriver.ChromeOptions()
    if platform.system() == "Windows":
        service = Service(PATH_CHROME_DRIVER)
        # options.add_argument('--headless')
        driver = webdriver.Chrome(service=service, options=options)
    elif platform.system() == "Linux":
        options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')               # Linux環境の権限エラー回避
        options.add_argument('--disable-dev-shm-usage')    # /dev/shmのメモリ不足回避
        options.add_argument('--disable-gpu')
        driver = webdriver.Chrome(options=options)
    else:
        raise RuntimeError(f"未対応のOSです: {platform.system()}")

    return driver

def is_xpath_present(driver, xpath):
    return len(driver.find_elements(By.XPATH, xpath)) > 0

def is_css_selector_present(driver, css_selector):
    return len(driver.find_elements(By.CSS_SELECTOR, css_selector)) > 0

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

@log_step
def login_netkeiba(driver):

    # ログイン済みの場合は何もしない
    current_url = driver.current_url
    print(current_url)
    if current_url == "https://regist.netkeiba.com/":
        return
    # ログイン済みでない場合はログインする
    xpath = "//*[@id='page']/header/div/h1/a/img"
    while True:
        # ログイン画面に遷移
        try:
            driver.get(LOGIN_URL)
        except TimeoutException:
            print("タイムアウトしたが処理を継続")
            driver.execute_script("window.stop();")
        time.sleep(1)
        if not is_xpath_present(driver, xpath):
            continue
        # ログイン情報入力
        try:
            driver.find_element(By.NAME, "login_id").send_keys(LOGIN_ID)
            pw_field = driver.find_element(By.NAME, "pswd")
            pw_field.send_keys(LOGIN_PASSWORD)
            # ログイン後の画面に遷移
            pw_field.send_keys(Keys.ENTER)
        except TimeoutException:
            print("タイムアウトしたが処理を継続")
            driver.execute_script("window.stop();")
        time.sleep(1)
        if is_xpath_present(driver, xpath):
            break
        else:
            continue

@log_step
def scrape_horse_shutuba_data(driver, num_horses):
    
    all_horses_data = []
    # 馬番・馬名取得
    # 馬番・馬名・馬名リンク取得
    for i in range(1, num_horses + 1):
        try:
            # 馬番
            xpath_horse_number = df_config_netkeiba.loc["XPATH_HORSE_NUMBER_1_SHUTUBA"].iloc[0] + str(i) + df_config_netkeiba.loc["XPATH_HORSE_NUMBER_2_SHUTUBA"].iloc[0]
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
            xpath_horse_link_1 = df_config_netkeiba.loc["XPATH_HORSE_LINK_1_1_SHUTUBA"].iloc[0] + str(i) + df_config_netkeiba.loc["XPATH_HORSE_LINK_1_2_SHUTUBA"].iloc[0]
            xpath_horse_link_2 = df_config_netkeiba.loc["XPATH_HORSE_LINK_2_1_SHUTUBA"].iloc[0] + str(i) + df_config_netkeiba.loc["XPATH_HORSE_LINK_2_2_SHUTUBA"].iloc[0]
            if is_xpath_present(driver, xpath_horse_link_1):
                xpath_horse_link = xpath_horse_link_1
            elif is_xpath_present(driver, xpath_horse_link_2):
                xpath_horse_link = xpath_horse_link_2
            horse_link_elem = driver.find_element(By.XPATH, xpath_horse_link)
            horse_name = horse_link_elem.text.strip()
            horse_href = horse_link_elem.get_attribute("href")
            horse_id = horse_href.rstrip("/").split("/")[-1]
            # 騎手名と騎手ID
            xpath_jockey_link = df_config_netkeiba.loc["XPATH_JOCKEY_LINK_1_SHUTUBA"].iloc[0] + str(i) + df_config_netkeiba.loc["XPATH_JOCKEY_LINK_2_SHUTUBA"].iloc[0]
            jockey_link_elem = driver.find_element(By.XPATH, xpath_jockey_link)
            jockey_name = jockey_link_elem.text.strip()
            jockey_href = jockey_link_elem.get_attribute("href")
            jockey_id = jockey_href.rstrip("/").split("/")[-1]
            # 人気
            xpath_popularity = df_config_netkeiba.loc["XPATH_POPULARITY_1_SHUTUBA"].iloc[0] + str(i) + df_config_netkeiba.loc["XPATH_POPULARITY_2_SHUTUBA"].iloc[0]
            popularity = driver.find_element(By.XPATH, xpath_popularity).text
            # オッズ
            xpath_odds = df_config_netkeiba.loc["XPATH_ODDS_1_SHUTUBA"].iloc[0] + str(i) + df_config_netkeiba.loc["XPATH_ODDS_2_SHUTUBA"].iloc[0]
            odds = driver.find_element(By.XPATH, xpath_odds).text
            # 性齢
            xpath_sex_and_age = df_config_netkeiba.loc["XPATH_SEX_AND_AGE_1_SHUTUBA"].iloc[0] + str(i) + df_config_netkeiba.loc["XPATH_SEX_AND_AGE_2_SHUTUBA"].iloc[0]
            sex_and_age = driver.find_element(By.XPATH, xpath_sex_and_age).text
            # 馬体重
            xpath_weight = df_config_netkeiba.loc["XPATH_WEIGHT_1_SHUTUBA"].iloc[0] + str(i) + df_config_netkeiba.loc["XPATH_WEIGHT_2_SHUTUBA"].iloc[0]
            weight = driver.find_element(By.XPATH, xpath_weight).text
            # 枠番
            xpath_frame_number = df_config_netkeiba.loc["XPATH_FRAME_1_SHUTUBA"].iloc[0] + str(i) + df_config_netkeiba.loc["XPATH_FRAME_2_SHUTUBA"].iloc[0]
            frame_number = driver.find_element(By.XPATH, xpath_frame_number).text
            # 斤量
            xpath_impost = df_config_netkeiba.loc["XPATH_IMPOSE_1_SHUTUBA"].iloc[0] + str(i) + df_config_netkeiba.loc["XPATH_IMPOSE_2_SHUTUBA"].iloc[0]
            impost = driver.find_element(By.XPATH, xpath_impost).text
            # 後半3F
            xpath_last_3_furlongs_pred = df_config_netkeiba.loc["XPATH_LAST_3_FURLONGS_PRED_1_SHUTUBA"].iloc[0] + str(i) + df_config_netkeiba.loc["XPATH_LAST_3_FURLONGS_PRED_2_SHUTUBA"].iloc[0]
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

@log_step
def get_all_horses_result(driver, num_horses):

    all_horses_data = []
    # 馬番・馬名取得
    # 馬番・馬名・馬名リンク取得
    for i in range(1, num_horses + 1):
        try:
            # 着番
            xpath_finish_rank = df_config_netkeiba.loc["XPATH_FINISH_RANK_1_RESULT"].iloc[0] + str(i) + df_config_netkeiba.loc["XPATH_FINISH_RANK_2_RESULT"].iloc[0]
            finish_rank = driver.find_element(By.XPATH, xpath_finish_rank).text
            # 枠番
            xpath_frame_number = df_config_netkeiba.loc["XPATH_FRAME_NUMBER_1_RESULT"].iloc[0] + str(i) + df_config_netkeiba.loc["XPATH_FRAME_NUMBER_2_RESULT"].iloc[0]
            frame_number = driver.find_element(By.XPATH, xpath_frame_number).text
            # 馬番
            xpath_horse_number = df_config_netkeiba.loc["XPATH_HORSE_NUMBER_1_RESULT"].iloc[0] + str(i) + df_config_netkeiba.loc["XPATH_HORSE_NUMBER_2_RESULT"].iloc[0]
            if is_xpath_present(driver, xpath_horse_number):
                horse_number = driver.find_element(By.XPATH, xpath_horse_number).text.strip()
            else:
                continue
            # 馬名と馬ID
            xpath_horse_link = df_config_netkeiba.loc["XPATH_HORSE_LINK_1_RESULT"].iloc[0] + str(i) + df_config_netkeiba.loc["XPATH_HORSE_LINK_2_RESULT"].iloc[0]
            horse_link_elem = driver.find_element(By.XPATH, xpath_horse_link)
            horse_name = horse_link_elem.text.strip()
            horse_href = horse_link_elem.get_attribute("href")
            horse_id = horse_href.rstrip("/").split("/")[-1]
            # 性齢
            xpath_sex_and_age = df_config_netkeiba.loc["XPATH_SEX_AND_AGE_1_RESULT"].iloc[0] + str(i) + df_config_netkeiba.loc["XPATH_SEX_AND_AGE_2_RESULT"].iloc[0]
            sex_and_age = driver.find_element(By.XPATH, xpath_sex_and_age).text
            # 斤量
            xpath_impost = df_config_netkeiba.loc["XPATH_IMPOSE_1_RESULT"].iloc[0] + str(i) + df_config_netkeiba.loc["XPATH_IMPOSE_2_RESULT"].iloc[0]
            impost = driver.find_element(By.XPATH, xpath_impost).text
            # 騎手名と騎手ID
            xpath_jockey_link = df_config_netkeiba.loc["XPATH_JOCKEY_LINK_1_RESULT"].iloc[0] + str(i) + df_config_netkeiba.loc["XPATH_JOCKEY_LINK_2_RESULT"].iloc[0]
            jockey_link_elem = driver.find_element(By.XPATH, xpath_jockey_link)
            jockey_name = jockey_link_elem.text.strip()
            jockey_href = jockey_link_elem.get_attribute("href")
            jockey_id = jockey_href.rstrip("/").split("/")[-1]
            # タイム
            xpath_time = df_config_netkeiba.loc["XPATH_TIME_1_RESULT"].iloc[0] + str(i) + df_config_netkeiba.loc["XPATH_TIME_2_RESULT"].iloc[0]
            time = driver.find_element(By.XPATH, xpath_time).text
            # 着差
            xpath_diff = df_config_netkeiba.loc["XPATH_DIFF_1_RESULT"].iloc[0] + str(i) + df_config_netkeiba.loc["XPATH_DIFF_2_RESULT"].iloc[0]
            diff = driver.find_element(By.XPATH, xpath_diff).text
            # 人気
            xpath_popularity = df_config_netkeiba.loc["XPATH_POPULARITY_1_RESULT"].iloc[0] + str(i) + df_config_netkeiba.loc["XPATH_POPULARITY_2_RESULT"].iloc[0]
            popularity = driver.find_element(By.XPATH, xpath_popularity).text
            # オッズ
            xpath_odds = df_config_netkeiba.loc["XPATH_ODDS_1_RESULT"].iloc[0] + str(i) + df_config_netkeiba.loc["XPATH_ODDS_2_RESULT"].iloc[0]
            odds = driver.find_element(By.XPATH, xpath_odds).text
            # 後半3F
            xpath_last_3_furlongs = df_config_netkeiba.loc["XPATH_LAST_3_FURLONGS_1_RESULT"].iloc[0] + str(i) + df_config_netkeiba.loc["XPATH_LAST_3_FURLONGS_2_RESULT"].iloc[0]
            last_3_furlongs = driver.find_element(By.XPATH, xpath_last_3_furlongs).text
            # 馬体重
            xpath_weight = df_config_netkeiba.loc["XPATH_WEIGHT_1_RESULT"].iloc[0] + str(i) + df_config_netkeiba.loc["XPATH_WEIGHT_2_RESULT"].iloc[0]
            weight = driver.find_element(By.XPATH, xpath_weight).text
            # 馬データ作成
            horse_data = Horse_Result(
                finish_rank = finish_rank,
                frame_number = frame_number,
                horse_number = horse_number,
                horse_id = horse_id,
                horse_name = horse_name,
                sex_and_age = sex_and_age,
                impost =   impost,
                jockey_id = jockey_id,
                jockey_name = jockey_name,
                time = time,
                diff = diff,
                popularity = popularity,
                odds = odds,
                last_3_furlongs = last_3_furlongs,
                weight = weight
            )
            all_horses_data.append(horse_data)
        except Exception as e:
            print(f"  馬番{i}: データ取得失敗 ({e})")
    # 戻り値
    return all_horses_data

@log_step
def get_all_odds(driver, race_id, num_horses, racecourse):

    list_odds = []
    # 単勝・複勝
    url = f"https://nar.netkeiba.com/odds/?race_id={race_id}&type=b1"
    xpath = "//*[@id='Netkeiba_Race_OddsView']/div[1]/header/div/h1/a/img"
    while True:
        driver.get(url)
        if is_xpath_present(driver, xpath):
            break
    for horse_number in range(1, num_horses + 1):
        # 単勝
        xpath_odds_1 = f"//*[@id='odds_tan_block']/table/tbody/tr[{horse_number + 1}]/td[5]"
        xpath_odds_2 = f"//*[@id='odds_tan_block']/table/tbody/tr[{horse_number + 1}]/td[6]"
        if is_xpath_present(driver, xpath_odds_2):
            odds = driver.find_element(By.XPATH, xpath_odds_2).text
        elif is_xpath_present(driver, xpath_odds_1):
            odds = driver.find_element(By.XPATH, xpath_odds_1).text
        else:
            odds = ""
        list_odds.append({"race_id": race_id, "type": "win", "horse_number_1": horse_number, "horse_number_2": "", "odds_1": odds, "odds_2": ""})
        # 複勝
        xpath_odds_1 = f"//*[@id='odds_fuku_block']/table/tbody/tr[{horse_number + 1}]/td[5]"
        xpath_odds_2 = f"//*[@id='odds_fuku_block']/table/tbody/tr[{horse_number + 1}]/td[6]"
        if is_xpath_present(driver, xpath_odds_2):
            odds = driver.find_element(By.XPATH, xpath_odds_2).text
        elif is_xpath_present(driver, xpath_odds_1):
            odds = driver.find_element(By.XPATH, xpath_odds_1).text
        else:
            odds = ""
        if "-" in odds:
            odds_low = odds.split("-")[0]
            odds_high = odds.split("-")[1]
        else:
            odds_low = ""
            odds_high = ""
        list_odds.append({"race_id": race_id, "type": "place", "horse_number_1": horse_number, "horse_number_2": "","odds_1": odds_low, "odds_2": odds_high})
    # 馬連
    url = f"https://nar.netkeiba.com/odds/?race_id={race_id}&type=b4"
    xpath = "//*[@id='Netkeiba_Race_OddsView']/div[1]/header/div/h1/a/img"
    while True:
        driver.get(url)
        if is_xpath_present(driver, xpath):
            break
    for horse_number_1 in range(1, num_horses + 1):
        for horse_number_2 in range(horse_number_1 + 1, num_horses + 1):
            xpath = f"//*[contains(@id, '{horse_number_1}_{horse_number_2}')]"
            if is_xpath_present(driver, xpath):
                odds = driver.find_element(By.XPATH, xpath).text
            else:
                odds = ""
            list_odds.append({"race_id": race_id, "type": "quinella", "horse_number_1": horse_number_1, "horse_number_2": horse_number_2, "odds_1": odds, "odds_2": ""})
    # ワイド
    url = f"https://nar.netkeiba.com/odds/?race_id={race_id}&type=b5"
    xpath = "//*[@id='Netkeiba_Race_OddsView']/div[1]/header/div/h1/a/img"
    while True:
        driver.get(url)
        if is_xpath_present(driver, xpath):
            break
    for horse_number_1 in range(1, num_horses + 1):
        for horse_number_2 in range(horse_number_1 + 1, num_horses + 1):
            xpath = f"//*[contains(@id, '{horse_number_1}_{horse_number_2}')]"
            if is_xpath_present(driver, xpath):
                odds = driver.find_element(By.XPATH, xpath).text
            else:
                odds = ""
            if "-" in odds:
                odds_low = odds.split("-")[0]
                odds_high = odds.split("-")[1]
            else:
                odds_low = ""
                odds_high = ""
            list_odds.append({"race_id": race_id, "type": "quinella_place", "horse_number_1": horse_number_1, "horse_number_2": horse_number_2, "odds_1": odds_low, "odds_2": odds_high})
    # 馬単
    url = f"https://nar.netkeiba.com/odds/?race_id={race_id}&type=b6"
    xpath = "//*[@id='Netkeiba_Race_OddsView']/div[1]/header/div/h1/a/img"
    while True:
        driver.get(url)
        if is_xpath_present(driver, xpath):
            break
    for horse_number_1 in range(1, num_horses + 1):
        for horse_number_1 in range(1, num_horses + 1):
            if horse_number_1 == horse_number_2:
                continue
            xpath = f"//*[contains(@id, '{horse_number_1}_{horse_number_2}')]"
            if is_xpath_present(driver, xpath):
                odds = driver.find_element(By.XPATH, xpath).text
            else:
                odds = ""
            list_odds.append({"race_id": race_id, "type": "exacta", "horse_number_1": horse_number_1, "horse_number_2": horse_number_2, "odds_1": odds, "odds_2": ""})
    return list_odds

@log_step
def fetch_bet_type_payouts(driver, race_id, date, racecourse, race_number, xpath_bet_type, xpath_horse_number, xpath_payout, all_payouts):
    """
    指定された馬券種の払い戻し情報を取得し、リストに追加する
    """
    # XPATHが存在しない場合は何もしない
    if not is_xpath_present(driver, xpath_bet_type):
        print(f"存在しない: {xpath_bet_type}")
        return
    else:
        print(f"存在する: {xpath_bet_type}")
    # データの取得
    bet_type = driver.find_element(By.XPATH, xpath_bet_type).text
    list_horse_numbers = driver.find_element(By.XPATH, xpath_horse_number).text.splitlines()    # 5 6, 5,7
    list_payout = driver.find_element(By.XPATH, xpath_payout).text.splitlines()         # 1400, 1600
    # 辞書に追加
    for str_horse_numbers, str_payout in zip(list_horse_numbers, list_payout):
        horse_number_1 = ""
        horse_number_2 = ""
        horse_number_3 = ""
        list_horse_number = str_horse_numbers.split()
        for i, horse_number in enumerate(list_horse_number, start=1):
            if i == 1:
                horse_number_1 = horse_number
            elif i == 2:
                horse_number_2 = horse_number
            elif i == 3:
                horse_number_3 = horse_number
        # 払戻金
        str_payout = str_payout.replace("円", "")
        str_payout = str_payout.replace(",", "")
        payout = str_payout
        # 辞書に追加
        all_payouts.append({
            "race_id": race_id,
            "date": date,
            "racecourse": racecourse,
            "race_number": race_number,
            "bet_type": bet_type,
            "horse_number_1": horse_number_1, 
            "horse_number_2": horse_number_2, 
            "horse_number_3": horse_number_3, 
            "payout": payout
        })

@log_step
def get_all_payouts(driver, race_id, date, racecourse, race_number):

    all_payouts = []
    for col in range(1, 3):
        for raw in range(1, 6):
            if is_xpath_present(driver, f"//*[@id='Netkeiba_Race_Nar_Result']/div[1]/div[3]/div[4]/div/div[1]/div/div[2]/table[1]/tbody/tr[1]/th"):
                xpath_bet_type = f"//*[@id='Netkeiba_Race_Nar_Result']/div[1]/div[3]/div[4]/div/div[1]/div/div[2]/table[{col}]/tbody/tr[{raw}]/th"
                xpath_horse_number = f"//*[@id='Netkeiba_Race_Nar_Result']/div[1]/div[3]/div[4]/div/div[1]/div/div[2]/table[{col}]/tbody/tr[{raw}]/td[1]"
                xpath_payout = f"//*[@id='Netkeiba_Race_Nar_Result']/div[1]/div[3]/div[4]/div/div[1]/div/div[2]/table[{col}]/tbody/tr[{raw}]/td[2]"
            elif is_xpath_present(driver, f"//*[@id='Netkeiba_Race_Nar_Result']/div[1]/div[3]/div[5]/div/div[1]/div/div[2]/table[1]/tbody/tr[1]/th"):
                xpath_bet_type = f"//*[@id='Netkeiba_Race_Nar_Result']/div[1]/div[3]/div[5]/div/div[1]/div/div[2]/table[{col}]/tbody/tr[{raw}]/th"
                xpath_horse_number = f"//*[@id='Netkeiba_Race_Nar_Result']/div[1]/div[3]/div[5]/div/div[1]/div/div[2]/table[{col}]/tbody/tr[{raw}]/td[1]"
                xpath_payout = f"//*[@id='Netkeiba_Race_Nar_Result']/div[1]/div[3]/div[5]/div/div[1]/div/div[2]/table[{col}]/tbody/tr[{raw}]/td[2]"          
            fetch_bet_type_payouts(
                driver=driver,
                race_id=race_id,
                date=date,
                racecourse=racecourse,
                race_number=race_number,
                xpath_bet_type=xpath_bet_type,
                xpath_horse_number=xpath_horse_number,
                xpath_payout=xpath_payout,
                all_payouts=all_payouts
            )
    # 戻り値
    return all_payouts

@log_step
def scrape_horse_result_data(driver, race_id, date, racecourse, race_number, num_horses):
    # 馬
    list_horses = get_all_horses_result(driver, num_horses)
    # 払戻金
    list_payouts = get_all_payouts(driver, race_id, date, racecourse, race_number)
    print(list_payouts)
    # オッズ
    # list_odds = get_all_odds(driver, race_id, num_horses, racecourse)
    list_odds = None
    # 戻り値
    return list_horses, list_payouts, list_odds

@log_step
def scrape_race_data(driver, race_id, date):

    # ステータスの初期値はTrue
    # 存在しないレースページに遷移した場合はFalse
    # （競馬場のセレクタが存在するかどうかで判断）
    status = True

    if driver.find_element(By.CSS_SELECTOR, SELECTOR_RACECOURSE).text != "":

        try:
            # 競馬場
            racecourse = driver.find_element(By.CSS_SELECTOR, SELECTOR_RACECOURSE).text
            # R
            race_number = driver.find_element(By.CSS_SELECTOR, SELECTOR_RACE_NUMBER).text.replace("R", "")
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
            if MODE == "shutuba":
                list_horses = scrape_horse_shutuba_data(driver, num_horses)
                list_payouts = None
                list_odds = None
            elif MODE == "result":
                list_horses, list_payouts, list_odds = scrape_horse_result_data(driver, race_id, date, racecourse, race_number, num_horses)
            # 競馬場が帯広でない場合は予想データを取得する
            reliability = None
            opinion = None
            if MODE == "shutuba" and racecourse != "帯広(ば)":
                if is_xpath_present(driver, df_config_netkeiba.loc["XPATH_CORNER_1"].iloc[0]):
                    # 1人気信頼度
                    if is_xpath_present(driver, df_config_netkeiba.loc["XPATH_RELIABILITY"].iloc[0]):
                        reliability = driver.find_element(By.XPATH, df_config_netkeiba.loc["XPATH_RELIABILITY"].iloc[0]).text
                    # 見解
                    if is_xpath_present(driver, df_config_netkeiba.loc["XPATH_OPINION"].iloc[0]):
                        opinion = driver.find_element(By.XPATH, df_config_netkeiba.loc["XPATH_OPINION"].iloc[0]).text
                    # ポジション予想（1）
                    corner = driver.find_element(By.XPATH, df_config_netkeiba.loc["XPATH_CORNER_1"].iloc[0]).text
                    dic_position_pred = get_position_pred(driver)
                    match corner:
                        case "スタート後":
                            for horse in list_horses:
                                horse.position_1_top_pred = dic_position_pred[f'Horse{horse.horse_number}']["top"]
                                horse.position_1_left_pred = dic_position_pred[f'Horse{horse.horse_number}']["left"]
                        case "2コーナー":
                            for horse in list_horses:
                                horse.position_2_top_pred = dic_position_pred[f'Horse{horse.horse_number}']["top"]
                                horse.position_2_left_pred = dic_position_pred[f'Horse{horse.horse_number}']["left"]
                        case "3コーナー":
                            for horse in list_horses:
                                horse.position_3_top_pred = dic_position_pred[f'Horse{horse.horse_number}']["top"]
                                horse.position_3_left_pred = dic_position_pred[f'Horse{horse.horse_number}']["left"]
                        case "4コーナー":
                            for horse in list_horses:
                                horse.position_4_top_pred = dic_position_pred[f'Horse{horse.horse_number}']["top"]
                                horse.position_4_left_pred = dic_position_pred[f'Horse{horse.horse_number}']["left"]
                    # ポジション予想（2）
                    driver.find_element(By.XPATH, df_config_netkeiba.loc["XPATH_CORNER_2"].iloc[0]).click()
                    corner = driver.find_element(By.XPATH, df_config_netkeiba.loc["XPATH_CORNER_2"].iloc[0]).text
                    dic_position_pred = get_position_pred(driver)
                    # ポジション予想を馬と紐づける
                    match corner:
                        case "スタート後":
                            for horse in list_horses:
                                horse.position_1_top_pred = dic_position_pred[f'Horse{horse.horse_number}']["top"]
                                horse.position_1_left_pred = dic_position_pred[f'Horse{horse.horse_number}']["left"]
                        case "2コーナー":
                            for horse in list_horses:
                                horse.position_2_top_pred = dic_position_pred[f'Horse{horse.horse_number}']["top"]
                                horse.position_2_left_pred = dic_position_pred[f'Horse{horse.horse_number}']["left"]
                        case "3コーナー":
                            for horse in list_horses:
                                horse.position_3_top_pred = dic_position_pred[f'Horse{horse.horse_number}']["top"]
                                horse.position_3_left_pred = dic_position_pred[f'Horse{horse.horse_number}']["left"]
                        case "4コーナー":
                            for horse in list_horses:
                                horse.position_4_top_pred = dic_position_pred[f'Horse{horse.horse_number}']["top"]
                                horse.position_4_left_pred = dic_position_pred[f'Horse{horse.horse_number}']["left"]
                    # ポジション予想（3）
                    driver.find_element(By.XPATH, df_config_netkeiba.loc["XPATH_CORNER_3"].iloc[0]).click()
                    corner = driver.find_element(By.XPATH, df_config_netkeiba.loc["XPATH_CORNER_3"].iloc[0]).text
                    dic_position_pred = get_position_pred(driver)
                    # ポジション予想を馬と紐づける
                    match corner:
                        case "スタート後":
                            for horse in list_horses:
                                horse.position_1_top_pred = dic_position_pred[f'Horse{horse.horse_number}']["top"]
                                horse.position_1_left_pred = dic_position_pred[f'Horse{horse.horse_number}']["left"]
                        case "2コーナー":
                            for horse in list_horses:
                                horse.position_2_top_pred = dic_position_pred[f'Horse{horse.horse_number}']["top"]
                                horse.position_2_left_pred = dic_position_pred[f'Horse{horse.horse_number}']["left"]
                        case "3コーナー":
                            for horse in list_horses:
                                horse.position_3_top_pred = dic_position_pred[f'Horse{horse.horse_number}']["top"]
                                horse.position_3_left_pred = dic_position_pred[f'Horse{horse.horse_number}']["left"]
                        case "4コーナー":
                            for horse in list_horses:
                                horse.position_4_top_pred = dic_position_pred[f'Horse{horse.horse_number}']["top"]
                                horse.position_4_left_pred = dic_position_pred[f'Horse{horse.horse_number}']["left"]
                    # 「騎手傾向を考慮」をチェック
                    driver.find_element(By.XPATH, "//*[@id='dev_check_01_03']").click()
                    # ポジション予想（1）
                    driver.find_element(By.XPATH, df_config_netkeiba.loc["XPATH_CORNER_1"].iloc[0]).click()
                    corner = driver.find_element(By.XPATH, df_config_netkeiba.loc["XPATH_CORNER_1"].iloc[0]).text
                    dic_position_pred = get_position_pred(driver)
                    match corner:
                        case "スタート後":
                            for horse in list_horses:
                                horse.position_1_top_pred_jockey_tendency = dic_position_pred[f'Horse{horse.horse_number}']["top"]
                                horse.position_1_left_pred_jockey_tendency = dic_position_pred[f'Horse{horse.horse_number}']["left"]
                        case "2コーナー":
                            for horse in list_horses:
                                horse.position_2_top_pred_jockey_tendency = dic_position_pred[f'Horse{horse.horse_number}']["top"]
                                horse.position_2_left_pred_jockey_tendency = dic_position_pred[f'Horse{horse.horse_number}']["left"]
                        case "3コーナー":
                            for horse in list_horses:
                                horse.position_3_top_pred_jockey_tendency = dic_position_pred[f'Horse{horse.horse_number}']["top"]
                                horse.position_3_left_pred_jockey_tendency = dic_position_pred[f'Horse{horse.horse_number}']["left"]
                        case "4コーナー":
                            for horse in list_horses:
                                horse.position_4_top_pred_jockey_tendency = dic_position_pred[f'Horse{horse.horse_number}']["top"]
                                horse.position_4_left_pred_jockey_tendency = dic_position_pred[f'Horse{horse.horse_number}']["left"]
                    # ポジション予想（2）
                    driver.find_element(By.XPATH, df_config_netkeiba.loc["XPATH_CORNER_2"].iloc[0]).click()
                    corner = driver.find_element(By.XPATH, df_config_netkeiba.loc["XPATH_CORNER_2"].iloc[0]).text
                    dic_position_pred = get_position_pred(driver)
                    # ポジション予想を馬と紐づける
                    match corner:
                        case "スタート後":
                            for horse in list_horses:
                                horse.position_1_top_pred_jockey_tendency = dic_position_pred[f'Horse{horse.horse_number}']["top"]
                                horse.position_1_left_pred_jockey_tendency = dic_position_pred[f'Horse{horse.horse_number}']["left"]
                        case "2コーナー":
                            for horse in list_horses:
                                horse.position_2_top_pred_jockey_tendency = dic_position_pred[f'Horse{horse.horse_number}']["top"]
                                horse.position_2_left_pred_jockey_tendency = dic_position_pred[f'Horse{horse.horse_number}']["left"]
                        case "3コーナー":
                            for horse in list_horses:
                                horse.position_3_top_pred_jockey_tendency = dic_position_pred[f'Horse{horse.horse_number}']["top"]
                                horse.position_3_left_pred_jockey_tendency = dic_position_pred[f'Horse{horse.horse_number}']["left"]
                        case "4コーナー":
                            for horse in list_horses:
                                horse.position_4_top_pred_jockey_tendency = dic_position_pred[f'Horse{horse.horse_number}']["top"]
                                horse.position_4_left_pred_jockey_tendency = dic_position_pred[f'Horse{horse.horse_number}']["left"]
                    # ポジション予想（3）
                    driver.find_element(By.XPATH, df_config_netkeiba.loc["XPATH_CORNER_3"].iloc[0]).click()
                    corner = driver.find_element(By.XPATH, df_config_netkeiba.loc["XPATH_CORNER_3"].iloc[0]).text
                    dic_position_pred = get_position_pred(driver)
                    # ポジション予想を馬と紐づける
                    match corner:
                        case "スタート後":
                            for horse in list_horses:
                                horse.position_1_top_pred_jockey_tendency = dic_position_pred[f'Horse{horse.horse_number}']["top"]
                                horse.position_1_left_pred_jockey_tendency = dic_position_pred[f'Horse{horse.horse_number}']["left"]
                        case "2コーナー":
                            for horse in list_horses:
                                horse.position_2_top_pred_jockey_tendency = dic_position_pred[f'Horse{horse.horse_number}']["top"]
                                horse.position_2_left_pred_jockey_tendency = dic_position_pred[f'Horse{horse.horse_number}']["left"]
                        case "3コーナー":
                            for horse in list_horses:
                                horse.position_3_top_pred_jockey_tendency = dic_position_pred[f'Horse{horse.horse_number}']["top"]
                                horse.position_3_left_pred_jockey_tendency = dic_position_pred[f'Horse{horse.horse_number}']["left"]
                        case "4コーナー":
                            for horse in list_horses:
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
                for horse in list_horses:
                    if horse.horse_number in list_lead:
                        horse.style_pred = STYLE_MAP.get(1)
                    elif horse.horse_number in list_stalker:
                        horse.style_pred = STYLE_MAP.get(2)
                    elif horse.horse_number in list_chaser:
                        horse.style_pred = STYLE_MAP.get(3)
                    elif horse.horse_number in list_closer:
                        horse.style_pred = STYLE_MAP.get(4)
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
                horses = list_horses,
                payouts = list_payouts,
                odds = list_odds
            )
            # 出力確認
            print(f"📄 年月日: {race_data.race_date} | 競馬場: {race_data.racecourse} | R: {race_data.race_number}")

        except Exception as e:
            print(f"❌ Race ID: {race_id} データ取得に失敗: {e}")
            race_data = None
        
    else:
        race_data = None
        status = False

    # 戻り値
    return race_data, status

@log_step
def scrape_one_day_data(date):
    """
    競馬場とRでループ
    """
    
    while True:
        flg_retry = False

        driver = create_driver()

        # タイムアウト設定
        driver.set_page_load_timeout(30)

        # ログイン
        login_netkeiba(driver)
        # 年月日のURLでアクセス
        date_str = date.strftime("%Y%m%d")
        race_list_url = RACE_LIST_URL + date_str
        try:
            driver.get(race_list_url)
        except:
            print("タイムアウトしたが処理を継続")
            driver.execute_script("window.stop();")
        # 1日の全レースのデータを取得
        all_races_data = []
        # 競馬場のループ
        for place_code in PLACE_MAP:
            # Rのループ
            for race_num in RACE_NUMBERS:
                yyyy = date.strftime("%Y")
                mmdd = date.strftime("%m%d")
                race_id = f"{yyyy}{place_code}{mmdd}{race_num}"
                race_url = f"https://nar.netkeiba.com/race/{MODE}.html?race_id={race_id}"
                try:
                    driver.get(race_url)
                except:
                    print("タイムアウトしたが処理を継続")
                    driver.execute_script("window.stop();")
                time.sleep(1)
                # レースページが正常に取得できていたらレースデータ取得
                if is_xpath_present(driver, f"//*[@id='Netkeiba_Race_Nar_{MODE_CAPITAL}']/div[1]/header/div/h1/a/img"):
                    race_data, status = scrape_race_data(driver, race_id, date)
                else:
                    # driverを終了
                    driver.quit()
                    flg_retry = True
                    break
                # 1Rのrace_dataがNoneだったらその競馬場では開催していないためRのループを抜けたい
                if not status:
                    break
                if race_data is not None:
                    all_races_data.append(race_data)
            if flg_retry:
                break
        if flg_retry:
            continue
        # driverを終了
        driver.quit()
        # 戻り値
        return all_races_data

@log_step
def main_scraper(date_list):
    """
    年月日でループ
    """
    all_days_data = []
    # 年月日のループ
    for date in date_list:
        one_day_data = scrape_one_day_data(date)
        all_days_data.append(one_day_data)
    # 戻り値
    return all_days_data

@log_step
def save_to_horses_csv(final_result, filename):
    """
    スクレイピング結果（Raceオブジェクトのリスト）を平坦化してCSVに出力する
    """
    flattened_data = []

    # final_result は [ [Race1, Race2, ...], [Race1, Race2, ...] ] という2次元リスト
    for day_data in final_result:
        for race in day_data:
            # レース情報の共通項目を辞書化 (horsesリスト以外を取得)
            race_info = {
                "race_id": race.race_id,
                "race_date": race.race_date.strftime("%Y-%m-%d") if isinstance(race.race_date, datetime) else race.race_date,
                "race_time": race.race_time,
                "num_horses": race.num_horses,
                "race_number": race.race_number,
                "racecourse": race.racecourse,
                "ground": race.ground,
                "distance": race.distance,
                "direction": race.direction,
                "reliability": race.reliability,
                # "opinion": race.opinion,
            }

            # そのレースに属する馬のデータを結合
            for horse in race.horses:
                # 馬のデータを辞書化
                horse_info = vars(horse)
                
                # レース情報と馬情報を統合した新しい辞書を作成
                combined_dict = {**race_info, **horse_info}
                flattened_data.append(combined_dict)

    if not flattened_data:
        print("出力するデータがありません。")
        return

    # DataFrameに変換
    df = pd.DataFrame(flattened_data)

    # CSV出力
    df.to_csv(filename, index=False, encoding='cp932')
    print("✅ CSV出力が完了しました")

def move_target_files(source_dir_path, target_dir_path, search_pattern):
    # パスをオブジェクトとして定義
    source_dir = Path(source_dir_path)
    target_dir = Path(target_dir_path)

    # 条件に合うファイルを検索して移動
    files = list(source_dir.glob(search_pattern))

    if not files:
        print("移動対象のファイルがありませんでした")
        return

    for file_path in files:
        # 移動先のフルパスを作成
        destination = target_dir / file_path.name
        
        # 移動実行（同名ファイルがあれば上書き）
        shutil.move(str(file_path), str(destination))
        print(f"移動完了: {file_path.name} -> {target_dir.name}")
#         return data.get("target_shutuba_date")

# %%
### 過去データ移動 ###

move_target_files(rf"C:\keiba\data\{MODE}", rf"C:\keiba\data\{MODE}\old", f"{MODE}*")

# %%
### データ取得 ###

# 今日の年月日
today_str = datetime.now().strftime('%Y%m%d')
# 開始日～終了日
start_date = "20250301"
end_date = "20250331"
date_list = pd.date_range(
    start=start_date,
    end=end_date,
    freq='D'
)
# データ取得
final_result = main_scraper(date_list)

### CSV出力 ###
# shutuba または result
horses_dir = Path.cwd().parent.parent / "data" / MODE
# save_to_horses_csv(final_result, horses_dir / f"{MODE}_{today_str}.csv")
save_to_horses_csv(final_result, horses_dir / f"{MODE}_{start_date}_{end_date}.csv")
# payout と odds
list_payouts = []
# list_odds = []
for one_day_data in final_result:
    for race_data in one_day_data:
        payouts = race_data.payouts
        # odds = race_data.odds
        if payouts is not None:
            list_payouts.extend(payouts)
        # if odds is not None:
        #     list_odds.extend(odds)
df_payout = pd.DataFrame(list_payouts)
payout_dir = Path.cwd().parent.parent / "data" / "payout"
df_payout.to_csv(payout_dir / f"payout_{start_date}_{end_date}.csv", index=False, encoding="cp932")
# df_odds = pd.DataFrame(list_odds)
# odds_dir = Path.cwd().parent.parent / "data" / "odds"
# df_odds.to_csv(odds_dir / f"payout_{start_date}_{end_date}.csv", index=False, encoding="cp932")

# %%
# 地方競馬 https://nar.netkeiba.com/top/race_list.html?kaisai_date=YYYYMMDD
# 波乱度 https://nar.sp.netkeiba.com/race/compatibility.html
# 調子偏差値 https://race.sp.netkeiba.com/barometer/profile.html?kaisai_date=YYYYMMDD


