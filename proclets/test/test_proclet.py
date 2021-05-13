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
from proclets.mission import mission
from proclets.proclet import Proclet


class ProcletTests(unittest.TestCase):

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
        procs = mission()

        for n in range(16):
            for p in procs:
                self.assertTrue(p.marking)
                flow = list(p())
                with self.subTest(n=n):

                    self.assertTrue(p)

        objs = set(procs).union({d for p in procs for d in p.domain})
        control = next(i for i in objs if isinstance(i, Control))
        vehicles = [i for i in objs if isinstance(i, Vehicle)]
        self.assertEqual(2, len(vehicles))
        recoveries = [i for i in objs if isinstance(i, Recovery)]
        self.assertEqual(2, len(recoveries))
