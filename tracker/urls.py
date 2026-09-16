from django.urls import path
from . import models,views


app_name = "tracker"

urlpatterns = [
    path("", views.today, name="today"),
    path("entry/<int:entry_id>/toggle/", views.toggle_entry, name="toggle_entry"),
    path("entry/<int:entry_id>/update/", views.update_entry, name="update_entry"),
    path("entry/<int:entry_id>/delete/", views.delete_entry, name="delete_entry"),
    path("adhoc/add/", views.add_adhoc, name="add_adhoc"),
    path("routine/", views.routine, name="routine"),
    path("routine/<str:day>/", views.routine, name="routine_day"),
    path("routine/exercise/<int:pk>/delete/", views.delete_routine_exercise, name="delete_routine_exercise"),
    path("history/", views.history, name="history"),
]
