from keiba.models import Race, RaceDetail, RaceStatistics

def aggregate_statistics(filters):
    start = filters["start_date"]
    end = filters["end_date"]

    details = RaceDetail.objects.filter(
        race__race_date__range=(start, end)
    ).select_related("race")

    stats_map = {}

    for d in details:
        key = (
            d.race.course_id,
            d.race.num_horses,
            # d.race.race_number,   このフィールドを考慮するとrace_statisticsのレコードが多すぎるので除外
            # d.race.weather_id,    このフィールドを考慮するとrace_statisticsのレコードが多すぎるので除外
            d.horse_number,
            d.frame_number,
            d.style_id,
        )

        if key not in stats_map:
            stats_map[key] = {
                "sample_size": 0,
                "num_place": 0,
                "num_win": 0,
            }

        stats_map[key]["sample_size"] += 1
        if d.finish_rank and d.finish_rank <= 3:
            stats_map[key]["num_place"] += 1
        if d.finish_rank == 1:
            stats_map[key]["num_win"] += 1

    for key, values in stats_map.items():
        course_id, num_horses, horse_number, frame_number, style_id = key

        RaceStatistics.objects.update_or_create(
            start_date=start,
            end_date=end,
            course_id=course_id,
            num_horses=num_horses,
            # race_number=race_number,
            # weather_id=weather_id,
            horse_number=horse_number,
            frame_number=frame_number,
            style_id=style_id,
            defaults={
                "sample_size": values["sample_size"],
                "num_place": values["num_place"],
                "num_win": values["num_win"],
            }
        )

    return {
        "sample_size": sum(v["sample_size"] for v in stats_map.values())
    }
