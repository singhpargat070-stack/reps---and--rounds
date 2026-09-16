from django.db import models
from django.conf import settings

# Create your models here.
class ExerciseType(models.TextChoices):
    STRENGTH = "strength", "Strength"
    CARDIO = "cardio", "Cardio"
    STRETCHING = "stretching", "Stretching"
    
class Day(models.TextChoices):
    MONDAY = "monday", "Monday"
    TUESDAY = "tuesday", "Tuesday"
    WEDNESDAY = "wednesday", "Wednesday"
    THURSDAY = "thursday", "Thursday"
    FRIDAY = "friday", "Friday"
    SATURDAY = "saturday", "Saturday"
    SUNDAY = "sunday", "Sunday"

class WeightUnit(models.TextChoices):
    KG = "kg", "kg"
    LB = "lb", "lb"


class DistanceUnit(models.TextChoices):
    KM = "km", "km"
    MI = "mi", "mi"

class RoutineExercise(models.Model):
    day_of_week=models.CharField(max_length=10, choices=Day.choices,default=Day.MONDAY)
    name=models.TextField()
    type=models.CharField(max_length=10, choices=ExerciseType.choices, default=ExerciseType.STRENGTH)
    user=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
    def __str__(self):
        return self.name


class WorkoutLog(models.Model):
    user=models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    date=models.DateField()
    class Meta:
        unique_together = ("user", "date")
    def __str__(self):
        return f"{self.user} — {self.date}"       # WorkoutLog


class LoggedExercise(models.Model):
    workout_log=models.ForeignKey(WorkoutLog, on_delete=models.CASCADE)
    routine_exercies=models.ForeignKey(RoutineExercise, null=True, blank=True,  on_delete=models.SET_NULL)
    completed= models.BooleanField(default=False)
    notes=models.CharField(max_length=255)
    def __str__(self):
        return f"{self.workout_log} — {self.routine_exercies}"   # LoggedExercise, once typo below is fixed





class LoggedExercise(models.Model):
    workout_log = models.ForeignKey(WorkoutLog, on_delete=models.CASCADE)
    routine_exercise = models.ForeignKey(
        RoutineExercise, null=True, blank=True, on_delete=models.SET_NULL
    )

    # snapshotted at log time, so editing/deleting the routine exercise
    # later doesn't change what history shows
    name = models.TextField()
    exercise_type = models.CharField(max_length=10, choices=ExerciseType.choices, default=ExerciseType.STRENGTH)

    completed = models.BooleanField(default=False)

    # actuals — mirrors RoutineExcercise's target fields
    actual_sets = models.PositiveIntegerField(null=True, blank=True)
    actual_reps = models.PositiveIntegerField(null=True, blank=True)
    actual_weight = models.DecimalField(max_digits=6, decimal_places=1, null=True, blank=True)
    actual_weight_unit = models.CharField(max_length=2, choices=WeightUnit.choices, default=WeightUnit.KG)
    actual_duration_minutes = models.PositiveIntegerField(null=True, blank=True)
    actual_distance = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    actual_distance_unit = models.CharField(max_length=2, choices=DistanceUnit.choices, default=DistanceUnit.KM)

    notes = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"{self.name} ({'done' if self.completed else 'pending'})"