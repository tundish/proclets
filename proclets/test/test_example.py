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

class ExampleTests(unittest.TestCase):

    def test_flow(self):
        flow = Order().flow
        self.assertEqual(4, len(flow), flow)

        flow = Package().flow
        self.assertEqual(8, len(flow), flow)

        flow = Delivery().flow
        self.assertEqual(6, len(flow), flow)

        flow = Back().flow
        self.assertEqual(3, len(flow), flow)

    def test_order(self):
        order = Order(*list(Product))
        self.assertEqual(3, len(order.products))
