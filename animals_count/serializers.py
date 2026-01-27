from rest_framework import serializers
from .models import AnimalsCount

class AnimalsCountSerializer(serializers.ModelSerializer):
    """Hayvonlarni qayd etish va ularni o'qish uchun serializer"""

    class Meta:
        model = AnimalsCount
        fields = ['id', 'animal_type', 'track_id', 'timestamp']
        read_only_fields = ['id', 'timestamp']


class AnimalsStatsSerializer(serializers.ModelSerializer):
    """Hayvonlarning kunlik statistikasini aniqlash uchun serializer"""

    date = serializers.DateField()
    animal_type = serializers.CharField()
    count = serializers.IntegerField()