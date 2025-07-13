# services/keiba/feature_engineering.py

import pandas as pd
from .race_analysis import get_time_index_average, get_jockey_place_rate

def build_features(race_details, race_date_map, recent_n):
    rows = []

    for rd in race_details:
        race_id = rd['race_id']
        horse_id = rd['horse_id']
        horse_number = rd['horse_number']
        jockey_id = rd.get('jockey_id')
        race_date = race_date_map.get(race_id)

        if not race_date:
            continue

        time_idx_avg = get_time_index_average(horse_id, race_date)
        jockey_rate = get_jockey_place_rate(jockey_id, race_date, recent_n)

        rows.append({
            'race_id': race_id,
            'horse_number': horse_number,
            'jockey_id': jockey_id,
            'time_index_average': time_idx_avg,
            'jockey_place_rate': jockey_rate,
        })

    df = pd.DataFrame(rows)

    # 補完処理（レース単位で中央値）
    df['jockey_place_rate'] = df.groupby('race_id')['jockey_place_rate'] \
                                .transform(lambda x: x.fillna(x.median()))
    df['jockey_place_rate'] = df['jockey_place_rate'].fillna(0.0)

    return df
