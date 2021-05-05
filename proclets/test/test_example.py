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
import queue
import unittest
import sys

from proclets.channel import Channel
from proclets.example import Order
from proclets.example import Package
from proclets.example import Delivery
from proclets.example import Back
from proclets.example import Product
from proclets.proclet import Proclet
from proclets.types import Performative


class DeliveryTests(unittest.TestCase):

    @staticmethod
    def report(m):
        try:
            source = Proclet.population[m.sender]
            connect = getattr(m.connect, "hex", "")
            return f"{connect:>36}|{source.name:^20}|{m.action:<14}|{m.content or ''}"
        except AttributeError:
            return "{0}|{1}|Call Proclet  |{2.name}".format(" "*36, " "*20, m)
        except TypeError:
            print(m, file=sys.stderr)
            raise

    def test_deliver(self):
        channels = {"orders": Channel(), "logistics": Channel()}
        # Create Package proclets with pro_load enabled
        jobs = [
            Package.create([], luck=0, channels=channels, marking={1}),
            Package.create([], luck=1, channels=channels, marking={1})
        ]

        for n in range(32):
            for p in jobs:
                with self.subTest(n=n, p=p):
                    if not n:
                        self.assertEqual(0, len(p.domain))

                    run = list(p())
                    for r in run:
                        print(self.report(r), file=sys.stderr)

                    if not n:
                        self.assertEqual(1, len(p.domain))
                        self.assertIsInstance(p.domain[0], Delivery)
                        self.assertIsInstance(run[0], Delivery)
                        self.assertEqual(0, len(p.domain[0].retries))

        for p in jobs:
            with self.subTest(p=p):
                self.assertIn("pro_bill", p.tally)
                self.assertEqual(1, p.tally["pro_bill"])


class ExampleTests(unittest.TestCase):

    def test_dag(self):
        dag = Order(None, []).dag
        arcs = Order(None, []).arcs
        i_nodes = Order(None, []).i_nodes
        self.assertEqual(4, len(dag), dag)

        dag = Package(None, []).dag
        self.assertEqual(7, len(dag), dag)

        dag = Delivery(None, []).dag
        self.assertEqual(6, len(dag), dag)

        dag = Back(None, []).dag
        self.assertEqual(3, len(dag), dag)
