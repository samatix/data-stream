import pytest
from django.test import override_settings
from django.contrib.auth import get_user_model
from django.test import Client
from channels.db import database_sync_to_async
from channels.layers import get_channel_layer
from channels.testing import WebsocketCommunicator

from webapp.routing import application
from generic.models import Data

TEST_CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer',
    },
}


@database_sync_to_async
def create_user(username='admin', password='admin'):
    # Create user.
    user = get_user_model().objects.create_user(
        username=username,
        password=password
    )
    user.save()
    return user


@database_sync_to_async
def create_order(**kwargs):
    return Data.objects.create(**kwargs)


@database_sync_to_async
def update_order(order, **kwargs):
    for i in kwargs:
        setattr(order, i, kwargs[i])
    order.save()


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
class TestWebsockets:

    async def test_authorized_user_can_connect(self, settings):
        with override_settings(CHANNEL_LAYERS=TEST_CHANNEL_LAYERS):
            user = await create_user()
            communicator = await auth_connect(user)
            await communicator.disconnect()

    async def test_user_can_subscribe_to_realtime(self, settings):
        with override_settings(CHANNEL_LAYERS=TEST_CHANNEL_LAYERS):
            user = await create_user()
            channel_layer = get_channel_layer()

            # Test subscribing to realtime data
            communicator = await send_command(user, command="subscribe")

            response = await communicator.receive_json_from()

            assert response == {'command': 'subscribe', 'status': 'ok'}
            if response is not None:
                # Assert that a group is created within channel layer  :
                assert len(channel_layer.groups) == 1
                assert "realtime_" + str(user.id) in channel_layer.groups

            communicator = await send_command(user, command="unsubscribe")

            response_unsubscribe = await communicator.receive_json_from()

            assert response_unsubscribe == {'command': 'unsubscribe', 'status': 'ok'}

            # Test that the websocket channel was discarded from the group on disconnect
            await communicator.disconnect()
            # assert channel_layer.groups == {} issue group is not deleted

    async def test_user_can_receive_new_orders(self, settings):
        with override_settings(CHANNEL_LAYERS=TEST_CHANNEL_LAYERS):
            channel_layer = get_channel_layer()
            user1 = await create_user(username='user1', password='user1')
            user2 = await create_user(username='user2', password='user2')

            # Test subscribing to realtime data
            communicator1 = await send_command(user1, command="subscribe")
            communicator2 = await send_command(user2, command="subscribe")

            # Assert responses received
            assert await communicator1.receive_json_from() == {'command': 'subscribe', 'status': 'ok'}
            assert await communicator2.receive_json_from() == {'command': 'subscribe', 'status': 'ok'}

            # Add sample orders for both users
            order1 = await create_order(
                instrument="BNP",
                quantity=100,
                initial_price=99,
                user=user1
            )
            order2 = await create_order(
                instrument="EDF",
                quantity=200,
                initial_price=222,
                user=user2
            )

            # Test the websocket for the initial order is received only through the first channel
            response1 = await communicator1.receive_json_from()

            assert '{"id": 1, "quantity": 100, "initial_price": 99, "instrument": "BNP", ' \
                   '"type": "data.new"' in response1['content']
            assert response1['type'] == 'data.send'

            # Assert that nothing else is received through the first communicator
            assert await communicator1.receive_nothing() is True

            # Test the websocket for the second order is received only through the second channel
            response2 = await communicator2.receive_json_from()

            assert '{"id": 2, "quantity": 200, "initial_price": 222, "instrument": "EDF", ' \
                   '"type": "data.new"' in response2['content']

            assert response2['type'] == 'data.send'

            # Assert that nothing else is received through the second communicator
            assert await communicator1.receive_nothing() is True

            await communicator1.disconnect()
            await communicator2.disconnect()
            assert channel_layer.groups == {}

    async def test_user_can_receive_update_orders(self, settings):
        with override_settings(CHANNEL_LAYERS=TEST_CHANNEL_LAYERS):
            channel_layer = get_channel_layer()
            user1 = await create_user(username='user1', password='user1')
            user2 = await create_user(username='user2', password='user2')

            # Add sample orders for both users
            order1 = await create_order(
                instrument="BNP",
                quantity=100,
                initial_price=99,
                user=user1
            )
            order2 = await create_order(
                instrument="EDF",
                quantity=200,
                initial_price=222,
                user=user2
            )

            # Test subscribing to realtime data
            communicator1 = await send_command(user1, command="subscribe")
            communicator2 = await send_command(user2, command="subscribe")

            # Assert responses received
            assert await communicator1.receive_json_from() == {'command': 'subscribe', 'status': 'ok'}
            assert await communicator2.receive_json_from() == {'command': 'subscribe', 'status': 'ok'}

            # Add sample orders for both users
            await update_order(
                order1,
                instrument="BNP",
                quantity=333,
                initial_price=33,
                user=user1
            )
            await update_order(
                order2,
                instrument="EDF",
                quantity=444,
                initial_price=44,
                user=user2
            )

            # Test the websocket for the initial order is received only through the first channel
            response1 = await communicator1.receive_json_from()

            assert '{"id": 3, "quantity": 333, "initial_price": 33, "instrument": "BNP", ' \
                   '"type": "data.update"' in response1['content']
            assert response1['type'] == 'data.send'

            # Assert that nothing else is received through the first communicator
            assert await communicator1.receive_nothing() is True

            # Test the websocket for the second order is received only through the second channel
            response2 = await communicator2.receive_json_from()

            assert '{"id": 4, "quantity": 444, "initial_price": 44, "instrument": "EDF", ' \
                   '"type": "data.update"' in response2['content']

            assert response2['type'] == 'data.send'

            # Assert that nothing else is received through the second communicator
            assert await communicator1.receive_nothing() is True

            await communicator1.disconnect()
            await communicator2.disconnect()
            assert channel_layer.groups == {}


async def send_command(user, command="subscribe"):
    communicator = await auth_connect(user)
    await communicator.send_json_to({
        "command": command
    })
    return communicator


async def auth_connect(user):
    # Force authentication to get session ID.
    client = Client()
    client.force_login(user=user)

    # Pass session ID in headers to authenticate.
    communicator = WebsocketCommunicator(
        application=application,
        path='/data/stream/',
        headers=[(
            b'cookie',
            f'sessionid={client.cookies["sessionid"].value}'.encode('ascii')
        )]
    )
    connected, _ = await communicator.connect()
    assert connected is True
    return communicator


@database_sync_to_async
def create_order(**kwargs):
    return Data.objects.create(**kwargs)
