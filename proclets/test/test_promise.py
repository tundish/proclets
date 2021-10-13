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

import unittest

from proclets.types import Init
from proclets.types import Exit
from proclets.types import Fruition


class FruitionTests(unittest.TestCase):

    def test_inception(self):
        state = Fruition.inception
        self.assertEqual(state, state.trigger())
        for i in Init:
            with self.subTest(state=state, i=i):
                if i == Init.request:
                    self.assertEqual(Fruition.elaboration, state.trigger(Init.request))
                else:
                    self.assertEqual(state, state.trigger(i))

    def test_elaboration(self):
        state = Fruition.elaboration
        for i in Init:
            with self.subTest(state=state, i=i):
                if i == Init.promise:
                    self.assertEqual(Fruition.construction, state.trigger(i))
                elif i in (Init.abandon, Init.decline):
                    self.assertEqual(Fruition.withdrawn, state.trigger(i))
                elif i == Init.counter:
                    self.assertEqual(Fruition.discussion, state.trigger(i))
                else:
                    self.assertEqual(state, state.trigger(i))

    def test_discussion(self):
        state = Fruition.discussion
        for i in Init:
            with self.subTest(state=state, i=i):
                if i == Init.counter:
                    self.assertEqual(Fruition.elaboration, state.trigger(i))
                elif i in (Init.abandon, Init.decline):
                    self.assertEqual(Fruition.withdrawn, state.trigger(i))
                elif i in (Init.confirm, Init.promise):
                    self.assertEqual(Fruition.construction, state.trigger(i))
                else:
                    self.assertEqual(state, state.trigger(i))

    def test_construction(self):
        state = Fruition.construction
        for i in Exit:
            with self.subTest(state=state, i=i):
                if i == Exit.deliver:
                    self.assertEqual(Fruition.transition, state.trigger(i))
                elif i == Exit.decline:
                    self.assertEqual(Fruition.defaulted, state.trigger(i))
                elif i == Exit.abandon:
                    self.assertEqual(Fruition.cancelled, state.trigger(i))
                else:
                    self.assertEqual(state, state.trigger(i))

    def test_transition(self):
        state = Fruition.transition
        for i in Exit:
            with self.subTest(state=state, i=i):
                if i == Exit.decline:
                    self.assertEqual(Fruition.construction, state.trigger(i))
                elif i == Exit.abandon:
                    self.assertEqual(Fruition.cancelled, state.trigger(i))
                elif i == Exit.confirm:
                    self.assertEqual(Fruition.completion, state.trigger(i))
                else:
                    self.assertEqual(state, state.trigger(i))

    def test_terminal(self):
        for state in (
            Fruition.withdrawn, Fruition.defaulted, Fruition.cancelled, Fruition.completion
        ):
            for i in list(Init) + list(Exit):
                with self.subTest(state=state, i=i):
                    self.assertEqual(state, state.trigger(i))
