from django.contrib import admin
from .models import Data


admin.site.register(
    Data,
    list_display=["id", "instrument", "quantity", "initial_price"],
    list_display_links=["id", "instrument"],
)


