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

class ExampleTests(unittest.TestCase):

    def setUp(self):
        self.proclets = {
            i.__class__.__name__.lower(): i for i in (
                Order(), Package(), Delivery(), Back()
            )
        }

    def test_simple(self):
        print(self.proclets)
