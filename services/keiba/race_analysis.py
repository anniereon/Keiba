# services/keiba/race_analysis.py

from ...models import RaceDetail

def get_time_index_average(horse_id, race_date):
    past = RaceDetail.objects.filter(
        horse_id=horse_id,
        race__race_date__lt=race_date
    ).select_related('race').order_by('-race__race_date')[:3]

    values = [r.time_index for r in past if r.time_index is not None]
    return round(sum(values) / len(values), 3) if values else None

def get_jockey_place_rate(jockey_id, race_date, recent_n=10):
    if not jockey_id:
        return None

    past = RaceDetail.objects.filter(
        jockey_id=jockey_id,
        race__race_date__lt=race_date
    ).select_related('race').order_by('-race__race_date')[:recent_n]

    total = past.count()
    if total == 0:
        return None

    top3 = sum(1 for r in past if r.finish_rank and r.finish_rank <= 3)
    return round(top3 / total, 3)
