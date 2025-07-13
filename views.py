from django.shortcuts import render

from keiba.forms import DateRangeForm
from keiba.services.keiba import race_repository, feature_engineering
from keiba.services.csv.export import create_csv_response_from_df

def index(request):
    form = DateRangeForm(request.GET or None)
    if form.is_valid():
        sd = form.cleaned_data['start_date']
        ed = form.cleaned_data['end_date']
        recent_n = 3

        race_ids = race_repository.get_race_ids_between(sd, ed)
        race_details = race_repository.get_race_details(race_ids)
        race_date_map = race_repository.get_race_date_map(race_details)

        df = feature_engineering.build_features(race_details, race_date_map, recent_n)

        return create_csv_response_from_df(df)

    return render(request, 'keiba/index.html', {'form': form})
