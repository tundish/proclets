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
import unittest

from proclets.example import Order
from proclets.example import Package
from proclets.example import Delivery
from proclets.example import Back
from proclets.example import Product
from proclets.performative import Performative

class ExampleTests(unittest.TestCase):

    def test_arcs(self):
        arcs = Order().arcs
        transitions = Order().transitions
        print(transitions)
        places = Order().places
        print(places)
        self.assertEqual(4, len(arcs), arcs)

        arcs = Package().arcs
        self.assertEqual(8, len(arcs), arcs)

        arcs = Delivery().arcs
        self.assertEqual(6, len(arcs), arcs)

        arcs = Back().arcs
        self.assertEqual(3, len(arcs), arcs)

    def test_order(self):
        order = Order(*list(Product))
        self.assertEqual(3, len(order.args))
        self.assertFalse(order.items)
        rv = list(order())
        self.assertTrue(rv)
        self.assertTrue(
            all(isinstance(i, Performative) for i in rv if i is not None)
        )
        self.assertTrue(order.items)
