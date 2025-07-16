# services/keiba/race_repository.py

from keiba.models import Race, RaceDetail

def get_race_ids_between(start_date, end_date, num_horses=None):
    qs = Race.objects.filter(race_date__range=(start_date, end_date))
    if num_horses is not None:
        qs = qs.filter(num_horses=num_horses)
    return qs.values_list('race_id', flat=True)

def get_race_details(race_ids, num_horses=None):
    qs = RaceDetail.objects.select_related(
        'race', 'race__weather', 'race__track_condition', 'style'
    ).filter(race_id__in=race_ids)

    if num_horses:
        qs = qs.filter(race__num_horses=num_horses)

    return qs

def get_race_date_map(race_details):
    race_ids = [rd.race_id for rd in race_details]  # ← 修正：辞書でなく属性アクセス
    race_dates = Race.objects.filter(race_id__in=race_ids).values('race_id', 'race_date')
    return {r['race_id']: r['race_date'] for r in race_dates}
