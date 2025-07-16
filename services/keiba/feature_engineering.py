import pandas as pd
from .race_analysis import get_time_index_average, get_jockey_place_rate
from keiba.models import RaceStatistics

def build_features(race_details, race_date_map, feature_spec_list):
    rows = []

    for rd in race_details:  # rd は RaceDetail モデルのインスタンス
        race = rd.race
        race_id = rd.race_id
        horse_id = rd.horse_id
        jockey_id = rd.jockey_id
        horse_number = rd.horse_number
        frame_number = rd.frame_number
        style = getattr(rd, 'style', None)
        race_date = race_date_map.get(race_id)

        if not race_date:
            continue

        row = {
            # --- race_detailの情報 ---
            'race_id': race_id,
            'horse_id': horse_id,
            'jockey_id': jockey_id,
            'horse_number': horse_number,
            'frame_number': frame_number,
            'odds': rd.odds,
            'popularity': rd.popularity,
            'finish_rank': rd.finish_rank,
            'time_index': rd.time_index,
            'note': rd.note,
            'style_name': style.style_name if style else None,

            # --- raceの情報 ---
            'course_id': race.course_id,
            'num_horses': race.num_horses,
            'race_number': race.race_number,
            'weather_name': getattr(race.weather, 'weather_name', None),
            'track_condition_name': getattr(race.track_condition, 'track_condition_name', None),
            'race_date': race.race_date,
        }

        # 特徴量追加処理
        for idx, spec in enumerate(feature_spec_list):
            f_type = spec['type']
            col_name = f"{f_type}_{idx}"

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

                for cond in conditions:
                    if cond == 'course_id':
                        filter_kwargs['course_id'] = race.course_id
                    elif cond == 'num_horses':
                        filter_kwargs['num_horses'] = race.num_horses
                    elif cond == 'race_number':
                        filter_kwargs['race_number'] = race.race_number
                    elif cond == 'weather':
                        filter_kwargs['weather_id'] = getattr(race.weather, 'weather_id', None)
                    elif cond == 'track_condition':
                        filter_kwargs['track_condition_id'] = getattr(race.track_condition, 'track_condition_id', None)
                    elif cond == 'frame_number':
                        filter_kwargs['frame_number'] = frame_number
                    elif cond == 'style_prediction':
                        filter_kwargs['style_id'] = rd.style_id

                stats = RaceStatistics.objects.filter(**filter_kwargs).first()
                if stats and stats.sample_size:
                    row[col_name] = round(stats.num_place / stats.sample_size, 3)
                else:
                    row[col_name] = None

        rows.append(row)

    df = pd.DataFrame(rows)

    for col in df.columns:
        if col.startswith("jockey_place_rate") or col.startswith("conditional_place_rate"):
            df[col] = df[col].fillna(0.0)

    return df
