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

from proclets.mission import Control
from proclets.mission import Recovery
from proclets.mission import Vehicle
from proclets.mission import mission
from proclets.types import Termination


class MissionTests(unittest.TestCase):

    def setUp(self):
        self.procs = mission()

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

    def test_flow(self):
        for n, p, m in self.run_to_terminate(self.procs):
            print(n, p, p.marking)

    def test_vehicles(self):

        objs = set(self.procs).union({d for p in self.procs for d in p.domain})
        control = next(i for i in objs if isinstance(i, Control))

        for n, v in enumerate(i for i in objs if isinstance(i, Vehicle)):
            with self.subTest(v=v):
                self.assertEqual(1, v.tally["pro_separation"], v.tally)
        self.assertEqual(1, n)
        recoveries = [i for i in objs if isinstance(i, Recovery)]
        self.assertEqual(2, len(recoveries))
