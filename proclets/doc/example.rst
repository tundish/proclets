..  Titling
    ##++::==~~--''``

Example
:::::::

`Describing behaviour of Processes with Many-to-Many Interactions
<https://dblp.org/rec/conf/apn/Fahland19>`_ by Dirk Fahland (2019).

.. literalinclude:: ../mission.py
   :pyobject: Control.dag

::

     Mission control|    pro_launch|We are go for launch
       Space vehicle|    pro_launch|Launch phase is complete
       Space vehicle|pro_separation|Separation initiated
     Mission control|pro_separation|Copy your separation
      Launch vehicle|   pro_reentry|Re-entering atmosphere
       Space vehicle|     pro_orbit|In orbit 1
     Mission control|   pro_reentry|Observing reentry of launch vehicle
       Space vehicle|     pro_orbit|In orbit 2
     Mission control|  pro_recovery|Team 1a3 briefed for recovery of launch vehicle
       Space vehicle|     pro_orbit|In orbit 3
       Recovery Team|  pro_recovery|Commencing search for launch vehicle
       Recovery Team|  pro_recovery|Rendezvous with launch vehicle
      Launch vehicle|  pro_recovery|Signing off
       Space vehicle|   pro_reentry|Re-entering atmosphere
       Recovery Team|   pro_standby|Team 1a3 standing by
     Mission control|   pro_reentry|Observing reentry of space vehicle
     Mission control|  pro_recovery|Team 1a3 briefed for recovery of space vehicle
       Recovery Team|  pro_recovery|Commencing search for space vehicle
       Recovery Team|  pro_recovery|Abandoning search for space vehicle
     Mission control|  pro_recovery|Team c4b briefed for recovery of space vehicle
       Recovery Team|   pro_standby|Team 1a3 standing by
       Recovery Team|  pro_recovery|Commencing search for space vehicle
       Recovery Team|  pro_recovery|Abandoning search for space vehicle
     Mission control|  pro_recovery|Team 1a3 briefed for recovery of space vehicle
       Recovery Team|   pro_standby|Team c4b standing by
       Recovery Team|  pro_recovery|Commencing search for space vehicle
       Recovery Team|  pro_recovery|Rendezvous with space vehicle
     Mission control|  pro_recovery|Mission complete
