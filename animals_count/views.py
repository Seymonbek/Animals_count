from datetime import timedelta

from django.conf import settings
from django.db.models import Count
from django.db.models.functions import TruncDate
from django.shortcuts import render
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import AnimalsCount
from .serializers import AnimalsCountSerializer

# Create your views here.


class AnimalsCountListView(generics.ListAPIView):
    """Saqlangan barcha hayvon yozuvlarini ro'yxat ko'rinishida qaytaradi."""

    serializer_class = AnimalsCountSerializer

    def get_queryset(self):
        limit = getattr(settings, "ANIMAL_LOG_LIST_LIMIT", 100)
        return AnimalsCount.objects.all()[:limit]


def cleanup_animal_logs():
    """Eski yoki ortiqcha yozuvlarni o'chirib, bazani ixcham saqlaydi."""

    retention_days = getattr(settings, "ANIMAL_LOG_RETENTION_DAYS", None)
    max_records = getattr(settings, "ANIMAL_LOG_MAX_RECORDS", None)

    if retention_days and retention_days > 0:
        cutoff = timezone.now() - timedelta(days=retention_days)
        AnimalsCount.objects.filter(timestamp__lt=cutoff).delete()

    if max_records and max_records > 0:
        total_records = AnimalsCount.objects.count()
        if total_records > max_records:
            keep_ids = list(
                AnimalsCount.objects.values_list("id", flat=True)[:max_records]
            )
            AnimalsCount.objects.exclude(id__in=keep_ids).delete()


def animal_dashboard(request):
    """Auto-refresh qilinadigan monitoring sahifasi."""

    context = {
        "refresh_ms": 3000,
        "logs_url": "/logs/",
        "stats_url": "/stats/",
        "create_url": "/",
    }
    return render(request, "animals_count/dashboard.html", context)


class AnimalsCountCreateView(generics.CreateAPIView):
    """
    Hayvonni aniqlash malumotlarini qabul qiladi(hayvon turi, kuzatuv ID-si)
    """
    queryset = AnimalsCount.objects.all()
    serializer_class = AnimalsCountSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        animal_type = serializer.validated_data["animal_type"]
        track_id = serializer.validated_data["track_id"]

        if AnimalsCount.objects.filter(animal_type=animal_type, track_id=track_id).exists():
            return Response(
                {'error': f'{animal_type} turdagi {track_id} raqamli hayvon allaqachon ro\'yxatga olingan.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        self.perform_create(serializer)
        cleanup_animal_logs()
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class AnimalStatsView(APIView):
    """Hayvonlarning kunlik statistikasi va soni"""

    def get(self, request):
        stats = (
            AnimalsCount.objects.annotate(date=TruncDate('timestamp')).values('date', 'animal_type').annotate(count=Count('id')).order_by('-date', 'animal_type')
        )

        return Response(list(stats), status=status.HTTP_200_OK)
