from django.shortcuts import render
from django.http import HttpResponse
from .forms import DateRangeForm
from .services.keiba_logic import (
    get_race_ids_between,
    get_race_details,
    get_race_date_map,
    build_output_rows,
    create_csv_response
)

def index(request):
    form = DateRangeForm(request.GET or None)
    if form.is_valid():
        sd = form.cleaned_data['start_date']
        ed = form.cleaned_data['end_date']

        race_ids = get_race_ids_between(sd, ed)
        race_details = get_race_details(race_ids)
        race_date_map = get_race_date_map(race_details)
        output_rows = build_output_rows(race_details, race_date_map)

        return create_csv_response(output_rows)

    return render(request, 'keiba/index.html', {'form': form})
