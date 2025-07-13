from django import forms
import datetime

class DateRangeForm(forms.Form):
    start_date = forms.DateField(
        label="期間開始日",
        widget=forms.DateInput(attrs={'type': 'date'}),
        initial=datetime.date(2024, 1, 1)
    )
    end_date = forms.DateField(
        label="期間終了日",
        widget=forms.DateInput(attrs={'type': 'date'}),
        initial=datetime.date(2024, 1, 1)
    )

class StatisticsFilterForm(forms.Form):
    start_date = forms.DateField(
        label="集計開始日",
        widget=forms.DateInput(attrs={'type': 'date'}),
        initial=datetime.date(2024, 1, 1)
    )
    end_date = forms.DateField(
        label="集計終了日",
        widget=forms.DateInput(attrs={'type': 'date'}),
        initial=datetime.date(2024, 1, 1)
    )
    racecourse = forms.CharField(label="競馬場", required=False)
    surface_type = forms.CharField(label="グラウンド", required=False)
    distance = forms.IntegerField(label="距離", required=False)
    direction = forms.CharField(label="向き", required=False)
    num_horses = forms.IntegerField(label="頭数", required=False)
    race_number = forms.IntegerField(label="レース番号", required=False)
    weather = forms.CharField(label="天気", required=False)
    horse_number = forms.IntegerField(label="馬番", required=False)
    frame_number = forms.IntegerField(label="枠番", required=False)
    style_prediction = forms.CharField(label="脚質予想", required=False)
