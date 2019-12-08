from rest_framework import routers
from . import api_views

router = routers.DefaultRouter()
router.register(r'data', api_views.DataViewSet, basename='data')
