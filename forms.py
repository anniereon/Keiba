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
    num_horses = forms.IntegerField(  # 新規追加
        label="頭数",
        required=False,
        min_value=1,
        help_text="併せてフィルタしたい頭数（省略可）"
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
