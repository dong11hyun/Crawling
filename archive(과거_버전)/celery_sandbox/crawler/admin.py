from django.contrib import admin
from .models import Book

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'price', 'rating', 'stock', 'crawled_at')
    search_fields = ('title',)
    list_filter = ('crawled_at', 'rating')