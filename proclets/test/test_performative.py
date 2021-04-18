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

import queue
import unittest

from proclets.channel import Channel
from proclets.performative import Performative


class PerformativeTests(unittest.TestCase):

    @unittest.skip("Not yet")
    def test_performative(self):
        perf = Performative()
        self.fail(perf)


class ChannelTests(unittest.TestCase):

    def test_api(self):
        c = Channel()
        self.assertTrue(c.empty(0))
        self.assertFalse(c.full(0))
        self.assertRaises(queue.Empty, c.get, 0)

    def test_put_plain_object(self):
        c = Channel()
        self.assertRaises(AttributeError, c.put, 0)

    def test_put_empty_group(self):
        c = Channel()
        p = Performative(group=[])
        self.assertIsNone(c.put(p))

    def test_put_one_in_group(self):
        c = Channel()
        p = Performative(group=[0])
        self.assertEqual(1, c.put(p))
        self.assertFalse(c.empty(0))

    def test_put_many(self):
        c = Channel()
        group = list(range(6))
        p = Performative(group=group)
        self.assertEqual(6, c.put(p))
        for i in group:
            with self.subTest(i=i):
                self.assertFalse(c.empty(i))

    def test_get_one(self):
        c = Channel()
        p = Performative(group=[0])
        self.assertEqual(1, c.put(p))
        self.assertFalse(c.empty(0))
        rv = c.get(0)
        self.assertEqual(p, rv)
        self.assertTrue(c.empty(0))

    def test_get_many(self):
        c = Channel()
        data = [Performative(group=[0])] * 6
        for p in data:
            c.put(p)

        for n, p in enumerate(data):
            with self.subTest(n=n, p=p):
                self.assertFalse(c.empty(0))
                self.assertEqual(p, c.get(0))
        self.assertTrue(c.empty(0))
