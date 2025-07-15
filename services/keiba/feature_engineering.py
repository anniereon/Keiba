# services/keiba/feature_engineering.py

import pandas as pd
from .race_analysis import get_time_index_average, get_jockey_place_rate
from keiba.models import RaceStatistics

def build_features(race_details, race_date_map, feature_spec_list):
    rows = []

    for rd in race_details:
        race_id = rd['race_id']
        horse_id = rd['horse_id']
        horse_number = rd['horse_number']
        jockey_id = rd.get('jockey_id')
        race_date = race_date_map.get(race_id)

        if not race_date:
            continue

        row = {
            'race_id': race_id,
            'horse_number': horse_number,
        }

        # 各特徴量を動的に構築
        for idx, spec in enumerate(feature_spec_list):
            f_type = spec['type']
            col_name = f"{f_type}_{idx}"  # 列名の重複防止

            if f_type == 'time_index_average':
                n = spec.get('param', 3)
                value = get_time_index_average(horse_id, race_date, n)
                row[col_name] = value

            elif f_type == 'jockey_place_rate':
                n = spec.get('param', 3)
                value = get_jockey_place_rate(jockey_id, race_date, n)
                row[col_name] = value

            elif f_type == 'conditional_place_rate':
                conditions = spec.get('conditions', [])
                filter_kwargs = {
                    'start_date__lte': race_date,
                    'end_date__gte': race_date,
                    'horse_number': horse_number,
                }

                # RaceStatistics に基づく条件で複勝率を計算
                for cond in conditions:
                    if cond == 'course_id':
                        filter_kwargs['course_id'] = rd.get('course_id')
                    elif cond == 'num_horses':
                        filter_kwargs['num_horses'] = rd.get('num_horses')
                    elif cond == 'race_number':
                        filter_kwargs['race_number'] = rd.get('race_number')
                    elif cond == 'weather':
                        filter_kwargs['weather'] = rd.get('weather')
                    elif cond == 'frame_number':
                        filter_kwargs['frame_number'] = rd.get('frame_number')
                    elif cond == 'style_prediction':
                        filter_kwargs['style_prediction'] = rd.get('style_prediction')

                stats = RaceStatistics.objects.filter(**filter_kwargs).first()
                if stats and stats.sample_size:
                    row[col_name] = round(stats.num_place / stats.sample_size, 3)
                else:
                    row[col_name] = None

        rows.append(row)

    df = pd.DataFrame(rows)

    # 補完処理（必要に応じて）
    for col in df.columns:
        if col.startswith("jockey_place_rate") or col.startswith("conditional_place_rate"):
            df[col] = df[col].fillna(0.0)

    return df
