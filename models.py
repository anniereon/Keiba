from django.db import models

class Course(models.Model):
    course_id = models.CharField(primary_key=True, max_length=4)
    racecourse = models.CharField(max_length=20)
    surface_type = models.CharField(max_length=10)
    distance = models.IntegerField()
    direction = models.CharField(max_length=10)

    class Meta:
        managed = False
        db_table = 'course'


class Horse(models.Model):
    horse_id = models.CharField(primary_key=True, max_length=10)
    horse_name = models.CharField(max_length=50)

    class Meta:
        managed = False
        db_table = 'horse'


class Jockey(models.Model):
    jockey_id = models.CharField(primary_key=True, max_length=5)
    jockey_name = models.CharField(max_length=50)

    class Meta:
        managed = False
        db_table = 'jockey'


class BetType(models.Model):
    bet_type_id = models.CharField(primary_key=True, max_length=3)
    bet_type_name = models.CharField(max_length=10)

    class Meta:
        managed = False
        db_table = 'bet_type'


class Race(models.Model):
    race_id = models.CharField(primary_key=True, max_length=9)
    race_date = models.DateField()
    num_horses = models.IntegerField()
    course_id = models.CharField(max_length=4)
    race_number = models.IntegerField()
    weather = models.CharField(max_length=2)
    track_condition = models.CharField(max_length=2)
    note = models.TextField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'race'


class RaceDetail(models.Model):
    race = models.ForeignKey('Race', db_column='race_id', on_delete=models.DO_NOTHING, primary_key=True)
    horse_id = models.CharField(max_length=10)
    jockey_id = models.CharField(max_length=5)
    horse_number = models.IntegerField()
    frame_number = models.IntegerField(null=True, blank=True)
    style_prediction = models.TextField(null=True, blank=True)
    odds = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    popularity = models.IntegerField(null=True, blank=True)
    finish_rank = models.IntegerField(null=True, blank=True)
    time_index = models.IntegerField(null=True, blank=True)
    note = models.TextField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'race_detail'
        unique_together = (('race', 'horse_number'),)

        # models.py

class RaceStatistics(models.Model):
    stat_id = models.BigAutoField(primary_key=True)
    start_date = models.DateField()
    end_date = models.DateField()
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    num_horses = models.IntegerField()
    race_number = models.IntegerField()
    weather = models.CharField(max_length=2, blank=True, null=True)
    horse_number = models.IntegerField()
    frame_number = models.IntegerField()
    style_prediction = models.TextField(blank=True, null=True)
    sample_size = models.IntegerField()
    num_place = models.IntegerField()
    num_win = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'race_statistics'