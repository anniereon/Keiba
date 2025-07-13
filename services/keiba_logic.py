from django.http import HttpResponse
from ..models import Race, RaceDetail
import csv
import logging
import pandas as pd
import statistics

logger = logging.getLogger(__name__)

def get_race_ids_between(start_date, end_date):
    return Race.objects.filter(
        race_date__range=(start_date, end_date)
    ).values_list('race_id', flat=True)

def get_race_details(race_ids):
    return RaceDetail.objects.filter(
        race_id__in=race_ids
    ).values('race_id', 'horse_id', 'horse_number', 'jockey_id')

def get_race_date_map(race_details):
    race_ids = [rd['race_id'] for rd in race_details]
    race_dates = Race.objects.filter(
        race_id__in=race_ids
    ).values('race_id', 'race_date')
    return {rd['race_id']: rd['race_date'] for rd in race_dates}

def build_output_df(race_details, race_date_map, recent_race_count=10):
    records = []

    # 全体を DataFrame 用のリストとして構築
    for rd in race_details:
        race_id = rd['race_id']
        horse_id = rd['horse_id']
        horse_number = rd['horse_number']
        jockey_id = rd.get('jockey_id')
        race_date = race_date_map.get(race_id)

        if not race_date:
            continue

        time_index_avg = get_time_index_average(horse_id, race_date)
        jockey_place_rate = get_jockey_win_place_show_rate(jockey_id, race_date, recent_race_count)

        records.append({
            'race_id': race_id,
            'horse_number': horse_number,
            'jockey_id': jockey_id,
            'time_index_average': time_index_avg,
            'jockey_place_rate': jockey_place_rate,
        })

    # DataFrame化
    df = pd.DataFrame(records)

    # 補完処理：同じ race_id ごとに複勝率の中央値で補完
    df['jockey_place_rate'] = df.groupby('race_id')['jockey_place_rate'] \
                                .transform(lambda x: x.fillna(x.median()))

    # fallback（それでも残る null を 0.0 に）
    df['jockey_place_rate'] = df['jockey_place_rate'].fillna(0.0)

    return df

def get_time_index_average(horse_id, race_date):
    past_details = RaceDetail.objects.filter(
        horse_id=horse_id,
        race__race_date__lt=race_date
    ).select_related('race') \
     .order_by('-race__race_date')[:3]

    time_indexes = [rd.time_index for rd in past_details if rd.time_index is not None]

    if time_indexes:
        return sum(time_indexes) / len(time_indexes)
    return None

def get_jockey_win_place_show_rate(jockey_id, race_date, recent_race_count):
    """
    騎手の過去直近 recent_race_count 件における複勝率（3着以内率）を計算する
    """
    past_details = RaceDetail.objects.filter(
        jockey_id=jockey_id,
        race__race_date__lt=race_date
    ).select_related('race') \
     .order_by('-race__race_date')[:recent_race_count]

    total = past_details.count()
    if total == 0:
        return None

    top_3 = sum(1 for rd in past_details if rd.finish_rank and rd.finish_rank <= 3)
    return round(top_3 / total, 3)  # 小数第3位で丸める

def create_csv_response_from_df(df):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="input.csv"'
    df = df[['race_id', 'horse_number', 'time_index_average', 'jockey_place_rate']]
    df.to_csv(path_or_buf=response, index=False)
    return response
