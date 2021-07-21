..  Titling
    ##++::==~~--''``

Example
:::::::

This scenario was inspired by the teaching problem set out in the paper
`Describing behaviour of Processes with Many-to-Many Interactions
<https://dblp.org/rec/conf/apn/Fahland19>`_ by Dirk Fahland (2019).

Our example concerns the launch by Mission Control of a Space Vehicle.
The Vehicle separates from its launcher and orbits the earth.

Mission Control dispatches Recovery teams to locate both Vehicles after
they have separately reentered the atmosphere.

Full source code is `here
<https://raw.githubusercontent.com/tundish/proclets/master/proclets/mission.py>`_.

Nets
~~~~

The net of the Vehicle proclet is simple; a linear arrangement of
five transitions, terminating at the last.
 
.. literalinclude:: ../mission.py
   :pyobject: Vehicle.net

Recovery teams have three transitions, looping continually so that after having finished one job,
they are available for another.
 
.. literalinclude:: ../mission.py
   :pyobject: Recovery.net

Mission Control is the most complex net. It must continually monitor the Vehicles and Recovery teams.
Some transitions loop back to themselves.

.. literalinclude:: ../mission.py
   :pyobject: Control.net

Transitions
~~~~~~~~~~~

In Proclet theory, a Transition is *activated* when all its input places are occupied by *tokens*.
It can choose whether to *fire* based on *guard* conditions. It may also *block* for a while, in
the manner of Timed Petri Nets.

Here we implement each Transition as a single instance method of the Proclet object.
The code in each one should be succinct and easy to understand.

We aim to standardise on a small number of code patterns based on simple Python idiom.

Syncing
-------

The simplest form of communication between Proclets is synchronising on a transition they both share.
Here's how one Proclet offers synchronisation to another:

.. literalinclude:: ../mission.py
   :pyobject: Control.pro_launch

Blocking
--------

A Proclet waiting for synchronisation must block. In **proclets** this is achieved by returning from
the transition without a `yield` to another.

.. literalinclude:: ../mission.py
   :pyobject: Vehicle.pro_launch

Forking
-------

One Proclet may create another. The :meth:`~proclets.proclet.Proclet.create` function
adds a new Proclet to the *population*.

Note here how the Space Vehicle explicitly sets the *marking* of the Launch Vehicle, since the latter
is not supposed to go into orbit.

The Transition must `yield` the newly created Proclet. In this way the new Proclet gets added to the *domain*
of its parent for reference.
Then we send a synchronisation offer back to Mission Control.
The `uid` of the new Vehicle is included in the *context* of the message.

.. literalinclude:: ../mission.py
   :pyobject: Vehicle.pro_separation

Joining
-------

After reentry, we brief the Recovery teams.
Now we begin to get many-to-many interactions between Recovery proclets and Vehicle proclets.

Back at Mission Control, the looped transitions monitor the radio for news. These are not state synchronisations,
they are messages whose significance depend on Performative action.

.. literalinclude:: ../mission.py
   :lines: 104-108

Finishing
---------

Mission Control has a cardinality constraint. It launched one Vehicle, but it expects two to be recovered.
When this is detected, it halts the run by raising an exception:

.. literalinclude:: ../mission.py
   :lines: 110-112

Running
~~~~~~~

To run the example code, first install **proclets**::

    pip install proclets

Then launch the Mission::

    python -m proclets.mission

Output
~~~~~~

.. code-block:: none

     Mission control|    pro_launch|We are go for launch
       Space vehicle|    pro_launch|Launch phase is complete
       Space vehicle|pro_separation|Separation initiated
     Mission control|pro_separation|Copy your separation
      Launch vehicle|   pro_reentry|Re-entering atmosphere
       Space vehicle|     pro_orbit|In orbit 1
     Mission control|   pro_reentry|Observing reentry of launch vehicle
       Space vehicle|     pro_orbit|In orbit 2
     Mission control|  pro_recovery|Team 501 briefed for recovery of launch vehicle
       Space vehicle|     pro_orbit|In orbit 3
       Recovery Team|  pro_recovery|Commencing search for launch vehicle
       Recovery Team|  pro_recovery|Abandoning search for launch vehicle
       Space vehicle|   pro_reentry|Re-entering atmosphere
       Recovery Team|   pro_standby|Team 501 standing by
     Mission control|   pro_reentry|Observing reentry of space vehicle
     Mission control|  pro_recovery|Team 501 briefed for recovery of space vehicle
       Recovery Team|  pro_recovery|Commencing search for space vehicle
       Recovery Team|  pro_recovery|Abandoning search for space vehicle
     Mission control|  pro_recovery|Team 54e briefed for recovery of space vehicle
       Recovery Team|   pro_standby|Team 501 standing by
       Recovery Team|  pro_recovery|Commencing search for space vehicle
       Recovery Team|  pro_recovery|Abandoning search for space vehicle
     Mission control|  pro_recovery|Team 501 briefed for recovery of space vehicle
       Recovery Team|   pro_standby|Team 54e standing by
       Recovery Team|  pro_recovery|Commencing search for space vehicle
       Recovery Team|  pro_recovery|Abandoning search for space vehicle
     Mission control|  pro_recovery|Team 54e briefed for recovery of space vehicle
       Recovery Team|   pro_standby|Team 501 standing by
       Recovery Team|  pro_recovery|Commencing search for space vehicle
       Recovery Team|  pro_recovery|Abandoning search for space vehicle
     Mission control|  pro_recovery|Team 501 briefed for recovery of space vehicle
       Recovery Team|   pro_standby|Team 54e standing by
       Recovery Team|  pro_recovery|Commencing search for space vehicle
       Recovery Team|  pro_recovery|Abandoning search for space vehicle
     Mission control|  pro_recovery|Team 54e briefed for recovery of space vehicle
       Recovery Team|   pro_standby|Team 501 standing by
       Recovery Team|  pro_recovery|Commencing search for space vehicle
       Recovery Team|  pro_recovery|Rendezvous with space vehicle
     Mission control|  pro_recovery|Team 501 briefed for recovery of launch vehicle
       Space vehicle|  pro_recovery|Signing off
       Recovery Team|   pro_standby|Team 54e standing by
       Recovery Team|  pro_recovery|Commencing search for launch vehicle
       Recovery Team|  pro_recovery|Rendezvous with launch vehicle
      Launch vehicle|  pro_recovery|Signing off
       Recovery Team|   pro_standby|Team 501 standing by
     Mission control|  pro_recovery|Mission complete

