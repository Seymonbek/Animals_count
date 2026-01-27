from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Count
from django.db.models.functions import TruncDate
from .models import AnimalsCount
from .serializers import AnimalsCountSerializer

# Create your views here.


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
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class AnimalStatsView(APIView):
    """Hayvonlarning kunlik statistikasi va soni"""

    def get(self, request):
        stats = (
            AnimalsCount.objects.annotate(date=TruncDate('timestamp')).values('date', 'animal_type').annotate(count=Count('id')).order_by('-date', 'animal_type')
        )

        return Response(list(stats), status=status.HTTP_200_OK)