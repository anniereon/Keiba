# services/keiba/race_repository.py

from keiba.models import Race, RaceDetail

def get_race_ids_between(start_date, end_date):
    return Race.objects.filter(
        race_date__range=(start_date, end_date)
    ).values_list('race_id', flat=True)

def get_race_details(race_ids):
    # 必要なフィールドを拡張（weather_id, style_id など）
    return RaceDetail.objects.filter(
        race_id__in=race_ids
    ).select_related('race').values(
        'race_id',
        'horse_id',
        'horse_number',
        'jockey_id',
        'frame_number',
        'style_id',
        'race__course_id',
        'race__num_horses',
        'race__race_number',
        'race__weather_id',
    )

def get_race_date_map(race_details):
    race_ids = [rd['race_id'] for rd in race_details]
    race_dates = Race.objects.filter(race_id__in=race_ids).values('race_id', 'race_date')
    return {r['race_id']: r['race_date'] for r in race_dates}
