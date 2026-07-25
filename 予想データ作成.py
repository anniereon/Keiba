# %%
### インポート ###
import numpy as np
import pandas as pd
from datetime import datetime
from pathlib import Path
import xgboost as xgb
import glob
import os
import re
import sys
import shutil
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

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
# ==========
# 設定
# ==========

### 設定ファイル ###
config_path = Path.cwd().parent / "config.xlsx"
df_config_style = pd.read_excel(config_path, sheet_name="style", header=0)
df_config_features = pd.read_excel(config_path, sheet_name="features", header=0)
df_config_data_model = pd.read_excel(config_path, sheet_name="data_model", header=0)
df_config_gmail = pd.read_excel(config_path, sheet_name="gmail", header=0)
# 脚質
STYLE_MAP = df_config_style.set_index('key')['value'].to_dict()
print(f'脚質: {STYLE_MAP}')
REVERSE_STYLE_MAP = {v: k for k, v in STYLE_MAP.items()}
# モデルのデータ
MIN_RECORDS_MAP = df_config_data_model.set_index('num_horses')['min_records'].to_dict()
print(f'最小許容有効レコード数: {MIN_RECORDS_MAP}')
# 最小騎手出走数
FEATURES_MAP = df_config_features.set_index('key')['value'].to_dict()
MIN_JOCKEY_RECORDS = FEATURES_MAP.get('min_jockey_records')
print(f'最小騎手出走数: {MIN_JOCKEY_RECORDS}')
if not is_jupyter() and len(sys.argv) > 1:
    MODE_PRED = sys.argv[1]   # 仮"bck"または本"prd"
else:
    MODE_PRED = "bck"
print(MODE_PRED)
# メール
GMAIL_MAP = df_config_gmail.set_index('key')['value'].to_dict()
# 年月日
today_str = datetime.now().strftime('%Y%m%d')
print(today_str)

# %%
# ========
# メソッド
# ========

# def create_dl_model(input_dim):
#     model = Sequential([
#         Dense(128, activation='relu', input_shape=(input_dim,)),
#         Dropout(0.5),
#         Dense(64, activation='relu'),
#         Dropout(0.5),
#         Dense(32, activation='relu'),
#         Dropout(0.5),
#         Dense(1, activation='sigmoid') 
#     ])
#     model.compile(optimizer=Adam(learning_rate=0.001), loss='binary_crossentropy', metrics=['accuracy'])
#     return model

def calculate_recent_time_index_avg(row, df):
    """
    特定の馬(horse_id)の直近2走の平均time_indexを計算する
    """
    # 1. dfから同じhorse_id、かつ今回のrace_dateより前のデータを抽出
    # ※昇順にソート（直近が下に来るようにする）
    df_filtered = df[
        (df['horse_id'] == row['horse_id']) & 
        (df['race_date'] < row['race_date'])
    ].sort_values('race_date')
    # 2. time_indexがNaNでないものを抽出
    df_valid = df_filtered.dropna(subset=['time_index'])
    # 3. 有効なデータが2つ以上あるか判定
    if len(df_valid) >= 2:
        # 下から2つ（直近2走）を選択して平均を出す
        avg_index = df_valid.tail(2)['time_index'].mean()
        return avg_index
    else:
        # 2回未満ならNaN
        return np.nan

def calculate_jockey_win_rate(row, df):
    """
    特定の騎手(jockey_id)の直近 MIN_JOCKEY_RECORDS 走（有効データ）の勝率を計算する
    """
    # 1. その騎手の、今回のレース日より前のデータを抽出
    # 2. かつ finish_rank が NaN でないものに絞る
    # 3. 日付順（昇順）にソート
    df_jockey_past = df[
        (df['jockey_id'].astype(str).str.zfill(5) == str(row['jockey_id']).zfill(5)) & 
        (df['race_date'] < row['race_date']) &
        (df['finish_rank'].notna())
    ].sort_values('race_date')
    
    # 4. 直近recent_num個のレコードを抽出（recent_num個なければ全件）
    df_recent = df_jockey_past.tail(MIN_JOCKEY_RECORDS)
    
    # レコード数をカウント（分母）
    total_count = len(df_recent)

    if total_count == 0:
        return np.nan
    
    # 5. finish_rank が 3 以下であるレコード数をカウント（分子）
    win_count = (df_recent['finish_rank'].astype(int) <= 3).sum()
    
    # 勝率を計算して返す
    return win_count / total_count

