from django.shortcuts import render
from keiba.forms import DateRangeForm
from .services.keiba_logic import (
    get_race_ids_between,
    get_race_details,
    get_race_date_map,
    build_output_df
)
from .services.csv_service import create_csv_response_from_df

def index(request):
    form = DateRangeForm(request.GET or None)
    if form.is_valid():
        sd = form.cleaned_data['start_date']
        ed = form.cleaned_data['end_date']
        recent_race_count = 10

        race_ids = get_race_ids_between(sd, ed)
        race_details = get_race_details(race_ids)
        race_date_map = get_race_date_map(race_details)

        # DataFrameで処理
        df = build_output_df(race_details, race_date_map, recent_race_count)

        return create_csv_response_from_df(df)

    return render(request, 'keiba/index.html', {'form': form})