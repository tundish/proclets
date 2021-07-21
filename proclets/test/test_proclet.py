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

from proclets.mission import Control
from proclets.mission import Vehicle
from proclets.proclet import Proclet
from proclets.types import Termination


class MarkingTests(unittest.TestCase):

    class Parallel(Proclet):

        @property
        def net(self):
            return {
                self.pro_one: [self.pro_two, self.pro_three],
                self.pro_two: [self.pro_four],
                self.pro_three: [self.pro_five],
                self.pro_four: [self.pro_four, self.pro_five],
                self.pro_five: [self.pro_one],
            }

        def pro_one(self, this, **kwargs):
            # print("one")
            yield

        def pro_two(self, this, **kwargs):
            # print("two")
            yield

        def pro_three(self, this, **kwargs):
            # print("three")
            yield

        def pro_four(self, this, **kwargs):
            # print("four")
            yield

        def pro_five(self, this, **kwargs):
            # print("five")
            if self.tally[this.__name__] > 1:
                raise Termination()
            yield

    def test_fork(self):
        n = 0
        p = MarkingTests.Parallel.create()
        while True:
            n += 1
            try:
                list(p())
            except Termination:
                break

            with self.subTest(n=n, p=p):
                if p.pro_two in p.enabled:
                    self.assertIn(p.pro_three, p.enabled)
                if p.pro_three in p.enabled:
                    self.assertIn(p.pro_two, p.enabled)

    def test_join(self):
        n = 0
        p = MarkingTests.Parallel.create()
        while True:
            n += 1
            try:
                list(p())
            except Termination:
                break

            if p.pro_five in p.enabled:
                with self.subTest(n=n, p=p):
                    self.assertTrue(p.i_nodes[p.pro_five].issubset(p.marking))

    def test_loop(self):
        p = MarkingTests.Parallel.create()
        self.assertEqual({0}, p.o_nodes[p.pro_five])

        a = next(k for k, v in p.arcs.items() if v[0] == v[1])
        self.assertNotIn(a, p.i_nodes[p.pro_four])
        self.assertNotIn(a, p.o_nodes[p.pro_four])


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
