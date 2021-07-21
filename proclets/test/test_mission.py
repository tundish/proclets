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

import itertools
import unittest
import sys

from proclets.mission import Control
from proclets.mission import Recovery
from proclets.mission import Vehicle
from proclets.mission import mission
from proclets.types import Termination


class MissionTests(unittest.TestCase):

    def setUp(self):
        self.procs = mission()

    @property
    def objects(self):
        rv = list(self.procs)
        for p in self.procs:
            for d in p.domain:
                if d not in rv:
                    rv.append(d)
        return rv

    @staticmethod
    def run_to_terminate(procs):
        n = 0
        for p in itertools.cycle(procs):
            try:
                for m in p():
                    yield n, p, m
                    n += 1
            except Termination:
                break
            except Exception as e:
                #print(n, m, p, file=sys.stderr)
                raise

    def test_flow(self):
        for n, p, m in self.run_to_terminate(self.procs):
            print(n, p, p.marking)

    def test_vehicles(self):
        for n, p, m in self.run_to_terminate(self.procs):
            pass

        for n, v in enumerate(i for i in self.objects if isinstance(i, Vehicle)):
            with self.subTest(n=n, v=v):
                self.assertEqual({0}, v.i_nodes[v.pro_launch])
                self.assertEqual({1}, v.o_nodes[v.pro_launch])
                self.assertEqual((1, 0)[n], v.tally["pro_launch"], v.tally)

                self.assertEqual({1}, v.i_nodes[v.pro_separation])
                self.assertEqual({2}, v.o_nodes[v.pro_separation])
                self.assertEqual((1, 0)[n], v.tally["pro_separation"], v.tally)

                self.assertEqual({2}, v.i_nodes[v.pro_orbit])
                self.assertEqual({3}, v.o_nodes[v.pro_orbit])
                self.assertEqual((4, 0)[n], v.tally["pro_orbit"], v.tally)

                self.assertEqual({3}, v.i_nodes[v.pro_reentry], v.arcs)
                self.assertEqual({4}, v.o_nodes[v.pro_reentry])
                self.assertEqual((1, 1)[n], v.tally["pro_reentry"], v.tally)

    def test_recovery(self):
        for n, p, m in self.run_to_terminate(self.procs):
            pass

        recoveries = [i for i in self.objects if isinstance(i, Recovery)]
        self.assertEqual(2, len(recoveries))

    def test_control(self):
        control = next(i for i in self.objects if isinstance(i, Control))
        limit = float("inf")
        for n, p, m in self.run_to_terminate(self.procs):
            if len(getattr(control, "results", [])) == 2:
                limit = sum(control.tally.values())

            with self.subTest(n=n, limit=limit):
                self.assertFalse(sum(control.tally.values()) > limit)
