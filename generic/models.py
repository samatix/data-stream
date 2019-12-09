import json
from asgiref.sync import async_to_sync
from time import time
import channels.layers
from django.db import models
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def broadcast(user, content):
    # Add condition if user has subscribed in Redis
    channel_layer = channels.layers.get_channel_layer()
    logger.info("sending socket to : " + 'realtime_' + str(user))
    logger.info("Content : " + str(content))
    async_to_sync(channel_layer.group_send)(
        'realtime_' + str(user), {
            "type": "data.send",
            "content": json.dumps(content),
        })


class Data(models.Model):
    """
    Data stored in the ORM
    """

    # Instrument Field
    instrument = models.CharField(max_length=255)

    # Quantity
    quantity = models.FloatField(default=0)

    # Initial Order Price
    initial_price = models.FloatField(default=0)

    # User
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )

    def save(self, *args, **kwargs):
        logger.info("Saving new data")
        if not self.id:
            # Go through a serializer
            notification_type = "data.new"
        else:
            notification_type = "data.update"

        # Save the data
        super(Data, self).save(*args, **kwargs)

        # Send the opened channels
        content = {
            'id': self.id,
            'quantity': self.quantity,
            'initial_price': self.initial_price,
            'instrument': self.instrument,
            'type': notification_type,
            'time': time()
        }

        # Send notification to opened channels
        broadcast(self.user.id, content)