def predict_position_half_type(group):
    '''
    以下でソート
    1. 脚質順
    2. タイム指数順
    '''
    group = group.sort_values(["style_id", "time_index_avg_recent_2"], ascending=[True, False])
    n = len(group)
    mid = n // 2
    res = pd.Series(index=group.index, dtype=str)
    res.iloc[:mid] = "front"
    res.iloc[mid:] = "back"
    return res

def check_race_validity(group, target_courses):
    # --- 1. コース条件のチェック ---
    course_info = (
        group['racecourse'].iloc[0], 
        group['ground'].iloc[0], 
        group['distance'].iloc[0], 
        group['direction'].iloc[0]
    )
    if course_info not in target_courses:
        return False
    # --- 2. 頭数のチェック ---
    num_horses = group['num_horses'].iloc[0]
    if num_horses not in MIN_RECORDS_MAP:
        return False
    # --- 3. 有効なデータ数が MIN_RECORDS_MAP の基準を満たしているかチェック ---
    min_required = MIN_RECORDS_MAP.get(num_horses)
    valid_row_count = group[['time_index_pred_from_race_avg', f'jockey_top3_rate_recent_{MIN_JOCKEY_RECORDS}']].notna().all(axis=1).sum()
    if valid_row_count < min_required:
        return False
    # 上記でFalseをreturnしなかった場合は条件をクリア
    return True

def filter_valid_data(df, target_courses):
    """
    メインのフィルタリング実行関数
    """
    # 統合したチェック関数を適用
    # 引数を渡すために lambda を使用
    valid_mask = df.groupby('race_id').apply(
        lambda x: check_race_validity(x, target_courses)
    )
    # 有効なrace_idだけを抽出
    valid_race_ids = valid_mask[valid_mask].index
    df_filtered = df[df['race_id'].isin(valid_race_ids)].copy()
    
    return df_filtered

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

