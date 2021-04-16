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

from proclets.performative import Performative
from proclets.performative import Proclet


class Order(Proclet):

    def create(self, state):
        yield Performative()

    def split(self, state):
        yield Performative()

    def notify(self, state):
        yield Performative()

    def bill(self, state):
        yield Performative()

class Package(Proclet): pass
class Delivery(Proclet): pass
class Back(Proclet): pass
