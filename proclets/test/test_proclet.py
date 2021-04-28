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
            self.pro_recovery: [],
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
            r = Recovery.create(name="Recovery Team", channels=channels, group={self.uid}, marking={0})
            yield from self.vhf.send(
                sender=self.uid, group=[r.uid],
                action=Init.request, content="Briefing Recovery Team"
            )
            yield r


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
            self.pro_reentry: [self.pro_recovery],
            self.pro_recovery: [],
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
                channels={"beacon": self.beacon}, group=self.group.copy(),
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
        if self.uplink and self.tally[self.pro_orbit] != 4:
            return
        elif self.tally[this]:
            yield None
        else:
            yield from self.beacon.send(
                sender=self.uid, group=self.group,
                action=Exit.message, content="Re-entering atmosphere"
            )

    def pro_recovery(self, this, **kwargs):
        yield None


class Recovery(Proclet):

    @property
    def dag(self):
        return {
            self.pro_recovery: [],
        }

    def pro_recovery(self, this, **kwargs):
        if hasattr(self, "task"):
            yield None
        try:
            m = next(
                self.channels.get("vhf").respond(
                    self,
                    actions={Init.request: Init.promise},
                    contents={Init.request: "On our way"},
                )
            )
        except (StopIteration, queue.Empty):
            return
        else:
            self.task = m.connect
            yield m


class ProcletTests(unittest.TestCase):

    @staticmethod
    def report(m, lookup):
        try:
            source = lookup[m.sender]
            return "{connect!s:>36}|{source.name:15}|{action:<12}|{content}".format(source=source, **vars(m))
        except AttributeError:
            return "{0}|{1}|Call Proclet|{2.name}".format(" "*36, " "*15, m)

    def test_initial_markings(self):
        c = Control(None)
        self.assertEqual({0}, c.marking)
        self.assertEqual((None, c.pro_launch), c.arcs[0])
        self.assertEqual({0}, c.i_nodes[c.pro_launch])

        v = Vehicle(None)
        self.assertEqual({0}, v.marking)
        self.assertEqual((None, v.pro_launch), v.arcs[0])
        self.assertEqual({0}, v.i_nodes[v.pro_launch])

    def test_flow(self):
        channels = {"uplink": Channel(), "beacon": Channel()}
        v = Vehicle.create(name="Space vehicle", channels=channels)
        c = Control.create(name="Mission control", channels=dict(channels, vhf=Channel()), group={v.uid: v})
        v.group = {c.uid: c}
        lookup = {c.uid: c, v.uid: v}

        for n in range(12):
            c_flow = list(c())
            v_flow = list(v())
            with self.subTest(n=n):
                self.assertTrue(v.marking)
                self.assertTrue(c.marking)
                for flow in (c_flow, v_flow):
                    for item in flow:
                        if isinstance(item, Proclet):
                            lookup[item.uid] = item
                        else:
                            self.assertTrue(item.content)

                        print(self.report(item, lookup), file=sys.stderr)

                if n == 0:
                    self.assertIn(c.pro_launch, c.enabled)
                    self.assertIn(v.pro_launch, v.enabled)
                elif n == 2:
                    self.assertIn(c.pro_separation, c.enabled)
                    self.assertIn(v.pro_separation, v.enabled)
                elif n == 4:
                    self.assertIn(c.pro_separation, c.enabled)
                    self.assertIn(v.pro_orbit, v.enabled)
                elif n == 5:
                    self.assertIn(c.pro_recovery, c.enabled)
                    self.assertIn(v.pro_orbit, v.enabled)
                elif n == 7:
                    self.assertIn(c.pro_recovery, c.enabled)
                    self.assertIn(v.pro_orbit, v.enabled)
                elif n == 8:
                    self.assertIn(c.pro_recovery, c.enabled)
                    self.assertIn(v.pro_reentry, v.enabled)
                elif n == 9:
                    self.assertIn(c.pro_recovery, c.enabled)
                    self.assertIn(v.pro_reentry, v.enabled)
                elif n == 10:
                    self.assertIn(c.pro_recovery, c.enabled)
                    self.assertIn(v.pro_recovery, v.enabled)

        vehicles = [i for i in lookup.values() if isinstance(i, Vehicle)]
        self.assertEqual(2, len(vehicles))
        recoveries = [i for i in lookup.values() if isinstance(i, Recovery)]
        self.assertEqual(2, len(recoveries))
