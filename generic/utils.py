from channels.db import database_sync_to_async

from .exceptions import ClientError
from .models import Data, RealtimeSettings


# This decorator turns this function from a synchronous function into an async one
# we can call from our async consumers, that handles Django DBs correctly.
# For more, see http://channels.readthedocs.io/en/latest/topics/databases.html
@database_sync_to_async
def get_data_or_error(user):
    """
    Tries to fetch data saved for the user, checking permissions along the way.
    """
    # Check if the user is logged in
    if not user.is_authenticated:
        raise ClientError("USER_HAS_TO_LOGIN")
    # Find the room they requested (by ID)
    try:
        data = Data.objects.get(user=user)
    except Data.DoesNotExist:
        raise ClientError("EMPTY_DATA")
    return data


@database_sync_to_async
def get_realtime_setting_or_error(user):
    """
    Tries to fetch the realtime settings saved for the user, checking permissions along the way.
    """

    default_realtime_settings = {
        "realtime": True
    }

    # Check if the user is logged in
    if not user.is_authenticated:
        raise ClientError("USER_HAS_TO_LOGIN")

    # Find the room they requested (by ID)
    try:
        realtime_settings = RealtimeSettings.objects.get(user=user)
    except Data.DoesNotExist:
        realtime_settings = default_realtime_settings
    except Exception:
        raise ClientError("Unknown Error")
    return {
        "active": realtime_settings.realtime
    }
