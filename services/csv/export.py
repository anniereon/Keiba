# services/csv/export.py

import pandas as pd
from django.http import HttpResponse

def create_csv_response_from_df(df, filename="output.csv"):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    df = df[['race_id', 'horse_number', 'time_index_average', 'jockey_place_rate']]
    df.to_csv(response, index=False)
    return response
