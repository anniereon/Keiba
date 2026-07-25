# %% [markdown]
# # インポート

# %%
import time
import re
import pandas as pd
from typing import List, Dict, Any, Tuple
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException

# %% [markdown]
# # 関数

# %%
class NetkeibaScraper:

    def __init__(self):
        # 初期設定
        self.path_chrome_driver = "C:\\Users\\ryo\\AppData\\Local\\SeleniumBasic\\chromedriver.exe"
        self.service = Service(self.path_chrome_driver)
        self.options = webdriver.ChromeOptions()
        self.driver = webdriver.Chrome(service=self.service, options=self.options)
        self.driver.set_page_load_timeout(30)
        self.max_try_num = 5
        self.xpath_to_check = "//*[@id='page']/header/div/h1/a/img"
        # ログイン
        self.login_url = "https://regist.netkeiba.com/?pid=login"
        # マッピング
        self.style_map = {1: "逃げ", 2: "先行", 3: "差し", 4: "追込"}

    def _is_xpath_present(self, xpath) -> bool:
        return len(self.driver.find_elements(By.XPATH, xpath)) > 0

    def _is_css_selector_present(self, css_selector) -> bool:
        return len(self.driver.find_elements(By.CSS_SELECTOR, css_selector)) > 0

    def login(self, login_id, password) -> bool:
        try_num = 0
        while True:
            try_num = try_num + 1
            if try_num > self.max_try_num:
                break
            # ログイン画面へ遷移
            try:
                self.driver.get(self.login_url)
            except TimeoutException:
                self.driver.execute_script("window.stop();")
            time.sleep(1)
            if not self._is_xpath_present(self.xpath_to_check):
                continue
            # ログイン情報の入力と送信
            try:
                name_login_id = "login_id"
                self.driver.find_element(By.NAME, name_login_id).send_keys(login_id)
                name_password = "pswd"
                pw_field = self.driver.find_element(By.NAME, name_password)
                pw_field.send_keys(password)
                pw_field.send_keys(Keys.ENTER)
            except TimeoutException:
                self.driver.execute_script("window.stop();")
            time.sleep(1)
            status = True
            break
        status = False
        return status

    def scrape_horse_data_shutuba(self, num_horses) -> List[Dict[str, Any]]:
        list_horses = []
        for i in range(1, num_horses + 1):
            try:
                xpath_horse_number = "//*[@id='tr_" + str(i) + "']/td[2]"
                if self._is_xpath_present(xpath_horse_number):
                    horse_number = self.driver.find_element(By.XPATH, xpath_horse_number).text.strip()
                elif self._is_xpath_present(f"//*[@id='Netkeiba_Race_Nar_Shutuba']/div[1]/div[3]/div[3]/table/tbody/tr[{i}]/td[2]"):
                    horse_number = self.driver.find_element(By.XPATH, f"//*[@id='Netkeiba_Race_Nar_Shutuba']/div[1]/div[3]/div[3]/table/tbody/tr[{i}]/td[2]").text.strip()
                    horse = {"horse_number": horse_number}
                    list_horses.append(horse)
                    # all_horses_data.append(Horse_Shutuba(None, None, None, None, None, None, None, None, horse_number, None))
                    continue
                else:
                    break
                # 馬
                xpath_horse_link_1 = "/html/body/div[1]/div[3]/div[3]/table/tbody/tr[" + str(i) + "]/td[4]/div/div/span[2]/a"
                xpath_horse_link_2 = "/html/body/div[1]/div[3]/div[3]/table/tbody/tr[" + str(i) + "]/td[4]/div/div/span/a"
                xpath_horse_link = xpath_horse_link_1 if self._is_xpath_present(xpath_horse_link_1) else xpath_horse_link_2                
                horse_link_elem = self.driver.find_element(By.XPATH, xpath_horse_link)
                horse_name = horse_link_elem.text.strip()
                horse_id = horse_link_elem.get_attribute("href").rstrip("/").split("/")[-1]
                # 騎手
                xpath_jockey_link = "//*[@id='tr_" + str(i) + "']/td[7]/span/a"
                jockey_link_elem = self.driver.find_element(By.XPATH, xpath_jockey_link)
                jockey_name = jockey_link_elem.text.strip()
                jockey_id = jockey_link_elem.get_attribute("href").rstrip("/").split("/")[-1]
                # 単勝人気
                popularity = self.driver.find_element(By.XPATH, "//*[@id='tr_" + str(i) + "']/td[11]").text
                # 単勝オッズ
                odds = self.driver.find_element(By.XPATH, "//*[@id='tr_" + str(i) + "']/td[10]").text
                # 性齢
                sex_and_age = self.driver.find_element(By.XPATH, "//*[@id='tr_" + str(i) + "']/td[5]/span").text
                # 体重
                weight = self.driver.find_element(By.XPATH, "//*[@id='tr_" + str(i) + "']/td[9]").text
                # 枠番
                frame_number = self.driver.find_element(By.XPATH, "//*[@id='tr_" + str(i) + "']/td[1]").text
                # 斤量
                impost = self.driver.find_element(By.XPATH, "//*[@id='tr_" + str(i) + "']/td[6]").text
                # 後3F
                xpath_last_3_furlongs_pred = "//*[@id='ai_tenkai']/div/section/div[3]/table[1]/tbody/tr[" + str(i) + "]/td[3]"
                last_3_furlongs_pred = self.driver.find_element(By.XPATH, xpath_last_3_furlongs_pred).text if self._is_xpath_present(xpath_last_3_furlongs_pred) else None
                print(f"  馬番{i}: データ取得成功")
                # リストに追加
                horse = {
                    "horse_id": horse_id,
                    "horse_name": horse_name,
                    "jockey_id": jockey_id,
                    "jockey_name": jockey_name,
                    "popularity": popularity,
                    "odds": odds,
                    "sex_and_age": sex_and_age,
                    "weight": weight,
                    "horse_number": horse_number,
                    "frame_number": frame_number,
                    "impost": impost,
                    "last_3_furlongs_pred": last_3_furlongs_pred,
                }
                list_horses.append(horse)
            except Exception as e:
                print(f"  馬番{i}: データ取得失敗 ({e})")
        return list_horses

    def get_race_shutuba_data(self, race_id) -> Tuple[bool, pd.DataFrame]:
        status = True
        selector_racecourse = "#Netkeiba_Race_Nar_Shutuba > div.Wrap.fc > div.RaceColumn01 > div > div.RaceMainColumn > div.RaceList_NameBox > div.RaceList_Item02 > div.RaceData02 > span:nth-child(2)"
        if self.driver.find_element(By.CSS_SELECTOR, selector_racecourse).text == "":
            status = False
            return status, None
        # 年月日
        race_date = f"{race_id[:4]}/{race_id[6:8]}/{race_id[8:10]}"
        # 競馬場
        racecourse = self.driver.find_element(By.CSS_SELECTOR, selector_racecourse).text
        # レース番号
        selector_race_number = "#Netkeiba_Race_Nar_Shutuba > div.Wrap.fc > div.RaceColumn01 > div > div.RaceMainColumn > div.RaceList_NameBox > div.RaceList_Item01 > div"
        race_number = self.driver.find_element(By.CSS_SELECTOR, selector_race_number).text.replace("R", "")
        # 頭数
        selector_num_horses = "#Netkeiba_Race_Nar_Shutuba > div.Wrap.fc > div.RaceColumn01 > div > div.RaceMainColumn > div.RaceList_NameBox > div.RaceList_Item02 > div.RaceData02 > span:nth-child(5)"
        num_horses = int(self.driver.find_element(By.CSS_SELECTOR, selector_num_horses).text.replace("頭", "").strip())
        # 発走時刻, グラウンド, 距離, 方向
        xpath_race_info = "//*[@id='Netkeiba_Race_Nar_Shutuba']/div[1]/div[2]/div/div[1]/div[3]/div[2]/div[2]"
        race_info = self.driver.find_element(By.XPATH, xpath_race_info).text.strip()
        parts = [p.strip() for p in race_info.split("/")]            
        race_time = parts[0].replace("発走", "").strip()
        ground_info = parts[1]        
        ground_match = re.search(r"(芝|ダ)", ground_info)
        ground = ground_match.group(1) if ground_match else "不明"
        distance_match = re.search(r"(\d+)m", ground_info)
        distance = int(distance_match.group(1)) if distance_match else -1
        direction_match = re.search(r"\((左|右)\)", ground_info)
        direction = direction_match.group(1) if direction_match else "不明"
        # 馬
        list_horses = self.scrape_horse_data_shutuba(num_horses)
        # レース展開予想
        if racecourse != "帯広(ば)":
            # 旧版の展開予想に切り替え
            self.driver.find_element(By.XPATH, "//*[@id='Netkeiba_Race_Nar_Shutuba']/div[1]/div[3]/div[14]/div/div/label/span").click()
            list_styles = {1: [], 2: [], 3: [], 4: []}
            for row_idx in range(1, 5):
                for i in range(1, num_horses + 1):
                    xp = f"//*[@id='Netkeiba_Race_Nar_Shutuba']/div[1]/div[3]/div[16]/table/tbody/tr[{row_idx}]/td/div[{i}]/span[1]"
                    if self._is_xpath_present(xp):
                        list_styles[row_idx].append(self.driver.find_element(By.XPATH, xp).text)
                    else:
                        break
            for horse in list_horses:
                for s_code, h_nums in list_styles.items():
                    if horse["horse_number"] in h_nums:
                        horse["style_pred"] = self.style_map.get(s_code)
        # DataFrame型に成形
        df = pd.DataFrame(list_horses)
        columns = [
            ("race_id", race_id),
            ("race_date", race_date),
            ("racecourse", racecourse),
            ("race_number", race_number),
            ("num_horses", num_horses),
            ("ground", ground),
            ("race_time", race_time),
            ("distance", distance),
            ("direction", direction),
        ]
        for i, (col_name, value) in enumerate(columns):
            df.insert(i, col_name, value)
        return df

    # def get_race_result_data(self) -> str:
    #     return "shutuba"

    def get_nar_race_data_by_race_id(self, login_id, password, mode, list_race_id) -> pd.DataFrame:
        # ログイン
        self.login(login_id=login_id, password=password)
        # レースデータ取得
        list_df_race = []
        for race_id in list_race_id:
            # レースページに遷移
            race_url = f"https://nar.netkeiba.com/race/{mode}.html?race_id={race_id}"
            try:
                self.driver.get(race_url)
            except:
                self.driver.execute_script("window.stop();")
            time.sleep(1)
            # データ取得
            if mode == "shutuba":
                df_race = self.get_race_shutuba_data(race_id)
            # elif mode == "result":
                # df = self.get_race_result_data()
            list_df_race.append(df_race)
        df_races = pd.concat(list_df_race, ignore_index=True)
        # スクレイピング終了
        self.driver.quit()
        return df_races


