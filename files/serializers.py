from rest_framework import serializers
from .models import FileModel


class FileSerializer(serializers.ModelSerializer):
    class Meta:
        model = FileModel
        fields = '__all__'
        read_only_fields = ('user',)
