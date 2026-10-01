from django.contrib import admin
from .models import Recipe, Bookmark
admin.site.register([Recipe, Bookmark])
