from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.http import FileResponse
from .models import FileModel
from .serializers import FileSerializer


class FileViewSet(viewsets.ModelViewSet):
    queryset = FileModel.objects.all()
    serializer_class = FileSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['get', 'put', 'patch'], permission_classes=[permissions.AllowAny], parser_classes=[MultiPartParser, FormParser])
    def content(self, request, pk=None):
        instance = self.get_object()

        if request.method == 'GET':
            if not instance.file:
                return Response(status=status.HTTP_404_NOT_FOUND)
            return FileResponse(instance.file, as_attachment=True, filename=instance.file.name)

        elif request.method in ['PUT', 'PATCH']:
            if 'file' not in request.FILES:
                return Response({'detail': 'File not provided.'}, status=status.HTTP_400_BAD_REQUEST)

            file_obj = request.FILES['file']
            # Save the new file, which automatically updates the model
            instance.file.save(file_obj.name, file_obj, save=True)
            return Response({'status': 'file updated', 'file': instance.file.url})
