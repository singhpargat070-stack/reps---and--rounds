from django.shortcuts import render
from django.contrib.auth import login as auth_login
from django.contrib.auth.forms import UserCreationForm

# Create your views here.
from datetime import timedelta
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import Day, ExerciseType, LoggedExercise, RoutineExercise, WorkoutLog

DAY_ORDER = Day.values  # ["monday", "tuesday", ..., "sunday"], in declared order


def _today_day_key():
    return DAY_ORDER[timezone.localdate().weekday()]


def _get_or_create_log(user, for_date):
    log, _ = WorkoutLog.objects.get_or_create(user=user, date=for_date)
    return log


def _int_or_none(raw):
    raw = (raw or "").strip()
    return int(raw) if raw else None


def _decimal_or_none(raw):
    raw = (raw or "").strip()
    if not raw:
        return None
    try:
        return Decimal(raw)
    except InvalidOperation:
        return None


@login_required
def today(request):
    today_date = timezone.localdate()
    day_key = _today_day_key()
    routine_today = RoutineExercise.objects.filter(user=request.user, day_of_week=day_key)

    log = _get_or_create_log(request.user, today_date)

    # backfill: any routine exercise for today without a log entry yet gets one
    existing_ids = set(
        log.loggedexercise_set.filter(routine_exercise__isnull=False)
        .values_list("routine_exercise_id", flat=True)
    )
    for ex in routine_today:
        if ex.id not in existing_ids:
            LoggedExercise.objects.create(
                workout_log=log,
                routine_exercise=ex,
                name=ex.name,
                exercise_type=ex.type,
            )

    entries = log.loggedexercise_set.select_related("routine_exercise").order_by("id")

    context = {
        "today_date": today_date,
        "day_label": day_key.capitalize(),
        "entries": entries,
        "completed_count": entries.filter(completed=True).count(),
        "total_count": entries.count(),
    }
    return render(request, "tracker/today.html", context)


@login_required
@require_POST
def toggle_entry(request, entry_id):
    entry = get_object_or_404(LoggedExercise, id=entry_id, workout_log__user=request.user)
    entry.completed = not entry.completed
    if entry.completed and entry.routine_exercise and entry.actual_sets is None and entry.actual_duration_minutes is None:
        ex = entry.routine_exercise
        entry.actual_sets = ex.sets
        entry.actual_reps = ex.reps
        entry.actual_weight = ex.weight
        entry.actual_weight_unit = ex.weight_unit
        entry.actual_duration_minutes = ex.duration_minutes
        entry.actual_distance = ex.distance
        entry.actual_distance_unit = ex.distance_unit
    entry.save()
    return redirect("tracker:today")


@login_required
@require_POST
def update_entry(request, entry_id):
    entry = get_object_or_404(LoggedExercise, id=entry_id, workout_log__user=request.user)
    entry.actual_sets = _int_or_none(request.POST.get("actual_sets"))
    entry.actual_reps = _int_or_none(request.POST.get("actual_reps"))
    entry.actual_weight = _decimal_or_none(request.POST.get("actual_weight"))
    entry.actual_weight_unit = request.POST.get("actual_weight_unit", entry.actual_weight_unit)
    entry.actual_duration_minutes = _int_or_none(request.POST.get("actual_duration_minutes"))
    entry.actual_distance = _decimal_or_none(request.POST.get("actual_distance"))
    entry.actual_distance_unit = request.POST.get("actual_distance_unit", entry.actual_distance_unit)
    entry.notes = request.POST.get("notes", "").strip()
    entry.completed = True
    entry.save()
    messages.success(request, f"Logged {entry.name}.")
    return redirect("tracker:today")


@login_required
@require_POST
def add_adhoc(request):
    name = request.POST.get("name", "").strip()
    exercise_type = request.POST.get("exercise_type", ExerciseType.STRENGTH)
    if not name:
        messages.error(request, "Give it a name.")
        return redirect("tracker:today")

    log = _get_or_create_log(request.user, timezone.localdate())
    LoggedExercise.objects.create(
        workout_log=log, routine_exercise=None, name=name, exercise_type=exercise_type, completed=True,
    )
    messages.success(request, f"Added {name} to today.")
    return redirect("tracker:today")


@login_required
@require_POST
def delete_entry(request, entry_id):
    entry = get_object_or_404(
        LoggedExercise, id=entry_id, workout_log__user=request.user, routine_exercise__isnull=True
    )
    entry.delete()
    return redirect("tracker:today")


@login_required
def routine(request, day=None):
    day_key = day if day in DAY_ORDER else _today_day_key()
    exercises = RoutineExercise.objects.filter(user=request.user, day_of_week=day_key)

    editing = None
    edit_id = request.GET.get("edit")
    if edit_id:
        editing = get_object_or_404(RoutineExercise, id=edit_id, user=request.user, day_of_week=day_key)

    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        if not name:
            messages.error(request, "Give the exercise a name.")
        else:
            ex = editing or RoutineExercise(user=request.user, day_of_week=day_key)
            ex.name = name
            ex.type = request.POST.get("type", ExerciseType.STRENGTH)
            ex.sets = _int_or_none(request.POST.get("sets"))
            ex.reps = _int_or_none(request.POST.get("reps"))
            ex.weight = _decimal_or_none(request.POST.get("weight"))
            ex.weight_unit = request.POST.get("weight_unit", ex.weight_unit)
            ex.duration_minutes = _int_or_none(request.POST.get("duration_minutes"))
            ex.distance = _decimal_or_none(request.POST.get("distance"))
            ex.distance_unit = request.POST.get("distance_unit", ex.distance_unit)
            ex.save()
            messages.success(request, f"Saved {ex.name}.")
            return redirect("tracker:routine_day", day=day_key)

    context = {
        "days": Day.choices,
        "day_key": day_key,
        "exercises": exercises,
        "editing": editing,
        "exercise_types": ExerciseType.choices,
    }
    return render(request, "tracker/routine.html", context)


@login_required
@require_POST
def delete_routine_exercise(request, pk):
    ex = get_object_or_404(RoutineExercise, id=pk, user=request.user)
    day_key = ex.day_of_week
    ex.delete()
    messages.success(request, "Removed from your routine.")
    return redirect("tracker:routine_day", day=day_key)


@login_required
def history(request):
    logs = WorkoutLog.objects.filter(user=request.user).prefetch_related("loggedexercise_set")
    by_date = {log.date: log for log in logs}

    def done_on(d):
        log = by_date.get(d)
        return bool(log and any(e.completed for e in log.loggedexercise_set.all()))

    cursor = timezone.localdate()
    if not done_on(cursor):
        cursor -= timedelta(days=1)
    streak = 0
    while done_on(cursor):
        streak += 1
        cursor -= timedelta(days=1)

    grid_days = []
    d = timezone.localdate() - timedelta(days=27)
    while d <= timezone.localdate():
        grid_days.append({"date": d, "done": done_on(d)})
        d += timedelta(days=1)

    recent = []
    for log in sorted(by_date.values(), key=lambda l: l.date, reverse=True)[:10]:
        names = [e.name for e in log.loggedexercise_set.all() if e.completed]
        if names:
            recent.append({"date": log.date, "names": names})

    context = {
        "streak": streak,
        "total_workouts": sum(1 for d in by_date if done_on(d)),
        "grid_days": grid_days,
        "recent": recent,
    }
    return render(request, "tracker/history.html", context)



def signup(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            return redirect("tracker:routine")
    else:
        form = UserCreationForm()
    return render(request, "registration/signup.html", {"form": form})