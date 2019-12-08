from django.conf import settings
import logging

from channels.generic.websocket import AsyncJsonWebsocketConsumer

from .exceptions import ClientError

logger = logging.getLogger(__name__)

class DataConsumer(AsyncJsonWebsocketConsumer):
    """
    This data consumer handles websocket connections for the users subscribing to their data.

    It uses AsyncJsonWebsocketConsumer, which means all the handling functions
    must be async functions, and any sync work (like ORM access) has to be
    behind database_sync_to_async or sync_to_async. For more, read
    http://channels.readthedocs.io/en/latest/topics/consumers.html
    """

    # WebSocket event handlers

    async def connect(self):
        """
        Called when the websocket is handshaking as part of initial connection.
        """
        # Are they logged in?
        if self.scope["user"].is_anonymous:
            # Reject the connection
            await self.close()
            logger.debug("Connexion Rejected + " + str(self.scope))
        else:
            # Accept the connection
            await self.accept()
            logger.debug("Connexion Accepted + " + str(self.scope))

    async def receive_json(self, content):
        """
        Called when we get a request to activate or not the realtime.
        Channels will JSON-decode the payload for us and pass it as the first argument.
        """

        # Messages will have a "command" key we can switch on
        command = content.get("command", None)
        logger.debug("Command Received + " + str(content))
        try:
            if command == "subscribe":
                # Make them join the room
                await self.subscribe_to_realtime()

            elif command == "unsubscribe":
                # Leave the room
                await self.unsubscribe_to_realtime()
        except ClientError as e:
            # Catch any errors and send it back
            await self.send_json({"error": e.code})

    async def disconnect(self, code):
        """
        Called when the WebSocket closes for any reason.
        """
        # Deactivate the Realtime
        try:
            await self.unsubscribe_to_realtime()
        except ClientError:
            pass

    # Command helper methods called by receive_json
    async def subscribe_to_realtime(self):
        """
        Called by receive_json when someone sent a join command.
        """
        logger.debug("Group Added on channel " + self.channel_name + " and group realtime_" +
                     str(self.scope["user"].id))
        # Send a realtime activation message
        await self.channel_layer.group_add(
            "realtime_" + str(self.scope["user"].id),
            self.channel_name
        )

    async def unsubscribe_to_realtime(self):
        """
        Called by receive_json when someone sent a leave command.
        """
        logger.debug("Group Discarded on channel " + self.channel_name + " and group realtime_" +
                     str(self.scope["user"].id))
        await self.channel_layer.group_discard(
            "realtime_" + str(self.scope["user"].id),
            self.channel_name
        )

    async def data_update(self, content):
        """
        Called when someone has messaged our chat.
        """
        logger.debug("Data update command received : "+ str(content))
        # Send a message down to the client
        await self.send_json(
            {
                "action": "update",
                "content": content,
            },
        )

    async def data_new(self, content):
        """
        Called when someone has messaged our chat.
        """
        logger.debug("Data update command received : " + str(content))
        # Send a message down to the client
        await self.send_json(
            {
                "action": "new",
                "content": content,
            },
        )