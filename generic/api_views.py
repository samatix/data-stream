import logging
from time import time
from rest_framework import viewsets
from rest_framework import permissions
from . import serializers
from . import models

logger = logging.getLogger(__name__)


class DataViewSet(viewsets.ModelViewSet):
    """
        Data "view" set is used as a model view set for the rest API to show the list of all the data stored.
        The API returns the data list depending on the permission of the user:
    """
    permission_classes = (permissions.DjangoModelPermissions,)
    serializer_class = serializers.DataSerializer

    def get_queryset(self):
        start = time()
        if self.request.user.is_authenticated:
            data = models.Data.objects.filter(
                user=self.request.user
            )
        else:
            data = models.Data.objects.none()
        logger.debug("Elapsed time to get the query set data {}.".format(time() - start))
        return data.order_by("-id")
