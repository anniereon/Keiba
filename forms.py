from django import forms
import datetime

class DateRangeForm(forms.Form):
    start_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}),initial=datetime.date(2024, 1, 1))
    end_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}),initial=datetime.date(2024, 1, 1))