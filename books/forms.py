from django import forms
from .models import Book, Author, Genre

class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = ['title', 'author', 'isbn', 'genre', 'publication_year',
                 'publisher', 'description', 'total_copies', 'available_copies', 'cover_image']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'publication_year': forms.NumberInput(attrs={'min': 1000, 'max': 2100}),
        }

class BookSearchForm(forms.Form):
    query = forms.CharField(required=False, label='Search')
    genre = forms.ModelChoiceField(queryset=Genre.objects.all(), required=False, empty_label='All Genres')
    publication_year = forms.IntegerField(required=False, min_value=1000, max_value=2100)
    author = forms.ModelChoiceField(queryset=Author.objects.all(), required=False, empty_label='All Authors')