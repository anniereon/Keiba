from django.shortcuts import render
from keiba.forms import DateRangeForm, StatisticsFilterForm
from keiba.services.keiba import race_repository, feature_engineering, statistics
from keiba.services.csv.export import create_csv_response_from_df

def index(request):
    action = request.GET.get("action")

    feature_form = DateRangeForm(request.GET if action == "export" else None)
    stats_form = StatisticsFilterForm(request.GET if action == "aggregate" else None)
    result = None

    if action == "export" and feature_form.is_valid():
        sd = feature_form.cleaned_data['start_date']
        ed = feature_form.cleaned_data['end_date']
        recent_n = 3

        race_ids = race_repository.get_race_ids_between(sd, ed)
        race_details = race_repository.get_race_details(race_ids)
        race_date_map = race_repository.get_race_date_map(race_details)

        df = feature_engineering.build_features(race_details, race_date_map, recent_n)

        return create_csv_response_from_df(df)

    elif action == "aggregate" and stats_form.is_valid():
        filters = stats_form.cleaned_data

        filters['weather'] = filters.get('weather') or None
        filters['style_prediction'] = filters.get('style_prediction') or None

        result = statistics.aggregate_statistics(filters)

    return render(request, 'keiba/index.html', {
        'feature_form': feature_form,
        'stats_form': stats_form,
        'result': result
    })

