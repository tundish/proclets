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
import sys

from proclets.channel import Channel
from proclets.proclet import Proclet
from proclets.types import Performative


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
            self.pro_create: [self.pro_split],
            self.pro_split: [self.pro_notify],
            self.pro_notify: [self.pro_bill],
            self.pro_bill: [],
        }

    def pro_create(self, this, **kwargs):
        self.items = {Item(p, q) for p, q in self.args.items()}
        self.channels["down"] = Channel()
        yield

    def pro_split(self, this, **kwargs):
        # Create one Package proclet for each ordered Item.
        # Declare them as a single Channel Group
        self.group = {
            item: Package(name=n, channels={"up": self.channels["down"]})
            for n, item in enumerate(self.items)
        }
        for item, p in self.group.items():
            yield p

            # Activate the initial transition
            yield Performative(
                channel=p.channels["up"], sender=self.uid, group=[p.uid],
                content=item
            )

    def pro_notify(self, this, **kwargs):
        yield Performative()

    def pro_bill(self, this, **kwargs):
        yield Performative()


class Package(Proclet):

    @property
    def dag(self):
        return {
            self.pro_split: [self.pro_load],
            self.pro_load: [self.pro_retry, self.pro_deliver, self.pro_undeliver],
            self.pro_retry: [self.pro_load, self.pro_finish],
            self.pro_deliver: [self.pro_bill, self.pro_finish],
            self.pro_undeliver: [self.pro_bill, self.pro_return, self.pro_finish],
            self.pro_return: [self.pro_bill],
            self.pro_bill: [self.pro_bill],
            self.pro_finish: [],
        }

    def pro_split(self, this, **kwargs):
        yield

    def pro_load(self, this, **kwargs):
        yield

    def pro_retry(self, this, **kwargs):
        yield

    def pro_deliver(self, this, **kwargs):
        yield

    def pro_undeliver(self, this, **kwargs):
        yield

    def pro_return(self, this, **kwargs):
        yield

    def pro_bill(self, this, **kwargs):
        yield

    def pro_finish(self, this, **kwargs):
        yield


class Delivery(Proclet): pass
class Back(Proclet): pass

if __name__ == "__main__":
    order = Order(*list(Product))
    while True:
        print(*list(order()), sep="\n", file=sys.stderr)
