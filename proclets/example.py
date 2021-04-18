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

from proclets.channel import Channel
from proclets.performative import Performative
from proclets.proclet import Proclet


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
        self.items = {Item(p, q) for p, q in self.args.items()}
        self.channels["down"] = Channel()
        yield

    def split(self, **kwargs):
        # Create one Package proclet for each ordered Item.
        # Declare them as a single Channel Group
        self.group = {
            item: Package(channels={"up": self.channels["down"]})
            for item in self.items
        }
        for item, p in self.group.items():
            yield p

            # Activate the initial transition
            yield Performative(
                channel=p.channels["up"], sender=self.uid, group=[p.uid],
                content=item
            )

    def notify(self, **kwargs):
        yield Performative()

    def bill(self, **kwargs):
        yield Performative()


class Package(Proclet):

    @property
    def dag(self):
        return {
            self.split: [self.load],
            self.load: [self.retry, self.deliver, self.undeliver],
            self.retry: [self.load, self.finish],
            self.deliver: [self.bill, self.finish],
            self.undeliver: [self.bill, self.return_, self.finish],
            self.return_: [self.bill],
            self.bill: [self.bill],
            self.finish: [],
        }

    def split(self, **kwargs):
        yield

    def load(self, **kwargs):
        yield

    def retry(self, **kwargs):
        yield

    def deliver(self, **kwargs):
        yield

    def undeliver(self, **kwargs):
        yield

    def return_(self, **kwargs):
        yield

    def bill(self, **kwargs):
        yield

    def finish(self, **kwargs):
        yield


class Delivery(Proclet): pass
class Back(Proclet): pass
