"""Admin-zone of the django app."""
from django.contrib import admin

from .models import User

admin.site.register(User, admin.ModelAdmin)
