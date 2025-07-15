from django.db import models

class Course(models.Model):
    course_id = models.CharField(primary_key=True, max_length=4)
    racecourse = models.CharField(max_length=20)
    surface_type = models.CharField(max_length=10)
    distance = models.IntegerField()
    direction = models.CharField(max_length=10)

    class Meta:
        db_table = 'course'
        managed = False

class Horse(models.Model):
    horse_id = models.CharField(primary_key=True, max_length=10)
    horse_name = models.CharField(max_length=50)

    class Meta:
        db_table = 'horse'
        managed = False

class Jockey(models.Model):
    jockey_id = models.CharField(primary_key=True, max_length=5)
    jockey_name = models.CharField(max_length=50)

    class Meta:
        db_table = 'jockey'
        managed = False

class BetType(models.Model):
    bet_type_id = models.CharField(primary_key=True, max_length=3)
    bet_type_name = models.CharField(max_length=10)

    class Meta:
        db_table = 'bet_type'
        managed = False

class Weather(models.Model):
    weather_id = models.CharField(primary_key=True, max_length=1)
    weather_name = models.CharField(max_length=10)

    class Meta:
        db_table = 'weather'
        managed = False

class TrackCondition(models.Model):
    track_condition_id = models.CharField(primary_key=True, max_length=1)
    track_condition_name = models.CharField(max_length=10)

    class Meta:
        db_table = 'track_condition'
        managed = False

class Style(models.Model):
    style_id = models.CharField(primary_key=True, max_length=1)
    style_name = models.CharField(max_length=10)

    class Meta:
        db_table = 'style'
        managed = False

class Race(models.Model):
    race_id = models.CharField(primary_key=True, max_length=9)
    race_date = models.DateField()
    num_horses = models.IntegerField()
    course = models.ForeignKey(Course, on_delete=models.DO_NOTHING, db_column='course_id')
    race_number = models.IntegerField()
    weather = models.ForeignKey(Weather, on_delete=models.DO_NOTHING, db_column='weather_id')
    track_condition = models.ForeignKey(TrackCondition, on_delete=models.DO_NOTHING, db_column='track_condition_id')
    note = models.TextField(null=True)

    class Meta:
        db_table = 'race'
        managed = False

class RaceDetail(models.Model):
    race = models.ForeignKey('Race', db_column='race_id', on_delete=models.DO_NOTHING, primary_key=True)
    horse_number = models.IntegerField()
    # horse_id = models.CharField(max_length=10)
    horse = models.ForeignKey('Horse', db_column='horse_id', on_delete=models.DO_NOTHING)
    jockey = models.ForeignKey('Jockey', db_column='jockey_id', on_delete=models.DO_NOTHING)
    frame_number = models.IntegerField(null=True, blank=True)
    style = models.ForeignKey('Style', db_column='style_id', null=True, blank=True, on_delete=models.SET_NULL)
    odds = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    popularity = models.IntegerField(null=True, blank=True)
    finish_rank = models.IntegerField(null=True, blank=True)
    time_index = models.IntegerField(null=True, blank=True)
    note = models.TextField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'race_detail'
        unique_together = (('race', 'horse_number'),)

class RaceStatistics(models.Model):
    stat_id = models.BigAutoField(primary_key=True)
    start_date = models.DateField()
    end_date = models.DateField()
    course = models.ForeignKey(Course, on_delete=models.DO_NOTHING, db_column='course_id')
    num_horses = models.IntegerField()
    race_number = models.IntegerField()
    weather = models.ForeignKey(Weather, on_delete=models.DO_NOTHING, db_column='weather_id')
    horse_number = models.IntegerField()
    frame_number = models.IntegerField()
    style = models.ForeignKey(Style, on_delete=models.DO_NOTHING, db_column='style_id')
    sample_size = models.IntegerField()
    num_place = models.IntegerField()
    num_win = models.IntegerField()

    class Meta:
        db_table = 'race_statistics'
        managed = False