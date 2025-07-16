# services/csv/export.py

import pandas as pd
from django.http import HttpResponse

def create_csv_response_from_df(df, filename="input.csv"):
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    # UTF-8 BOMを書き込む（Excelでの文字化け防止）
    response.write('\ufeff')

    base_cols = ['race_id', 'horse_number']
    other_cols = [col for col in df.columns if col not in base_cols]
    df = df[base_cols + other_cols]

    df.to_csv(response, index=False, encoding='utf-8')
    return response

