import json
from asgiref.sync import async_to_sync
import channels.layers
from django.db import models
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def broadcast(user, content, notification_type="new"):
    # Add condition if user has subscribed in Redis
    channel_layer = channels.layers.get_channel_layer()
    logger.info("sending socket to : " + 'realtime_' + str(user))
    logger.info("Type : " + 'realtime_' + str(notification_type))
    logger.info("Content : " + str(content))
    async_to_sync(channel_layer.group_send)(
        'realtime_' + str(user), {
            "type": notification_type,
            "content": json.dumps(content),
        })


class Data(models.Model):
    """
    Data stored in the ORM or anywhere else
    """

    # Information Field
    information = models.CharField(max_length=255)

    # Linear factor
    a = models.FloatField(default=0)

    # Value
    x = models.FloatField(default=0)

    # User
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )

    def save(self, *args, **kwargs):
        logger.info("Saving new data")
        content = {
            'a': self.a,
            'x': self.x,
            'information': self.information
        }
        if not self.id:
            # Go through a serializer
            notification_type = "data.new"
        else:
            notification_type = "data.update"

        # Send notification to opened channels
        broadcast(self.user.id, content, notification_type)
        # Save the data
        super(Data, self).save(*args, **kwargs)


class RealtimeSettings(models.Model):
    """
    Realtime Settings stored in the ORM
    """

    # Information Field
    realtime = models.BooleanField(default=True)

    # User
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
