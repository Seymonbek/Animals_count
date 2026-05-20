from django.urls import path
from .views import (
    AnimalStatsView,
    AnimalsCountCreateView,
    AnimalsCountListView,
    animal_dashboard,
)

urlpatterns = [
    path('', AnimalsCountCreateView.as_view(), name='animal-log-create'),
    path('dashboard/', animal_dashboard, name='animal-dashboard'),
    path('logs/', AnimalsCountListView.as_view(), name='animal-logs'),
    path('stats/', AnimalStatsView.as_view(), name='animal-stats'),
]
