# services/keiba/race_repository.py

from keiba.models import Race, RaceDetail
from django.forms.models import model_to_dict

def get_race_ids_between(start_date, end_date, num_horses=None):
    qs = Race.objects.filter(race_date__range=(start_date, end_date))
    if num_horses is not None:
        qs = qs.filter(num_horses=num_horses)
    return qs.values_list('race_id', flat=True)

def get_race_details(race_ids, num_horses=None):
    query = RaceDetail.objects.filter(
        race_id__in=race_ids
    ).select_related('race')

    if num_horses:
        query = query.filter(race__num_horses=num_horses)

    result = []

    for rd in query:
        rd_dict = model_to_dict(rd)

        # 明示的に race_id を追加（特に pk の場合、model_to_dict で除かれることがある）
        rd_dict['race_id'] = rd.race_id
        rd_dict['horse_id'] = rd.horse_id  # 同様に他のカラムも必要に応じて追加

        race_dict = model_to_dict(rd.race)
        race_dict.pop('race_id', None)  # 重複を防ぐ
        race_dict_prefixed = {f"race_{k}": v for k, v in race_dict.items()}

        rd_dict.update(race_dict_prefixed)
        result.append(rd_dict)

    return result


def get_race_date_map(race_details):
    race_ids = [rd['race_id'] for rd in race_details]
    race_dates = Race.objects.filter(race_id__in=race_ids).values('race_id', 'race_date')
    return {r['race_id']: r['race_date'] for r in race_dates}
