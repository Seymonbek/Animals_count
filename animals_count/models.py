from django.db import models

# Create your models here.
class AnimalsCount(models.Model):
    """Hayvonlarni aniqlash va saqlash uchun model"""

    ANIMAL_CHOICES = [
        ('cow', 'Cow'),
        ('sheep', 'Sheep'),
        ('goat', 'Goat'),
    ]

    animal_type = models.CharField(max_length=15, choices=ANIMAL_CHOICES)
    track_id = models.IntegerField(help_text="trekerdan olingan takrorlanmas (unikal) identifikator")
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['animal_type', 'track_id']
        ordering = ['-timestamp']
        verbose_name = "Animal Count"
        verbose_name_plural = "Animals Count"

    def __str__(self):
        return f"{self.animal_type} - Track ID: {self.track_id}"