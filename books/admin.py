from django.contrib import admin
from .models import Book, Author, Genre


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    prepopulated_fields = {'name': ('name',)}


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'date_of_birth', 'date_of_death')
    search_fields = ('first_name', 'last_name')
    list_filter = ('date_of_birth',)


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'genre', 'publication_year', 'available_copies', 'total_copies', 'is_available')
    list_filter = ('genre', 'publication_year', 'created_at')
    search_fields = ('title', 'author__first_name', 'author__last_name', 'isbn')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'author', 'genre', 'isbn')
        }),
        ('Publication Details', {
            'fields': ('publication_year', 'publisher', 'description', 'cover_image')
        }),
        ('Inventory Management', {
            'fields': ('total_copies', 'available_copies')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def is_available(self, obj):
        return obj.is_available

    is_available.boolean = True
    is_available.short_description = 'Available'