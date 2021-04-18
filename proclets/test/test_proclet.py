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
from proclets.performative import Performative as M
from proclets.proclet import Proclet


class Status(enum.Enum):

    activate = enum.auto()
    accepted = enum.auto()
    declined = enum.auto()
    received = enum.auto()
    complete = enum.auto()


class Control(Proclet):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.uplink = self.channels.get("uplink")

    @property
    def dag(self):
        return {
            self.in_launch: [self.in_separation],
            self.in_separation: [self.in_recovery],
            self.in_recovery: [],
        }

    def in_launch(self, **kwargs):
        yield from self.uplink.send(
            sender=self.uid, group=self.group,
            action=Status.activate, content=self.marking
        )
        yield from self.uplink.respond(self, {Status.accepted: Status.received, Status.complete: None})

    def in_separation(self, **kwargs):
        yield from self.uplink.send(
            sender=self.uid, group=self.group,
            action=Status.activate, content=self.marking
        )
        yield from self.uplink.respond(self, {Status.accepted: Status.received, Status.complete: None})

    def in_recovery(self, **kwargs):
        yield M(
            channel=self.channels["uplink"], sender=self.uid, group=self.group,
            action=Status.activate
        )


class Vehicle(Proclet):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.uplink = self.channels.get("uplink")

    @property
    def dag(self):
        return {
            self.in_launch: [self.in_separation],
            self.in_separation: [self.in_orbit, self.in_reentry],
            self.in_orbit: [self.in_orbit, self.in_reentry],
            self.in_reentry: [self.in_recovery],
            self.in_recovery: [],
        }

    def in_launch(self, **kwargs):
        yield from self.uplink.respond(self, {Status.activate: Status.accepted})

        # Transition here.

        yield from self.uplink.send(
            sender=self.uid, group=self.group,
            action=Status.complete,
        )
        yield None

    def in_separation(self, **kwargs):
        yield from self.uplink.respond(self, {Status.activate: Status.accepted})

        # Transition here.

        yield from self.uplink.send(
            sender=self.uid, group=self.group,
            action=Status.complete, content=self.marking
        )
        yield None

    def in_orbit(self, **kwargs):
        yield M()

    def in_reentry(self, **kwargs):
        yield M()

    def in_recovery(self, **kwargs):
        yield M()


class ProcletTests(unittest.TestCase):

    def test_initial_markings(self):
        c = Control()
        self.assertEqual({0}, c.marking)
        self.assertEqual((None, c.in_launch), c.arcs[0])
        self.assertEqual({0}, c.i_nodes[c.in_launch])

        v = Vehicle()
        self.assertEqual({0}, v.marking)
        self.assertEqual((None, v.in_launch), v.arcs[0])
        self.assertEqual({0}, v.i_nodes[v.in_launch])

    def test_flow(self):
        channels = {"uplink": Channel(), "beacon": Channel()}
        v = Vehicle(channels=dict(channels, bus=Channel()))
        c = Control(channels=channels, group={v.uid: v})
        v.group = {c.uid: c}

        for n in range(12):
            with self.subTest(n=n):
                c_flow = list(c())
                v_flow = list(v())
                self.assertTrue(c.marking)
                self.assertTrue(v.marking)
                self.assertFalse(any(i.content is None for i in c_flow))
                self.assertFalse(any(i.content is None for i in v_flow))
                print(*c_flow, sep="\n", file=sys.stderr)
                print(*v_flow, sep="\n", file=sys.stderr)
