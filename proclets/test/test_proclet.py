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

import unittest

from proclets.performative import Channel
from proclets.performative import Performative
from proclets.proclet import Proclet


class Control(Proclet):

    @property
    def dag(self):
        return {
            self.in_launch: [self.in_separation],
            self.in_separation: [self.in_recovery],
            self.in_recovery: [],
        }

    def in_launch(self, **kwargs):
        yield Performative()

    def in_separation(self, **kwargs):
        yield Performative()

    def in_recovery(self, **kwargs):
        yield Performative()


class Vehicle(Proclet):

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
        yield Performative()

    def in_separation(self, **kwargs):
        self.group = {
            item: Package(channels={"up": self.channels["down"]})
            for item in self.items
        }
        for item, p in self.group.items():
            yield p

            # Activate the initial transition
            yield Performative(
                channel=p.channels["up"], sender=self.uid, group=[p.uid],
                content=item
            )

    def in_orbit(self, **kwargs):
        yield Performative()

    def in_reentry(self, **kwargs):
        yield Performative()

    def in_recovery(self, **kwargs):
        yield Performative()


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

    def test_proclet(self):
        c = Control(channels={"uplink": Channel()})
        v = Vehicle(channels=c.channels)
        self.fail(list(c()))
