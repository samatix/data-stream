from django.contrib import admin
from .models import Data, RealtimeSettings


admin.site.register(
    Data,
    list_display=["id", "information", "a", "x"],
    list_display_links=["id", "information"],
)


