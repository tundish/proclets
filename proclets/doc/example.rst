..  Titling
    ##++::==~~--''``

Example
:::::::

This scenario was inspired by the teaching problem set out in the paper
`Describing behaviour of Processes with Many-to-Many Interactions
<https://dblp.org/rec/conf/apn/Fahland19>`_ by Dirk Fahland (2019).

Our example concerns the launch by Mission Control of a Space Vehicle.
The Vehicle separates from its launcher and orbits the earth.

Mission Control dispatches Recovery Teams to locate both Vehicles after
they have separately reentered the atmosphere.

Full source code is `here
<https://raw.githubusercontent.com/tundish/proclets/master/proclets/mission.py>`_.

DAGs
~~~~

The net of the Vehicle proclet is simple; a linear arrangement of
five transitions, terminating at the last.
 
.. literalinclude:: ../mission.py
   :pyobject: Vehicle.dag

Recovery teams have three transitions, looping continually so that after having finished one job,
they are available for another.
 
.. literalinclude:: ../mission.py
   :pyobject: Recovery.dag

Mission Control is the most complex net. Some transitions loop back to themselves.

.. literalinclude:: ../mission.py
   :pyobject: Control.dag

Transitions
~~~~~~~~~~~

In Proclet theory, a Transition is *activated* when all its input places are occupied by *tokens*.
It can choose whether to *fire* based on *guard* conditions. It may also *block* for a while, in
the manner of Timed Petri Nets.

Here we implement each Transition as a single instance method of the Proclet object.
It will be useful to adopt a small number of code patterns based on simple Python idiom.

Syncing
-------

.. literalinclude:: ../mission.py
   :pyobject: Control.pro_launch

Blocking
--------

.. literalinclude:: ../mission.py
   :pyobject: Vehicle.pro_launch

Forking
-------

.. literalinclude:: ../mission.py
   :pyobject: Vehicle.pro_separation

Joining
-------

.. literalinclude:: ../mission.py
   :pyobject: Control.recoveries

Finishing
---------

.. literalinclude:: ../mission.py
   :lines: 89-93

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
     Mission control|  pro_recovery|Team 81a briefed for recovery of launch vehicle
       Space vehicle|     pro_orbit|In orbit 3
       Recovery Team|  pro_recovery|Commencing search for launch vehicle
       Recovery Team|  pro_recovery|Abandoning search for launch vehicle
       Space vehicle|   pro_reentry|Re-entering atmosphere
       Recovery Team|   pro_standby|Team 81a standing by
     Mission control|   pro_reentry|Observing reentry of space vehicle
     Mission control|  pro_recovery|Team 81a briefed for recovery of launch vehicle
       Recovery Team|  pro_recovery|Commencing search for launch vehicle
       Recovery Team|  pro_recovery|Rendezvous with launch vehicle
     Mission control|  pro_recovery|Team 1f4 briefed for recovery of space vehicle
      Launch vehicle|  pro_recovery|Signing off
       Recovery Team|   pro_standby|Team 81a standing by
       Recovery Team|  pro_recovery|Commencing search for space vehicle
       Recovery Team|  pro_recovery|Abandoning search for space vehicle
     Mission control|  pro_recovery|Team 81a briefed for recovery of space vehicle
       Recovery Team|   pro_standby|Team 1f4 standing by
       Recovery Team|  pro_recovery|Commencing search for space vehicle
       Recovery Team|  pro_recovery|Rendezvous with space vehicle
     Mission control|  pro_recovery|Mission complete

