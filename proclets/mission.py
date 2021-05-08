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
import logging
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
        self.tasks = {}

    @property
    def dag(self):
        return {
            self.pro_launch: [self.pro_separation],
            self.pro_separation: [self.pro_recovery],
            self.pro_recovery: [self.pro_recovery, self.pro_complete],
            self.pro_complete: [],
        }

    def pro_launch(self, this, **kwargs):
        if not self.tasks.get(this):
            self.tasks[this] = next(self.uplink.send(
                sender=self.uid, group=self.group,
                action=Init.request, content="Advise ready for launch"
            ))
            yield self.tasks[this]

        yield from self.uplink.respond(
            self,
            actions={Init.promise: Init.confirm, Exit.deliver: None},
            contents={
                Init.promise: "Launch initiated",
                Exit.deliver: "Launch is complete"
            },
        )

    def pro_launch(self, this, **kwargs):
        logging.info("We are go for launch")
        yield from self.uplink.send(
            sender=self.uid, group=self.group,
            action=this.__name__,
        )
        yield None

    def pro_separation(self, this, **kwargs):
        if not self.tasks.get(this):
            self.tasks[this] = next(self.uplink.send(
                sender=self.uid, group=self.group,
                action=Init.request, content="You are go for separation"
            ))
            yield self.tasks[this]

        yield from self.uplink.respond(
            self,
            actions={Init.promise: Init.confirm, Exit.deliver: None},
            contents={
                Init.promise: "Copy your separation",
                Exit.deliver: "Separation complete"
            },
        )

    def pro_recovery(self, this, **kwargs):
        if this not in self.tasks:
            self.tasks[this] = set()

        try:
            msg = self.beacon.get(self.uid)
        except queue.Empty:
            return

        if msg.sender not in self.tasks[this]:
            self.tasks[this].add(msg.sender)
            channels = {k: self.channels[k] for k in ("beacon", "vhf")}
            r = Recovery.create(
                name="Recovery Team",
                channels=channels,  
                group={self.uid}
            )
            yield r
            yield from self.vhf.send(
                sender=self.uid, group=[r.uid],
                action=Init.request, context={msg.sender},
                content="Briefing Recovery Team"
            )

    def pro_complete(self, this, **kwargs):
        yield


class Vehicle(Proclet):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.beacon = self.channels.get("beacon")
        self.uplink = self.channels.get("uplink")
        self.tasks = {}

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
        if not self.tasks.get(this):
            try:
                m = next(
                    self.uplink.respond(
                        self,
                        actions={Init.request: Init.promise},
                        contents={Init.request: "We are go for launch"},
                    )
                )
            except (StopIteration, queue.Empty):
                return
            else:
                self.tasks[this] = m.connect
                yield m
        else:
            yield from self.uplink.send(
                sender=self.uid, group=self.group, connect=self.tasks[this],
                action=Exit.deliver, content="Launch phase is complete"
            )
            yield None

    def pro_launch(self, this, **kwargs):
        try:
            sync = next(
                i for i in self.uplink.receive(self, this)
                if i.action == this.__name__
            )
        except StopIteration:
            pass
        else:
            yield None

    def pro_separation(self, this, **kwargs):
        if not self.tasks.get(this):
            try:
                m = next(
                    self.uplink.respond(
                        self,
                        actions={Init.request: Init.promise},
                        contents={Init.request: "Separation initiated"},
                    )
                )
            except (StopIteration, queue.Empty):
                return
            else:
                self.tasks[this] = m.connect
                yield m
        else:
            yield Vehicle.create(
                name="Launch vehicle",
                channels={"beacon": self.beacon}, group=self.group,
                marking=self.i_nodes[self.pro_reentry]
            )

            yield from self.uplink.send(
                sender=self.uid, group=self.group, connect=self.tasks[this],
                action=Exit.deliver, content="Separation complete"
            )
            yield None

    def pro_orbit(self, this, **kwargs):
        if not self.uplink:
            yield None

        n = self.tasks.get(this, 1)
        if n < 4:
            yield from self.uplink.send(
                sender=self.uid, group=self.group,
                action=Init.message, content=f"In orbit {n}"
            )
            self.tasks[this] = n + 1
        else:
            yield from self.uplink.send(
                sender=self.uid, group=self.group,
                action=Exit.message, content="Orbits complete"
            )
            yield None

    def pro_reentry(self, this, **kwargs):
        if self.uplink and self.tally[self.pro_orbit] < 4:
            return
        else:
            yield from self.beacon.send(
                sender=self.uid, group=self.group,
                action=Exit.message, content="Re-entering atmosphere"
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
            yield sync
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


class Recovery(Proclet):


    def __init__(self, *args, luck=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.luck = random.triangular(0, 1, 3/4) if luck is None else luck

    @property
    def dag(self):
        return {
            self.pro_recovery: [self.pro_recovery, self.pro_complete],
            self.pro_complete: [],
        }

    def pro_recovery(self, this, **kwargs):
        try:
            m = next(
                self.channels.get("vhf").respond(
                    self,
                    actions={Init.request: Init.promise},
                    contents={Init.request: "On our way"},
                )
            )
            yield m
            yield from self.channels["beacon"].send(
                sender=self.uid, group=m.context,
                action=this.__name__,
                content="Rendezvous on beacon"
            )
            yield from self.channels["vhf"].send(
                sender=self.uid, group=[m.sender],
                action=Exit.deliver,
            )
        except (StopIteration, queue.Empty):
            return
        else:
            yield None

    def pro_complete(self, this, **kwargs):
        yield

def mission():
    channels = {"uplink": Channel(), "beacon": Channel()}
    v = Vehicle.create(name="Space vehicle", channels=channels)
    c = Control.create(name="Mission control", channels=dict(channels, vhf=Channel()), group=[v.uid])
    v.group = [c.uid]
    return (c, v)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, style="{", format="{message}")
    procs = mission()
    for n in range(16):
        for p in procs:
            flow = list(p())
            for i in flow:
                logging.info(i)
