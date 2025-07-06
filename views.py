from django.shortcuts import render
from django.http import HttpResponse
from .forms import DateRangeForm
from .models import RaceDetail, Race
import csv

def index(request):
    form = DateRangeForm(request.GET or None)
    if form.is_valid():
        sd = form.cleaned_data['start_date']
        ed = form.cleaned_data['end_date']
        # 期間内のrace_idを取得
        race_ids = Race.objects.filter(race_date__range=(sd, ed)).values_list('race_id', flat=True)

        # 取得結果：期間内のrace_detailを取得（race_id, horse_id, horse_number）
        race_details = RaceDetail.objects.filter(race_id__in=race_ids).values('race_id', 'horse_id', 'horse_number')

        # race_id → race_dateのマッピングを取得
        race_dates = Race.objects.filter(race_id__in=[rd['race_id'] for rd in race_details])\
            .values('race_id', 'race_date')
        race_date_map = {rd['race_id']: rd['race_date'] for rd in race_dates}

        output_rows = []

        for rd in race_details:
            race_id = rd['race_id']
            horse_id = rd['horse_id']
            horse_number = rd['horse_number']
            race_date = race_date_map[race_id]

            if not race_date:
                print(f"[WARNING] race_id={race_id} に race_date が見つかりません")
                continue

            time_index_avg = get_time_index_average(horse_id, race_date)

            output_rows.append({
                'race_id': race_id,
                'horse_number': horse_number,
                'time_index_average': time_index_avg
            })

        print(f"race_details 件数: {len(race_details)}")

        # CSVレスポンスを返す
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="input.csv"'

        writer = csv.writer(response)
        writer.writerow(['race_id', 'horse_number', 'time_index_average'])
        for row in output_rows:
            writer.writerow([row['race_id'], row['horse_number'], row['time_index_average']])

        return response

    return render(request, 'keiba/index.html', {'form': form})

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


