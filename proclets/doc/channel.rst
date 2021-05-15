..  Titling
    ##++::==~~--''``

Channels
::::::::

Channels are the means by which Proclets communicate. Being autonomous, :ref:`proclets` share no
data structures directly. Therefore, if their transitions are to synchronise, it must be by means
of exchanging messages. This is what Channels do. They accept messages, and store them permanently,
so the recipient can use them to make decisions.

In order to achieve this, the messages have to be of a certain form; a `Performative` described in
`the 2001 paper <https://dblp.org/rec/journals/ijcis/AalstBEW01>`_.

**Proclets** defines this :class:`~proclets.types.Performative` type,
but the Channel API is such that you don't have to explicitly create them yourself.
However it is useful to understand their structure because it enables powerful interactions and protocols.


.. autoclass:: proclets.channel.Channel
   :members:
   :member-order: bysource

.. _performative:

Performatives
:::::::::::::

.. autoattribute:: proclets.types.Performative
   :annotation: (pkg, description, metadata, paths, interludes)


