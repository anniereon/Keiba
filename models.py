from django.db import models

class RaceDetail(models.Model):
    race_id = models.CharField(max_length=9, primary_key=False)
    horse_id = models.CharField(max_length=10)
    jockey_id = models.CharField(max_length=5)
    horse_number = models.IntegerField()
    # 他カラム略

    class Meta:
        db_table = 'race_detail'
        unique_together = (('race_id', 'horse_number'),)

class Race(models.Model):
    race_id = models.CharField(max_length=9, primary_key=True)
    race_date = models.DateField()
    # 他カラム略

    class Meta:
        db_table = 'race'
