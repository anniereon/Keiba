# services/csv_service.py

import pandas as pd
from django.http import HttpResponse


def create_csv_response_from_df(df, filename="input.csv"):
    """
    Pandas DataFrame から CSV HTTP レスポンスを生成
    """
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    # 必要に応じて列順や内容を整える
    output_df = df[['race_id', 'horse_number', 'time_index_average', 'jockey_place_rate']]
    output_df.to_csv(path_or_buf=response, index=False)

    return response
