Rest API Datatable & Websockets Incremental Updates
===================================================

Basic example of a an integration between Django Channels, Django Rest API and Datatables.

The data are saved in the DB and are served as a datatable that is updated incrementally
via websockets sent whenever a new save is triggered within the data.

This example updates as well incrementally a linear function :

![f1]

The application uses the Django auth system to provide user accounts; users are only able to
subscribe to realtime updates on their data. The code checks the user credentials on incoming
WebSockets to allow users to subscribe to data streams based on their staff status.


Installation
------------

Manual installation
~~~~~~~~~~~~~~~~~~~

Make a new virtualenv for the project, and run::

    pip install -r requirements.txt

Then, you'll need Redis running locally (please refer to Redis deployment); the settings are configured to
point to ``localhost``, port ``6379``, but you can change this in the
``CHANNEL_LAYERS`` setting in ``settings.py``.

Finally, run::

    python manage.py migrate
    python manage.py runserver


Redis Docker Run
~~~~~~~~~~~~~~~~
You need to have docker deployed in order to run a live instance of Redis.

Run the app::

    docker run -p 6379:6379 -d redis:2.8

Usage
-----
Make yourself a superuser account::

    python manage.py createsuperuser

Then, log into http://localhost:8000/admin/ and add some data to the Data model and test that
the results are updated.

How It Works
------------

There's a normal Django view that just serves a HTML page behind the normal
``@login_required`` decorator, and that is basically a single-page app with
all the JS loaded into the ``index.html`` file.

There's a single consumer, which you can see routed to in ``webapp/routing.py``,
which is wrapped in the Channels authentication ASGI middleware so it can check
that your user is logged in and retrieve it to check access as you ask to join
rooms.

Whenever the client asks to activate realtime, it sends a WebSocket text frame with
a JSON encoded command to create a new group within the channel that is linked to the connected user.

When a new update is triggered from the save method overload within the model, a message
is sent (if the user is logged)


Next Actions
------------

If you want to try out making some changes and getting a feel for Channels,
here's some ideas and hints on how to do them:

* Make messages from yourself have a different message type. You'll need to
  edit the ``chat_message`` function to send a different packet down to the
  client based on if the ``chat.message`` event it gets is from you or not.

* Add message persistence. There's already a message sent to make a user join
  a room, so you can use that to send some previous messages; you'll need to make
  a model to save messages in, though.

* Make the Room list dynamically change as rooms are added and removed.
  You could add a common group that every socket joins and send events to it
  as rooms are created/deleted.

* Add message editing and deletion. You'll need to have made them persistent
  first; make sure you send message IDs down with every message so the client can
  keep track of them. Then, write some code to handle editing and trigger
  sending new messages down when this happens with the message ID it's happening to.


Further Reading
---------------

You can find the Channels documentation at http://channels.readthedocs.org


[f1]: http://chart.apis.google.com/chart?cht=tx&chl=f(x)=\sum_{i}^{n}a_i{\times}x_i
