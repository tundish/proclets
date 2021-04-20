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
from proclets.performative import Entry
from proclets.performative import Exit
from proclets.proclet import Proclet


class Control(Proclet):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.beacon = self.channels.get("beacon")
        self.uplink = self.channels.get("uplink")
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
                action=Entry.request, content=f"{self.name} go for launch"
            ))
            yield self.tasks[this]

        yield from self.uplink.respond(
            self, this,
            actions={Entry.promise: Entry.confirm, Exit.deliver: None},
            contents={
                Entry.promise: f"{self.name} copy your launch",
                Exit.deliver: f"{self.name} launch complete"
            },
        )

    def pro_separation(self, this, **kwargs):
        if not self.tasks.get(this):
            self.tasks[this] = next(self.uplink.send(
                sender=self.uid, group=self.group,
                action=Entry.request, content=f"{self.name} go for separation"
            ))
            yield self.tasks[this]

        yield from self.uplink.respond(
            self, this,
            actions={Entry.promise: Entry.confirm, Exit.deliver: None},
            contents={
                Entry.promise: f"{self.name} copy your separation",
                Exit.deliver: f"{self.name} separation complete"
            },
        )

    def pro_recovery(self, this, **kwargs):
        try:
            msg = self.beacon.get(self.uid)
            yield Recovery("Recovery Team", marking={0})
        except queue.Empty:
            pass

        if self.tally[this] == 2:
            yield None


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
            self.pro_orbit: [self.pro_orbit, self.pro_reentry],
            self.pro_reentry: [self.pro_recovery],
            self.pro_recovery: [],
        }

    def pro_launch(self, this, **kwargs):
        if not self.tasks.get(this):
            try:
                m = next(
                    self.uplink.respond(
                        self, this,
                        actions={Entry.request: Entry.promise},
                        contents={Entry.request: f"{self.name} acknowledge go for launch"},
                    )
                )
            except (StopIteration, queue.Empty):
                return
            else:
                self.tasks[this] = m.connect
                yield m

        yield from self.uplink.send(
            sender=self.uid, group=self.group, connect=self.tasks[this],
            action=Exit.deliver, content=f"{self.name} launch complete"
        )
        yield None

    def pro_separation(self, this, **kwargs):
        if not self.tasks.get(this):
            try:
                m = next(
                    self.uplink.respond(
                        self, this,
                        actions={Entry.request: Entry.promise},
                        contents={Entry.request: f"{self.name} acknowledge go for separation"},
                    )
                )
            except (StopIteration, queue.Empty):
                return
            else:
                self.tasks[this] = m.connect
                yield m

        yield Vehicle(
            "Launch vehicle",
            channels={"beacon": self.beacon}, group=self.group.copy(),
            marking=self.i_nodes[self.pro_reentry]
        )

        yield from self.uplink.send(
            sender=self.uid, group=self.group, connect=self.tasks[this],
            action=Exit.deliver, content=f"{self.name} separation complete"
        )
        yield None

    def pro_orbit(self, this, **kwargs):
        if not self.uplink:
            yield None

        n = self.tasks.get(this, 1)
        if n < 4:
            yield from self.uplink.send(
                sender=self.uid, group=self.group,
                action=Entry.message, content=f"{self.name} in orbit {n}"
            )
            self.tasks[this] = n + 1
        else:
            yield from self.uplink.send(
                sender=self.uid, group=self.group,
                action=Exit.message, content=f"{self.name} orbits complete"
            )
            yield None

    def pro_reentry(self, this, **kwargs):
        yield from self.beacon.send(
            sender=self.uid, group=self.group,
            action=Exit.message, content=f"{self.name} in reentry"
        )
        yield None

    def pro_recovery(self, this, **kwargs):
        yield None


class Recovery(Proclet):

    @property
    def dag(self):
        return {
            self.pro_recovery: [],
        }

    def pro_recovery(self, this, **kwargs):
        yield None


class ProcletTests(unittest.TestCase):

    @staticmethod
    def report(m):
        try:
            return "{connect!s:>36}|{sender.hex}|{action:<14}|{content}".format(**vars(m))
        except KeyError:
            return "{0}|{1}|Create Proclet|{2.name}".format(" "*36, " "*32, m)

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
        v = Vehicle("Space vehicle", channels=dict(channels, bus=Channel()))
        c = Control("Mission control", channels=channels, group={v.uid: v})
        v.group = {c.uid: c}
        self.assertIn(c.pro_launch, c.activated)
        self.assertIn(v.pro_launch, v.activated)

        for n in range(6):
            with self.subTest(n=n):
                c_flow = list(c())
                v_flow = list(v())
                self.assertTrue(c.marking)
                self.assertTrue(v.marking)
                self.assertFalse(any(i.content is None for i in c_flow if not isinstance(i, Proclet)))
                self.assertFalse(any(i.content is None for i in v_flow if not isinstance(i, Proclet)))
                print(*[self.report(i) for i in c_flow], sep="\n", file=sys.stderr)
                print(*[self.report(i) for i in v_flow], sep="\n", file=sys.stderr)
            if n == 0:
                pass
                #self.assertIn(c.pro_separation, c.activated)
                #self.assertIn(v.pro_separation, v.activated)
