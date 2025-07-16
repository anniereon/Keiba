# services/csv/export.py

import pandas as pd
from django.http import HttpResponse

def create_csv_response_from_df(df, filename="input.csv"):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    # race_id と horse_number は常に出力、それ以外は全列
    base_cols = ['race_id', 'horse_number']
    other_cols = [col for col in df.columns if col not in base_cols]
    df = df[base_cols + other_cols]

    df.to_csv(response, index=False)
    return response
