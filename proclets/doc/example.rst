..  Titling
    ##++::==~~--''``

Example
:::::::

DAGs
~~~~

.. literalinclude:: ../mission.py
   :pyobject: Vehicle.dag

.. literalinclude:: ../mission.py
   :pyobject: Recovery.dag

.. literalinclude:: ../mission.py
   :pyobject: Control.dag

Transitions
~~~~~~~~~~~

Contrast patterns.

Enabled -> Activated.

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

One-shots
---------

.. literalinclude:: ../mission.py
   :pyobject: Vehicle.pro_reentry

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