def create_html_body(df_pred):
    if df_pred.empty:
        return """
        <div style="font-family: sans-serif; max-width: 800px; margin: auto; border: 1px solid #ddd; padding: 20px;">
            <h2>予想なし</h2>
        </div>
        """

    tables = []

    # レースごとにテーブルを作成
    for (racecourse, race_number), df_race in df_pred.groupby(
        ["racecourse", "race_number"], sort=False
    ):

        df_race = df_race.sort_values("finish_rank_pred")

        race_date = df_race["race_date"].iloc[0]
        race_time = df_race["race_time"].iloc[0]

        display_df = (
            df_race[
                ["finish_rank_pred", "horse_number", "style_pred"]
            ]
            .rename(
                columns={
                    "finish_rank_pred": "着順予想",
                    "horse_number": "馬番",
                    "style_pred": "脚質予想",
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

            rank = row["着順予想"]

            if rank in [1, 2, 3]:
                row_color = "#E3F2FD"   # 薄い水色
            else:
                row_color = "white"

            html += f'<tr style="background:{row_color};">'

            # 着順予想
            html += f"""
                <td style="padding:8px; border:1px solid #ddd; font-weight:bold;">
                    {row["着順予想"]}
                </td>
            """

            # 馬番
            html += f"""
                <td style="padding:8px; border:1px solid #ddd;">
                    {row["馬番"]}
                </td>
            """

            # 脚質予想
            if row["脚質予想"] == "追込":
                style = "color:#0d6efd; font-weight:bold;"
            else:
                style = ""

            html += f"""
                <td style="padding:8px; border:1px solid #ddd; {style}">
                    {row["脚質予想"]}
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
                {race_date} {race_time}　{racecourse} {race_number}R
            </h3>
            {html}
        </div>
        """)

    html_body = f"""
    <div style="font-family:sans-serif; max-width:800px; margin:auto; border:1px solid #ddd; padding:20px;">
        <h2>予想一覧</h2>
        {''.join(tables)}
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
# ======================
# 本予測 / 仮予測
# ======================

if MODE_PRED == "prd":
    print("本予測")
    path_schedule = Path.cwd().parent.parent / "data" / "pred" / "schedule.csv"
    df_schedule_raw = pd.read_csv(path_schedule, encoding="cp932")
    df_schedule = df_schedule_raw.copy()
    race_ids = df_schedule.loc[df_schedule["status"] == "本予測待ち", "race_id"]
    if len(race_ids) == 0:
        sys.exit()
    print(f"予測対象：{race_ids}")
elif MODE_PRED == "bck":
    print("仮予測")
    move_target_files(rf"C:\keiba\data\pred", rf"C:\keiba\data\pred\old", f"pred*")
    move_target_files(rf"C:\keiba\data\pred", rf"C:\keiba\data\pred\old", f"schedule*")

# %%
# ===============
# trainデータ
# ===============

### trainデータ読み込み ###
print("trainデータ読み込み：開始")
train_path = Path.cwd().parent.parent / "data" / "train" / "train.csv"
df_train = pd.read_csv(train_path, header=0, encoding='cp932')
print("trainデータ読み込み：終了")

### 欠損値を埋める ###
# print("NaN補完：開始")
# df_train["time_index_pred_from_race_avg"] = df_train["time_index_pred_from_race_avg"].fillna(0)
# df_train[f'jockey_top3_rate_recent_{MIN_JOCKEY_RECORDS}_from_race_avg'] = df_train[f'jockey_top3_rate_recent_{MIN_JOCKEY_RECORDS}_from_race_avg'].fillna(0)
# print("NaN補完：終了")

# %%
# ===============
# historyデータ
# ===============

### historyデータ読み込み ###
print("historyデータ読み込み：開始")
history_path = Path.cwd().parent.parent / "data" / "history" / "history.csv"
df_history = pd.read_csv(history_path, header=0, encoding='cp932')
print("historyデータ読み込み：終了")

### 帯広(ば)を除外 ###
df_history = df_history[df_history["racecourse"] != "帯広(ば)"]

# %%
# ===============
# shutubaデータ
# ===============

### shutubaデータ読み込み ###
print("shutubaデータ読み込み：開始")
if MODE_PRED == "prd":
    list_df_tmp = []
    for race_id in race_ids:
        path_shutuba = Path.cwd().parent.parent / "data" / "shutuba" / f"shutuba_{race_id}.csv"
        df_tmp = pd.read_csv(path_shutuba, encoding="cp932")
        list_df_tmp.append(df_tmp)
    df_shutuba_raw = pd.concat(list_df_tmp, ignore_index=True)
elif MODE_PRED == "bck":
    path_shutuba = Path.cwd().parent.parent / "data" / "shutuba" / f"shutuba_{today_str}.csv"
    df_shutuba_raw = pd.read_csv(path_shutuba, encoding="cp932")
print("shutubaデータ読み込み：終了")

# %%
# ===============
# 説明変数作成
# ===============

print("説明変数作成：開始")
df_pred = df_shutuba_raw.copy()

### 準備（型変換）###
print("    準備（型変換）：開始")
df_train['horse_id'] = df_train['horse_id'].astype(str).str.replace('.0', '', regex=False)
df_history['horse_id'] = df_history['horse_id'].astype(str).str.replace('.0', '', regex=False)
df_pred['horse_id'] = df_pred['horse_id'].astype(str).str.replace('.0', '', regex=False)
print("    準備（型変換）：終了")

### 帯広(ば)を除外 ###
print("    対象レース絞り込み：開始")
df_pred = df_pred[df_pred["racecourse"] != "帯広(ば)"]
print("    対象レース絞り込み：終了")

### 予想タイム指数 ###
print("    予想タイム指数計算：開始")
# 直近過去2レースのタイム指数の平均値
df_pred['time_index_avg_recent_2'] = df_pred.apply(calculate_recent_time_index_avg, axis=1, args=(df_history,))
df_pred['time_index_avg_recent_2_race_avg'] = df_pred.groupby('race_id')['time_index_avg_recent_2'].transform('mean')
df_pred['time_index_pred_from_race_avg'] = df_pred['time_index_avg_recent_2'] - df_pred['time_index_avg_recent_2_race_avg']
print("    予想タイム指数計算：終了")

### 騎手複勝率 ###
print("    騎手複勝率計算：開始")
df_pred[f'jockey_top3_rate_recent_{MIN_JOCKEY_RECORDS}'] = df_pred.apply(calculate_jockey_win_rate, axis=1, args=(df_history,))
df_pred[f'jockey_top3_rate_recent_{MIN_JOCKEY_RECORDS}_race_avg'] = df_pred.groupby('race_id')[f'jockey_top3_rate_recent_{MIN_JOCKEY_RECORDS}'].transform('mean')
df_pred[f'jockey_top3_rate_recent_{MIN_JOCKEY_RECORDS}_from_race_avg'] = df_pred[f'jockey_top3_rate_recent_{MIN_JOCKEY_RECORDS}'] - df_pred[f'jockey_top3_rate_recent_{MIN_JOCKEY_RECORDS}_race_avg']
print("    騎手複勝率計算：終了")

### 欠損値を埋める ###
# print("    NaN補完：開始")
# df_pred["time_index_pred_from_race_avg"] = df_pred["time_index_pred_from_race_avg"].fillna(0)
# df_pred[f'jockey_top3_rate_recent_{MIN_JOCKEY_RECORDS}_from_race_avg'] = df_pred[f'jockey_top3_rate_recent_{MIN_JOCKEY_RECORDS}_from_race_avg'].fillna(0)
# print("    NaN補完：終了")

### コース × 頭数 × 馬番別勝率
print("    コース × 頭数 × 馬番別勝率計算：開始")
keys = ['racecourse', 'ground', 'distance', 'direction', 'num_horses', 'horse_number']
stats_df = df_history.groupby(keys)['finish_rank'].agg([
    ('win_count', lambda x: (pd.to_numeric(x, errors='coerce') == 1).sum()),
    ('total_count', 'count')
]).reset_index()
stats_df['condition_win_rate'] = stats_df['win_count'] / stats_df['total_count']
df_pred = pd.merge(df_pred, stats_df[keys + ['condition_win_rate']], on=keys, how='left')
print("    コース × 頭数 × 馬番別勝率計算：終了")

### ポジションに紐づく勝率計算 ###
print("    ポジション（front / back）予想作成：開始")
df_pred["style_id"] = df_pred["style_pred"].map(REVERSE_STYLE_MAP)

df_pred = df_pred.sort_values(["race_id", "style_id", "time_index_avg_recent_2"], ascending=[True, True, False])
df_pred['temp_rank'] = df_pred.groupby("race_id").cumcount()
df_pred["position_half_type_pred"] = np.where(
    df_pred['temp_rank'] < (df_pred['num_horses'] // 2), "front", "back"
)
df_pred = df_pred.drop(columns=['temp_rank'])
print("    ポジション（front / back）予想作成：終了")

print("    予想ポジション別勝率計算：開始")
keys = ['racecourse', 'ground', 'distance', 'direction', 'num_horses', 'position_half_type_pred']
stats = df_train.groupby(keys)['finish_rank'].agg([
    ('win_count', lambda x: (pd.to_numeric(x, errors='coerce') == 1).sum()),
    ('total_count', 'count')
]).reset_index()
stats['position_half_type_win_rate'] = stats['win_count'] / stats['total_count']
# predデータのコース×頭数×(front/back)に紐づく勝率を割り当てる
df_pred = pd.merge(
    df_pred,
    stats[keys + ['position_half_type_win_rate']], 
    on=keys, 
    how='left'
)
print("    予想ポジション別勝率計算：終了")

print("    予想ポジション比率別勝率計算：開始")
df_train['front_count'] = df_train.groupby('race_id')['position_half_type_pred'].transform(lambda x: (x == 'front').sum())
df_train['back_count'] = df_train.groupby('race_id')['position_half_type_pred'].transform(lambda x: (x == 'back').sum())
keys = ['num_horses', 'front_count', 'back_count', 'position_half_type_pred']
stats = df_train.groupby(keys)['finish_rank'].agg(
    composition_pos_win_rate = lambda x: (pd.to_numeric(x, errors='coerce') == 1).sum() / len(x)
).reset_index()
df_pred['front_count'] = df_pred.groupby('race_id')['position_half_type_pred'].transform(lambda x: (x == 'front').sum())
df_pred['back_count'] = df_pred.groupby('race_id')['position_half_type_pred'].transform(lambda x: (x == 'back').sum())
df_pred = pd.merge(df_pred, stats, on=keys, how='left')
print("    予想ポジション比率別勝率計算：終了")

if df_pred.empty:
    print('予想対象のレースがありません')

print("説明変数作成：終了")

# %%
# ==============
# 目的変数作成
# ==============

df_train['flg_finish_rank_top3'] = (df_train["finish_rank"] <= 3).astype(int)

# %%
# ===========================================
# 説明変数が欠損している馬を含むレースを除外
# ===========================================

def delete_feature_missing_race(df, features):
    df = df.copy()
    df["is_missing_horse"] = (df["horse_id"].notna() & df[features].isna().any(axis=1))
    missing_counts_per_race = (df.groupby("race_id")["is_missing_horse"].sum())
    valid_race_ids = (missing_counts_per_race[missing_counts_per_race == 0].index.tolist())
    df = df[df["race_id"].isin(valid_race_ids)].copy()
    return df

# 説明変数
features = [
    'time_index_pred_from_race_avg',
    f'jockey_top3_rate_recent_{MIN_JOCKEY_RECORDS}_from_race_avg',
    # 'condition_win_rate',
    'position_half_type_win_rate',
    'composition_pos_win_rate'
]

df_train = delete_feature_missing_race(df_train, features)
df_pred = delete_feature_missing_race(df_pred, features)

# %%
df_pred

# %%
# ==============
# 学習・予想
# ==============

if not df_pred.empty:

    # 全レースの予想を格納するリスト
    all_processed_races = []
    # --- 頭数ごとにループ ---
    for num_horses in [8, 9, 10, 11, 12]:
        print(f"{num_horses}頭：開始")
        # 指定した頭数のデータを抽出
        train_sub = df_train[df_train['num_horses'] == num_horses].copy()
        df_pred_sub = df_pred[df_pred['num_horses'] == num_horses].copy()
        # 予測対象がない場合は次の頭数へ
        if df_pred_sub.empty:
            print(f"    {num_horses}頭の予測対象データがないためスキップ")
            continue
        ### モデル作成 ###
        model = xgb.XGBClassifier(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=3,
            random_state=42,
            objective="binary:logistic",
            eval_metric="logloss"
        )
        ### 学習 ###
        print(f"    学習：開始")
        X_train = train_sub[features]
        y_train = train_sub['flg_finish_rank_top3']
        model.fit(X_train, y_train)
        print(f"    学習：終了")
        ### 予想 ###
        print(f"    予想：開始")        
        X_pred = df_pred_sub[features]
        df_pred_sub["pred_prob"] = model.predict_proba(X_pred)[:, 1]
        df_pred_sub["pred_prob"] = model.predict_proba(X_pred)[:, 1]
        df_pred_sub["finish_rank_pred"] = (df_pred_sub.groupby("race_id")["pred_prob"].rank(ascending=False, method="first").astype(int))
        print(f"    予想：終了")
        all_processed_races.append(df_pred_sub)
        print(f"{num_horses}頭：終了")
    # --- 全ての頭数の結果を統合 ---
    if all_processed_races:
        print("予想対象レースあり")
        # 結合
        df_pred = pd.concat(all_processed_races).reset_index(drop=True)
        # 不要なカラムを削除
        df_pred.drop(columns='style_id')
        # ファイル出力
        if MODE_PRED == "prd":
            # 本予測の場合はレースごとにファイル出力
            for df_pred_num_horses in all_processed_races:
                df_pred_num_horses.drop(columns='style_id')
                for race_id, df_race in df_pred_num_horses.groupby("race_id"):
                    path_pred = Path.cwd().parent.parent / "data" / "pred" / f"pred_{race_id}.csv"
                    df_race.to_csv(path_pred, index=False, encoding="cp932")
                    df_schedule.loc[df_schedule["race_id"] == race_id, "status"] = "本予測完了"
            df_schedule.to_csv(path_schedule, index=False, encoding="cp932")
        elif MODE_PRED == "bck":
            # 仮予測の場合はまとめてファイル出力
            df_pred = pd.concat(all_processed_races).reset_index(drop=True)
            df_pred.drop(columns='style_id')
            path_pred = Path.cwd().parent.parent / "data" / "pred" / "pred.csv"
            df_pred.to_csv(path_pred, index=False, encoding="cp932")
            path_schedule = Path.cwd().parent.parent / "data" / "pred" / "schedule.csv"
            df_schedule = (df_pred[["race_id", "race_date", "race_time", "race_number", "racecourse"]].drop_duplicates(subset=["race_id"]))
            df_schedule["status"] = "仮予測完了"
            df_schedule.to_csv(path_schedule, index=False, encoding="cp932")
    else:
        print("予想対象レースなし")

# %%
# ================
# メール送信
# ================

if MODE_PRED == "bck":
    # 宛先
    to_address = GMAIL_MAP.get('to')
    # 件名
    if df_pred.empty:
        subject = "【競馬ツール】仮予測【－】"
    else:
        subject = "【競馬ツール】仮予測【〇】"
    # 本文
    body_html = create_html_body(df_pred)
    # 送信
    send_gmail(subject, body_html, to_address)


