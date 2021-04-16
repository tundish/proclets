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
from collections import Counter
from dataclasses import dataclass
from dataclasses import field
import unittest
import uuid

from proclets.performative import Performative
from proclets.performative import Proclet


class Product(enum.Enum):
    apple = enum.auto()
    brush = enum.auto()
    cloth = enum.auto()

@dataclass(frozen=True)
class Item:

    uid: uuid.UUID = field(default_factory=uuid.uuid4)
    product: Product = None
    quantity: int = 0

class Order(Proclet):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.args = Counter(args)
        self.items = set()

    @property
    def dag(self):
        return {
            self.create: [self.split],
            self.split: [self.notify],
            self.notify: [self.bill],
            self.bill: [],
        }

    def create(self, **kwargs):
        # Create one synchronous channel ?
        self.items = {Item(p, q) for p, q in self.args.items()}
        yield

    def split(self, **kwargs):
        # Create one Package proclet for each ordered Item.
        # Declare them as a Channel Group
        # Activate their initial transition
        yield Performative()

    def notify(self, **kwargs):
        yield Performative()

    def bill(self, **kwargs):
        yield Performative()

class Package(Proclet): pass
class Delivery(Proclet): pass
class Back(Proclet): pass
