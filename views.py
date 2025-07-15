from django.shortcuts import render
from keiba.forms import DateRangeForm, StatisticsFilterForm
from keiba.services.keiba import race_repository, feature_engineering, statistics
from keiba.services.csv.export import create_csv_response_from_df

def index(request):
    action = request.POST.get("action")

    feature_form = DateRangeForm(request.POST if action == "export" else None)
    stats_form = StatisticsFilterForm(request.POST if action == "aggregate" else None)
    result = None

    if action == "export" and feature_form.is_valid():
        sd = feature_form.cleaned_data['start_date']
        ed = feature_form.cleaned_data['end_date']

        race_ids = race_repository.get_race_ids_between(sd, ed)
        race_details = race_repository.get_race_details(race_ids)
        race_date_map = race_repository.get_race_date_map(race_details)

        # 特徴量のリストを取得
        feature_spec_list = []
        index = 0
        while True:
            f_type = request.POST.get(f"features[{index}][type]")
            if not f_type:
                break

            feature_spec = {"type": f_type}

            if f_type in ["time_index_average", "jockey_place_rate"]:
                param = request.POST.get(f"features[{index}][param]")
                if param:
                    feature_spec["param"] = int(param)

            elif f_type == "conditional_place_rate":
                conditions = request.POST.getlist(f"features[{index}][conditions][]")
                if conditions:
                    feature_spec["conditions"] = conditions

            feature_spec_list.append(feature_spec)
            index += 1

        df = feature_engineering.build_features(
            race_details=race_details,
            race_date_map=race_date_map,
            feature_spec_list=feature_spec_list
        )

        return create_csv_response_from_df(df)

    elif action == "aggregate" and stats_form.is_valid():
        filters = stats_form.cleaned_data
        result = statistics.aggregate_statistics(filters)

    return render(request, 'keiba/index.html', {
        'feature_form': feature_form,
        'stats_form': stats_form,
        'result': result
    })
