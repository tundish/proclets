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

import itertools
import queue
from types import SimpleNamespace as SN
import unittest
import uuid

from proclets.channel import Channel
from proclets.types import Init
from proclets.types import Exit
from proclets.types import Performative


class ChannelTests(unittest.TestCase):

    def test_api(self):
        c = Channel()
        self.assertTrue(c.empty(0))
        self.assertTrue(c.empty(0, party=1))
        self.assertFalse(c.full(0))
        self.assertFalse(c.full(0, party=1))
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

        rv = c.get(0, party=1)
        self.assertEqual(p, rv)
        self.assertTrue(c.empty(0, party=1))

    def test_get_many(self):
        c = Channel()
        data = [Performative(group=[0])] * 6
        for p in data:
            c.put(p)

        for n, p in enumerate(data):
            with self.subTest(n=n, p=p):
                self.assertFalse(c.empty(0))
                self.assertFalse(c.empty(0, party=1), c.ready)
                self.assertEqual(p, c.get(0))
                self.assertEqual(p, c.get(0, party=1))

        self.assertTrue(c.empty(0))
        self.assertTrue(c.empty(0, party=1))
        self.assertFalse(c.empty(0, party=2))

    def test_send_one(self):
        c = Channel()

        rv = next(c.send(group=[0]))
        self.assertIsInstance(rv, Performative)
        self.assertIsInstance(rv.uid, uuid.UUID)
        self.assertEqual(rv.uid, rv.connect)

    def test_view(self):
        c = Channel()
        p = SN(uid=uuid.uuid4())
        q = SN(uid=uuid.uuid4())
        r = SN(uid=uuid.uuid4())
        init = None

        for n, a in zip(range(8), itertools.cycle(
            (Init.request, Init.promise, Exit.deliver, Init.request, Init.promise, Exit.abandon)
        )):
            with self.subTest(n=n, a=a):
                if a == Init.request:
                    init = next(c.send(sender=q.uid, group={p.uid}, action=a))
                    lost = next(c.send(sender=q.uid, group={r.uid}, action=a))
                elif a == Init.promise:
                    rv = list(c.respond(p, actions={Init.request: a}))
                    self.assertEqual(2, len(rv))
                    self.assertEqual(init, rv[0])
                    self.assertEqual(p.uid, rv[1].sender)
                    self.assertEqual({q.uid}, rv[1].group)
                    self.assertEqual(init.connect, rv[1].connect)
                else:
                    rv = c.reply(p, init, action=a)
                    self.assertIsInstance(rv, Performative)
                    self.assertEqual(p.uid, rv.sender)
                    self.assertEqual({q.uid}, rv.group)
                    self.assertEqual(init.connect, rv.connect)

                v = list(c.view(p.uid).values())
                self.assertFalse(
                    any(m for i in v for m in i if r.uid in m.group)
                )
                if n == 2:
                    self.assertEqual(1, len(v))
                    self.assertEqual(3, len(v[0]))
                    self.assertEqual(Exit.deliver, v[0][-1].action, v[0])
                elif n == 5:
                    self.assertEqual(2, len(v))
                    self.assertEqual(3, len(v[1]))
                    self.assertEqual(Exit.abandon, v[1][-1].action, v[1])

