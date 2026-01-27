from django.contrib import admin
from .models import AnimalsCount

# Register your models here.


@admin.register(AnimalsCount)
class AnimalsCountAdmin(admin.ModelAdmin):
    """AnimalsCount modeli uchun admin qismi"""

    list_display = ['id', 'animal_type', 'track_id', 'timestamp']
    list_filter = ['animal_type', 'timestamp']
    search_fields = ['animal_type', 'track_id']
    ordering = ['-timestamp']
    readonly_fields = ['timestamp']