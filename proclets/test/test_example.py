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

from proclets.channel import Channel
from proclets.example import Order
from proclets.example import Package
from proclets.example import Delivery
from proclets.example import Back
from proclets.example import Product
from proclets.proclet import Proclet
from proclets.types import Performative

class DevPackage(Proclet):

    def __init__(self, name, contents, *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    @property
    def dag(self):
        return {
            self.pro_split: [self.pro_load],
            self.pro_load: [], #[self.pro_retry, self.pro_deliver, self.pro_undeliver],
            #self.pro_retry: [self.pro_load, self.pro_finish],
            #self.pro_deliver: [self.pro_bill, self.pro_finish],
            #self.pro_undeliver: [self.pro_bill, self.pro_return, self.pro_finish],
            #self.pro_return: [self.pro_bill],
            #self.pro_bill: [self.pro_bill],
            #self.pro_finish: [],
        }

    def pro_split(self, this, **kwargs):
        yield from self.channels["orders"].respond(
            self, this,
            actions={Init.request: Init.promise},
            contents={Init.request: self.contents},
        )
        yield

    def pro_load(self, this, **kwargs):
        yield Delivery.create(
            channels=self.channels,
            group=self.group.copy(),
        )
        return
        if not self.delivery:
            rv = Delivery("Delivery", channels=self.channels)
            self.delivery[rv.uid] = rv
            yield rv

        if not self.channels["logistics"].store[self.uid]:
            yield from self.channels["logistics"].send(
                sender=self.uid, group=[next(iter(self.delivery.keys()))], connect=self.uid,
                action=Init.request, context={i.uid for i in self.contents}, content=self.contents
            )
        yield


class DeliveryTests(unittest.TestCase):

    def test_deliver(self):
        channels = {"orders": Channel(), "logistics": Channel()}
        # Create a Package proclet with pro_load enabled
        p = DevPackage.create([], channels=channels, marking={1})
        self.assertEqual("DevPackage_001", p.name)

        # First run creates delivery
        self.assertEqual(1, len(p.pending))
        run = list(p())
        self.assertEqual(2, len(p.pending))
        self.assertIsInstance(next(reversed(p.pending.values())), Delivery)
        self.assertIsInstance(run[0], Delivery)

        # Second run syncs on pro_load
        run = list(p())
        print(run)

class ExampleTests(unittest.TestCase):

    def test_dag(self):
        dag = Order(None, []).dag
        arcs = Order(None, []).arcs
        i_nodes = Order(None, []).i_nodes
        self.assertEqual(4, len(dag), dag)

        dag = Package(None, []).dag
        self.assertEqual(8, len(dag), dag)

        dag = Delivery(None, []).dag
        self.assertEqual(6, len(dag), dag)

        dag = Back(None, []).dag
        self.assertEqual(3, len(dag), dag)
