# services/keiba/race_analysis.py

from ...models import RaceDetail

def get_time_index_average(horse_id, race_date, recent_n=3):
    past = RaceDetail.objects.filter(
        horse_id=horse_id,
        race__race_date__lt=race_date,
        time_index__isnull=False
    ).select_related('race').order_by('-race__race_date')[:recent_n]

    if len(past) < recent_n:
        return None  # 十分なデータがない場合は None を返す

    values = [r.time_index for r in past]

    return round(sum(values) / recent_n, 3)

from django.db.models import Q

def get_jockey_place_rate(jockey_id, race_date, current_race_number, recent_n):
    if not jockey_id:
        return None

    # finish_rank が NULL でないデータを対象に、recent_n 件取得
    past = RaceDetail.objects.filter(
        jockey_id=jockey_id,
        finish_rank__isnull=False
    ).filter(
        Q(race__race_date__lt=race_date) |
        Q(race__race_date=race_date, race__race_number__lt=current_race_number)
    ).select_related('race').order_by(
        '-race__race_date',
        '-race__race_number',
    )[:recent_n]

    if len(past) < recent_n:
        return None  # データ不足

    # 3位以内の回数を数える
    top3 = sum(1 for r in past if r.finish_rank <= 3)
    return round(top3 / recent_n, 3)