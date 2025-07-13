from django import forms
import datetime

class DateRangeForm(forms.Form):
    start_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), initial=datetime.date(2024, 1, 1))
    end_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), initial=datetime.date(2024, 1, 1))

class StatisticsFilterForm(forms.Form):
    start_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), initial=datetime.date(2024, 1, 1))
    end_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), initial=datetime.date(2024, 1, 1))
    racecourse = forms.CharField(required=False)
    surface_type = forms.CharField(required=False)
    distance = forms.IntegerField(required=False)
    direction = forms.CharField(required=False)
    num_horses = forms.IntegerField(required=False)
    race_number = forms.IntegerField(required=False)
    weather = forms.CharField(required=False)
    horse_number = forms.IntegerField(required=False)
    frame_number = forms.IntegerField(required=False)
    style_prediction = forms.CharField(required=False)

