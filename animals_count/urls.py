from django.urls import path
from .views import AnimalsCountCreateView, AnimalStatsView

urlpatterns = [
    path('', AnimalsCountCreateView.as_view(), name='animal-log-create'),
    path('stats/', AnimalStatsView.as_view(), name='animal-stats'),
]
