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

class DevPackage(Proclet):

    def __init__(self, contents, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.contents = contents
        self.delivery = None

    @property
    def dag(self):
        return {
            self.pro_split: [self.pro_load],
            #self.pro_load: [self.pro_retry, self.pro_deliver, self.pro_undeliver],
            self.pro_load: [self.pro_deliver],
            self.pro_deliver: [self.pro_bill, self.pro_finish],
            self.pro_retry: [self.pro_load, self.pro_finish],
            self.pro_undeliver: [self.pro_bill, self.pro_return, self.pro_finish],
            self.pro_return: [self.pro_bill],
            self.pro_bill: [self.pro_bill],
            self.pro_finish: [],
        }

    def pro_split(self, this, **kwargs):
        yield from self.channels["orders"].respond(
            self, this,
            actions={this.__name__: None},
        )
        yield

    def pro_load(self, this, **kwargs):
        if not self.delivery:
            d = Delivery.create(
                domain=self.domain,
                channels=self.channels,
                group={self.uid},
            )
            self.delivery = d.uid
            yield d

            yield from self.channels["logistics"].send(
                sender=self.uid, group=[self.delivery],
                action=this.__name__,
            )

        yield

    def pro_deliver(self, this, **kwargs):
        #print("pro_deliver", *self.channels["logistics"].store[self.uid], sep="\n")
        try:
            msg = next(self.channels["logistics"].respond(
                self, this,
                actions={this.__name__: None},
                contents={this.__name__: "Yup"},
            ))
        except (StopIteration, queue.Empty):
            return
        else:
            yield msg

    def pro_retry(self, this, **kwargs):
        try:
            msg = next(self.channels["logistics"].respond(
                self, this,
                actions={this.__name__: None},
                contents={this.__name__: "Yup"},
            ))
        except (StopIteration, queue.Empty):
            return
        else:
            yield msg

    def pro_undeliver(self, this, **kwargs):
        try:
            msg = next(self.channels["logistics"].respond(
                self, this,
                actions={this.__name__: None},
                contents={this.__name__: "Yup"},
            ))
        except (StopIteration, queue.Empty):
            return
        else:
            yield msg

    def pro_return(self, this, **kwargs):
        yield

    def pro_bill(self, this, **kwargs):
        yield

    def pro_finish(self, this, **kwargs):
        yield


class DeliveryTests(unittest.TestCase):

    @staticmethod
    def report(m):
        try:
            source = Proclet.population[m.sender]
            connect = getattr(m.connect, "hex", "")
            return f"{connect:>36}|{source.name:^20}|{m.action:<12}|{m.content or ''}"
        except AttributeError:
            return "{0}|{1}|Call Proclet|{2.name}".format(" "*36, " "*20, m)
        except TypeError:
            print(m, file=sys.stderr)
            raise

    def test_deliver(self):
        channels = {"orders": Channel(), "logistics": Channel()}
        # Create a Package proclet with pro_load enabled
        p = DevPackage.create([0], channels=channels, marking={1})
        self.assertEqual("DevPackage_001", p.name)

        # First run creates delivery
        self.assertEqual(0, len(p.domain))
        for n in range(12):
            with self.subTest(n=n):
                run = list(p())
                print(*[self.report(i) for i in run], sep="\n", file=sys.stderr)

                if not n:
                    self.assertEqual(1, len(p.domain))
                    self.assertIsInstance(p.domain[0], Delivery)
                    self.assertIsInstance(run[0], Delivery)
                    self.assertEqual(0, len(p.domain[0].retries))
                elif n == 1:
                    self.assertEqual(1, len(p.domain[0].retries))


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
