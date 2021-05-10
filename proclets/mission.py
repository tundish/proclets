#!/usr/bin/env python3
#   encoding: utf-8

# This file is part of proclets.
#
# Proclets is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Proclets is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with proclets.  If not, see <http://www.gnu.org/licenses/>.

import enum
import functools
import itertools
import logging
import operator
import random
import sys
import queue
import unittest

from proclets.channel import Channel
from proclets.proclet import Proclet
from proclets.types import Init
from proclets.types import Exit


class Control(Proclet):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.beacon = self.channels.get("beacon")
        self.uplink = self.channels.get("uplink")
        self.vhf = self.channels.get("vhf")

    @property
    def dag(self):
        return {
            self.pro_launch: [self.pro_separation],
            self.pro_separation: [self.pro_reentry],
            self.pro_reentry: [self.pro_recovery, self.pro_reentry],
            self.pro_recovery: [self.pro_recovery, self.pro_complete],
            self.pro_complete: [],
        }

    @property
    def recoveries(self):
        return [
            msgs[-1] for msgs in self.channels["vhf"].view(self.uid)
            if msgs[-1].action == Exit.deliver
        ]

    def pro_launch(self, this, **kwargs):
        logging.info("We are go for launch", extra={"proclet": self})
        yield from self.uplink.send(
            sender=self.uid, group=self.group,
            action=this.__name__,
        )
        yield None

    def pro_separation(self, this, **kwargs):
        try:
            sync = next(
                i for i in self.uplink.receive(self, this)
                if i.action == this.__name__
            )
        except StopIteration:
            pass
        else:
            logging.info("Copy your separation", extra={"proclet": self})
            yield None

    def pro_reentry(self, this, **kwargs):
        try:
            sync = next(
                i for i in self.beacon.receive(self, this)
                if i.action == this.__name__
            )
        except StopIteration:
            pass
        else:
            vehicle = self.population[sync.sender].name.lower()
            logging.info(f"Observing reentry of {vehicle}", extra={"proclet": self})
            channels = {k: self.channels[k] for k in ("beacon", "vhf")}
            yield Recovery.create(
                name="Recovery Team",
                target=sync.sender,
                channels=channels,
                group=[self.uid],
            )
            yield None

    def pro_recovery(self, this, **kwargs):
        targets = [i.target for i in self.domain]
        for p in self.domain:
            if not p.duty:
                yield from self.vhf.send(
                    sender=self.uid, group={p.uid},
                    action=Init.request, context={p.target},
                )
                vehicle = self.population[p.target].name.lower()
                logging.info(f"Team {p.uid.hex[:3]} briefed for recovery of {vehicle}", extra={"proclet": self})
                yield None
        logging.info(self.recoveries, extra={"proclet": self})

    def pro_complete(self, this, **kwargs):
        yield


class Recovery(Proclet):


    def __init__(self, target, *args, luck=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.target = target
        self.luck = random.triangular(0, 1, 3/4) if luck is None else luck

    @property
    def dag(self):
        return {
            self.pro_tasking: [self.pro_recovery],
            self.pro_recovery: [self.pro_standby],
            self.pro_standby: [self.pro_tasking],
        }

    @property
    def duty(self):
        return next(
            (msgs[0] for msgs in self.channels["vhf"].view(self.uid)
            if {m.action for m in msgs}.isdisjoint({Exit.abandon, Exit.deliver})),
            None
        )

    def pro_tasking(self, this, **kwargs):
        try:
            m = next(
                self.channels["vhf"].respond(
                    self, this,
                    actions={Init.request: Init.promise},
                )
            )
            logging.info(m, extra={"proclet": self})
            vehicle = self.population[next(iter(self.duty.context))].name.lower()
            logging.info(f"Commencing search for {vehicle}", extra={"proclet": self})
            yield None
        except (StopIteration, queue.Empty):
            return

    def pro_recovery(self, this, **kwargs):
        vehicle = self.population[next(iter(self.duty.context))].name.lower()
        if random.random() < self.luck:
            yield from self.channels["beacon"].send(
                sender=self.uid, group=self.duty.context,
                action=this.__name__,
            )
            yield from self.channels["vhf"].send(
                sender=self.uid, group={self.duty.sender},
                action=Exit.deliver,
            )
            logging.info(f"Rendezvous with {vehicle}", extra={"proclet": self})
            yield None
        else:
            yield from self.channels["vhf"].send(
                sender=self.uid, group={self.duty.sender},
                action=Exit.abandon,
            )
            logging.info(f"Abandoning search for {vehicle}", extra={"proclet": self})
            yield None

    def pro_standby(self, this, **kwargs):
        logging.info("Standing by", extra={"proclet": self})
        yield


class Vehicle(Proclet):

    def __init__(self, *args, orbits=0, **kwargs):
        super().__init__(*args, **kwargs)
        self.beacon = self.channels.get("beacon")
        self.uplink = self.channels.get("uplink")
        self.orbits = orbits

    @property
    def dag(self):
        return {
            self.pro_launch: [self.pro_separation],
            self.pro_separation: [self.pro_orbit, self.pro_reentry],
            self.pro_orbit: [self.pro_reentry],
            self.pro_recovery: [self.pro_recovery, self.pro_complete],
            self.pro_complete: [],
        }

    def pro_launch(self, this, **kwargs):
        try:
            sync = next(
                i for i in self.uplink.receive(self, this)
                if i.action == this.__name__
            )
        except StopIteration:
            pass
        else:
            logging.info("Launch phase is complete", extra={"proclet": self})
            yield None

    def pro_separation(self, this, **kwargs):
        logging.info("Separation initiated", extra={"proclet": self})
        v = Vehicle.create(
            name="Launch vehicle", orbits=None,
            channels={"beacon": self.beacon}, group=self.group,
            marking=self.i_nodes[self.pro_reentry],
        )
        yield v
        yield from self.uplink.send(
            sender=self.uid, group=self.group, context={v.uid},
            action=this.__name__,
        )
        yield None

    def pro_orbit(self, this, **kwargs):
        if self.orbits is None:
            yield None

        if self.orbits < 3:
            self.orbits += 1
            logging.info(f"In orbit {self.orbits}", extra={"proclet": self})
        else:
            yield None

    def pro_reentry(self, this, **kwargs):
        if not self.tally[this.__name__]:
            logging.info("Re-entering atmosphere", extra={"proclet": self})
            yield from self.beacon.send(
                sender=self.uid, group=self.group,
                action=this.__name__,
            )
        yield None

    def pro_recovery(self, this, **kwargs):
        try:
            sync = next(
                i for i in self.channels["beacon"].receive(self, this)
                if i.action == this.__name__
            )
        except StopIteration:
            return
        else:
            yield None

    def pro_complete(self, this, **kwargs):
        try:
            sync = next(
                i for i in self.channels["beacon"].receive(self, this)
                if i.action == this.__name__
            )
        except StopIteration:
            return
        else:
            yield sync
            yield None


def mission():
    channels = {"uplink": Channel(), "beacon": Channel()}
    v = Vehicle.create(name="Space vehicle", channels=channels)
    c = Control.create(name="Mission control", channels=dict(channels, vhf=Channel()), group=[v.uid])
    v.group = [c.uid]
    return (c, v)


if __name__ == "__main__":
    logging.basicConfig(
        style="{", format="{proclet.name:>16}|{funcName:>14}|{message}",
        level=logging.INFO,
    )
    procs = mission()
    for n in range(32):
        for p in procs:
            flow = list(p())
            for i in flow:
                logging.debug(i, extra={"proclet": p})
