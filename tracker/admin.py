from django.contrib import admin

# Register your models here.
from . models import RoutineExercise, LoggedExercise, WorkoutLog


@admin.register(RoutineExercise)
class RoutineExercieAdmin(admin.ModelAdmin):
    list_display = ("user", "day_of_week", "name", "type")
    list_filter = ("day_of_week", "type", "user")
    search_fields = ("name",)

class LoggedExerciseInline(admin.TabularInline):
    model = LoggedExercise
    extra = 0

@admin.register(LoggedExercise)
class LoggedExerciesAdmin(admin.ModelAdmin):
    
    list_display = ("workout_log", "name", "exercise_type", "completed")
    list_filter = ("exercise_type", "completed")


@admin.register(WorkoutLog)

class WorkoutLogAdmin(admin.ModelAdmin):
    list_display = ("user", "date")
    list_filter = ("user",)
    inlines = [LoggedExerciseInline]
    