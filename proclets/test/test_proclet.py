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
    complete = enum.auto()


class Control(Proclet):

    @property
    def dag(self):
        return {
            self.in_launch: [self.in_separation],
            self.in_separation: [self.in_recovery],
            self.in_recovery: [],
        }

    def in_launch(self, **kwargs):
        yield M(
            channel=self.channels["uplink"], sender=self.uid, group=self.group,
            action=Status.activate, content=self.marking
        )
        while not self.channels["uplink"].empty(self.uid):
            m = self.channels["uplink"].get(self.uid)
            if m.action == Status.accepted:
                yield

    def in_separation(self, **kwargs):
        yield M(
            channel=self.channels["uplink"], sender=self.uid, group=self.group,
            action=Status.activate, content=self.marking
        )

    def in_recovery(self, **kwargs):
        yield M(
            channel=self.channels["uplink"], sender=self.uid, group=self.group,
            action=Status.activate
        )


class Vehicle(Proclet):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.uplink = self.channels["uplink"]

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
        try:
            response = list(self.uplink.respond(self, {Status.activate: Status.accepted}))
            yield from response
        except queue.Empty:
            return

        if response:
            self.uplink.put(M(
                channel=self.uplink,
                sender=self.uid, group=response[0].group,
                action=Status.complete,
                content=self.marking
            ))
            yield None

    def in_separation(self, **kwargs):
        if self.channels["uplink"].empty(self.uid):
            yield M(sender=self.uid, content=self.marking)
            return

        while not self.channels["uplink"].empty(self.uid):
            m = self.channels["uplink"].get(self.uid)
            if m.action == Status.activate:
                yield M(
                    channel=self.channels["uplink"],
                    sender=self.uid, group=[p.uid],
                    action=Status.accepted,
                    content=self.marking
                )
                yield
        else:
            yield M(sender=self.uid, content=self.marking)


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
        for n in range(12):
            with self.subTest(n=n):
                c_flow = list(c())
                v_flow = list(v())
                self.assertTrue(c.marking)
                self.assertTrue(v.marking)
                print(*list(filter(None, c())), sep="\n", file=sys.stderr)
                print(*list(filter(None, v())), sep="\n", file=sys.stderr)
