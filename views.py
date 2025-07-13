from django.shortcuts import render

from keiba.forms import DateRangeForm
from keiba.services.keiba_logic import get_race_ids_between, get_race_details, get_race_date_map, build_output_rows, \
    create_csv_response

def index(request):
    form = DateRangeForm(request.GET or None)
    if form.is_valid():
        sd = form.cleaned_data['start_date']
        ed = form.cleaned_data['end_date']

        recent_race_count = 3

        race_ids = get_race_ids_between(sd, ed)
        race_details = get_race_details(race_ids)
        race_date_map = get_race_date_map(race_details)
        output_rows = build_output_rows(race_details, race_date_map, recent_race_count)

        return create_csv_response(output_rows)

    return render(request, 'keiba/index.html', {'form': form})
