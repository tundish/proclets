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

from proclets.performative import Performative
from proclets.performative import Proclet


class GroupTests(unittest.TestCase):
    """
    A performative has by definition one sender, but can have multiple recipients.
    The sender is always represented by a procid, i.e. the identifer of a proclet instance.
    However, the list of recipients can be a mixture of procid's and classid's, i.e. one can send performatives
    to both proclet instances and proclet classes.
    A performative sent to a proclet class is received by all proclet instances of that class
    """
    pass


class PerformativeTests(unittest.TestCase):

    @unittest.skip("Not yet")
    def test_performative(self):
        perf = Performative()
        self.fail(perf)


class ProcletTests(unittest.TestCase):

    class InOut(Proclet):

        def __init__(self, **kwargs):
            super().__init__(self.go_in, self.go_out, **kwargs)

        def go_in(self, state):
            yield Performative()

        def go_out(self, state):
            yield Performative()

    @unittest.skip("Not yet")
    def test_proclet(self):
        # TODO: Russian roulette example?
        p = ProcletTests.InOut()
        self.fail(list(p()))
