from django.shortcuts import render
from keiba.forms import DateRangeForm, StatisticsFilterForm
from keiba.services.keiba import race_repository, feature_engineering, statistics
from keiba.services.csv.export import create_csv_response_from_df

def index(request):
    action = request.POST.get("action")  # ← GET → POST に変更

    feature_form = DateRangeForm(request.POST if action == "export" else None)
    stats_form = StatisticsFilterForm(request.POST if action == "aggregate" else None)
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
        # 空文字を None に変換（weather, style_prediction だけ）
        if filters.get("weather") == "":
            filters["weather"] = None
        if filters.get("style_prediction") == "":
            filters["style_prediction"] = None

        result = statistics.aggregate_statistics(filters)

    return render(request, 'keiba/index.html', {
        'feature_form': feature_form,
        'stats_form': stats_form,
        'result': result
    })
