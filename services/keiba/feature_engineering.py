import pandas as pd
from django.forms.models import model_to_dict
from .race_analysis import get_time_index_average, get_jockey_place_rate
from keiba.models import RaceStatistics

def build_features(race_details, race_date_map, feature_spec_list):
    rows = []

    for rd in race_details:
        race = rd.race
        race_id = rd.race_id
        horse_id = rd.horse_id
        jockey_id = rd.jockey_id
        horse_number = rd.horse_number
        frame_number = rd.frame_number
        style = getattr(rd, 'style', None)
        race_date = race_date_map.get(race_id)

        if not race_date:
            continue  # race_date_map に存在しない場合はスキップ

        base_data = model_to_dict(rd)

        # model_to_dict に含まれない関連や追加情報を上書き・追加
        base_data.update({
            'race_id': race_id,
            'horse_number': horse_number,
            'race_date': race_date,
            'course_id': race.course_id if race else None,
            'num_horses': race.num_horses if race else None,
            'race_number': race.race_number if race else None,
            'weather_name': getattr(race.weather, 'weather_name', None),
            'weather_id': getattr(race.weather, 'weather_id', None),
            'track_condition_name': getattr(race.track_condition, 'track_condition_name', None),
            'track_condition_id': getattr(race.track_condition, 'track_condition_id', None),
            'style_name': style.style_name if style else None,
            # position_1〜4、weight関連など、RaceDetailモデルに定義があれば model_to_dict で取得されるはずなので省略可能
            # ただし不足があれば以下のように明示的に
            'position_1': getattr(rd, 'position_1', None),
            'position_2': getattr(rd, 'position_2', None),
            'position_3': getattr(rd, 'position_3', None),
            'position_4': getattr(rd, 'position_4', None),
            'weight': getattr(rd, 'weight', None),
            'weight_delta': getattr(rd, 'weight_delta', None),
            'impost': getattr(rd, 'impost', None),
            'last_3_furlongs': getattr(rd, 'last_3_furlongs', None),
            'finish_time': getattr(rd, 'finish_time', None),
        })

        for idx, spec in enumerate(feature_spec_list):
            f_type = spec['type']
            col_name = f"{f_type}_{idx}"

            if f_type == 'time_index_average':
                n = spec.get('param', 3)
                value = get_time_index_average(horse_id, race_date, n) if horse_id else None

            elif f_type == 'jockey_place_rate':
                n = spec.get('param', 3)
                value = get_jockey_place_rate(jockey_id, race_date, race.race_number, n) if jockey_id else None

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
                        filter_kwargs['style_id'] = rd.style.style_id if rd.style else None

                stats = RaceStatistics.objects.filter(**filter_kwargs).first()
                if stats and stats.sample_size:
                    value = round(stats.num_place / stats.sample_size, 3)
                else:
                    value = None

            else:
                value = None

            base_data[col_name] = value

        rows.append(base_data)

    df = pd.DataFrame(rows)
    return df
