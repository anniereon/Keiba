from keiba.models import Course, Race, RaceDetail, RaceStatistics

def aggregate_statistics(filters):
    # Course 絞り込み
    course_qs = Course.objects.all()
    if filters.get("racecourse"):
        course_qs = course_qs.filter(racecourse=filters["racecourse"])
    if filters.get("surface_type"):
        course_qs = course_qs.filter(surface_type=filters["surface_type"])
    if filters.get("distance"):
        course_qs = course_qs.filter(distance=filters["distance"])
    if filters.get("direction"):
        course_qs = course_qs.filter(direction=filters["direction"])

    course_ids = course_qs.values_list("course_id", flat=True)
    course = course_qs.get() if course_qs.count() == 1 else None  # courseが1つに特定できたときのみ設定

    # Race 絞り込み
    race_qs = Race.objects.filter(
        race_date__range=(filters["start_date"], filters["end_date"]),
    )
    if course_ids:
        race_qs = race_qs.filter(course_id__in=course_ids)
    if filters.get("num_horses"):
        race_qs = race_qs.filter(num_horses=filters["num_horses"])
    if filters.get("race_number"):
        race_qs = race_qs.filter(race_number=filters["race_number"])
    if filters.get("weather"):
        race_qs = race_qs.filter(weather=filters["weather"])

    race_ids = race_qs.values_list("race_id", flat=True)

    # RaceDetail 絞り込み
    detail_qs = RaceDetail.objects.filter(race_id__in=race_ids)
    if filters.get("horse_number"):
        detail_qs = detail_qs.filter(horse_number=filters["horse_number"])
    if filters.get("frame_number"):
        detail_qs = detail_qs.filter(frame_number=filters["frame_number"])
    if filters.get("style_prediction"):
        detail_qs = detail_qs.filter(style_prediction=filters["style_prediction"])

    sample_size = detail_qs.count()
    num_place = detail_qs.filter(finish_rank__lte=3).count()
    num_win = detail_qs.filter(finish_rank=1).count()

    if sample_size == 0:
        return None  # 集計対象が存在しない

    # レコードの存在確認（course=None の場合も含む）
    lookup = {
        'start_date': filters['start_date'],
        'end_date': filters['end_date'],
        'course': course,
        'num_horses': filters.get('num_horses'),
        'race_number': filters.get('race_number'),
        'weather': filters.get('weather'),
        'horse_number': filters.get('horse_number'),
        'frame_number': filters.get('frame_number'),
        'style_prediction': filters.get('style_prediction'),
    }

    existing_qs = RaceStatistics.objects.filter(**lookup)

    if existing_qs.exists():
        existing_qs.update(
            sample_size=sample_size,
            num_place=num_place,
            num_win=num_win,
        )
        return existing_qs.first(), False  # update
    else:
        stats_obj = RaceStatistics.objects.create(
            **lookup,
            sample_size=sample_size,
            num_place=num_place,
            num_win=num_win,
        )
        return stats_obj, True  # insert
