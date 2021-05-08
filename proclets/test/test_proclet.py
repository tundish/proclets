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
import random
import sys
import queue
import unittest

from proclets.channel import Channel
from proclets.mission import Control
from proclets.mission import Recovery
from proclets.mission import Vehicle
from proclets.proclet import Proclet


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

        for n in range(16):
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
                            pass
                            #self.assertTrue(item.content)

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
                    pass
                    #self.assertIn(c.pro_recovery, c.enabled)
                    #self.assertIn(v.pro_recovery, v.enabled)

        vehicles = [i for i in lookup.values() if isinstance(i, Vehicle)]
        self.assertEqual(2, len(vehicles))
        recoveries = [i for i in lookup.values() if isinstance(i, Recovery)]
        self.assertEqual(2, len(recoveries))
