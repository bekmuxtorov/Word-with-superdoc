from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.http import FileResponse
from .models import FileModel
from .serializers import FileSerializer
from .authentication import JWTAuthenticationFromQuery


class FileViewSet(viewsets.ModelViewSet):
    queryset = FileModel.objects.all()
    serializer_class = FileSerializer
    permission_classes = [permissions.IsAuthenticated]
    # Butun ViewSet uchun JWT talab qilinadi
    authentication_classes = [JWTAuthenticationFromQuery]
    parser_classes = (MultiPartParser, FormParser)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['get', 'put', 'patch', 'options'],
            permission_classes=[permissions.IsAuthenticated],
            authentication_classes=[JWTAuthenticationFromQuery],
            parser_classes=[MultiPartParser, FormParser])
    def content(self, request, pk=None):
        # CORS preflight (OPTIONS) uchun autentifikatsiya talab qilinmaydi
        if request.method == 'OPTIONS':
            return Response(status=status.HTTP_200_OK)

        # Token tekshiruvi
        if not request.user or not request.user.is_authenticated:
            return Response(
                {'detail': 'Autentifikatsiya talab qilinadi. JWT token yuboring.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        instance = self.get_object()

        if request.method == 'GET':
            if not instance.file:
                return Response(
                    {'detail': 'Fayl topilmadi.'},
                    status=status.HTTP_404_NOT_FOUND
                )
            return FileResponse(instance.file, as_attachment=True, filename=instance.file.name)

        elif request.method in ['PUT', 'PATCH']:
            if 'file' not in request.FILES:
                return Response(
                    {'detail': 'Fayl yuborilmadi.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            file_obj = request.FILES['file']
            # Faylni saqlash va yangilash
            instance.file.save(file_obj.name, file_obj, save=True)
            return Response({
                'status': 'success',
                'message': 'Fayl muvaffaqiyatli yangilandi',
                'file_url': instance.file.url
            })
