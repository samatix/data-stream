from rest_framework import serializers
from . import models


class DataSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Data
        fields = ('id', 'user', 'information', 'a', 'x')
