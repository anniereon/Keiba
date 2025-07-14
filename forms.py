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
