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
        # race_dateで絞り込み
        race_ids = Race.objects.filter(race_date__range=(sd, ed)).values_list('race_id', flat=True)
        qs = RaceDetail.objects.filter(race_id__in=race_ids).values('race_id', 'horse_number')

        # CSVレスポンス
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="race_detail.csv"'
        writer = csv.writer(response)
        writer.writerow(['race_id', 'horse_number'])
        for row in qs:
            writer.writerow([row['race_id'], row['horse_number']])
        return response

    return render(request, 'keiba/index.html', {'form': form})
