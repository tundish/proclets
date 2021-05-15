..  Titling
    ##++::==~~--''``

Channels
::::::::

Channels are the means by which Proclets communicate. Being autonomous, :ref:`proclets` share no
data structures directly. Therefore, if their transitions are to synchronise, it must be by means
of exchanging messages. This is what Channels do. They accept messages, and store them permanently,
so the recipient can use them to make decisions.

In order to achieve this, the messages have to be of a certain form; a Performative_ described in
`the 2001 paper <https://dblp.org/rec/journals/ijcis/AalstBEW01>`_.

**Proclets** defines this Performative_ type,
but the Channel API is such that you don't have to explicitly create them yourself.
However it is useful to understand their structure because it enables powerful interactions and protocols.


.. autoclass:: proclets.channel.Channel
   :members:
   :member-order: bysource

.. _performative:

Performatives
:::::::::::::

.. py:class:: Performative(**kwargs)

    :param ts:      A time stamp for creation. Generated automatically.
                    Subject to resolution of the system clock. Some objects may share the same time stamp.
    :param uid:     A unique id. Generated automatically.
    :param channel: A channel object. Set automatically by :meth:`proclets.channel.Channel.send`.
    :param sender:  Uid of the sender.
    :param group:   Contains uids of intended recipients.
    :param connect: A uid to identify a thread of messages. Set automatically by Channel methods.
    :param context: Contains uids of objects to which the message relates. Application specific.
    :param action:  An object denoting a Performative action. Application specific.
    :param content: An object containing Performative content. Application specific.
    :type  ts:      int
    :type  uid:     uuid.UUID
    :type  channel: object
    :type  sender:  uuid.UUID
    :type  group:   set
    :type  context: set


