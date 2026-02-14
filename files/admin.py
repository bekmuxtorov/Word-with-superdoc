from django.contrib import admin
from .models import FileModel


@admin.register(FileModel)
class FileModelAdmin(admin.ModelAdmin):
    list_display = ('user', 'file', 'created_at', 'updated_at')
    search_fields = ('user__username', 'file')
    list_filter = ('created_at', 'updated_at')
