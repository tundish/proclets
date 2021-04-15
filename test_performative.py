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

from collections import ChainMap
from collections import defaultdict
from dataclasses import dataclass
from dataclasses import field
import enum
import time
import uuid

import unittest

@dataclass
class Performative:

    ts:         int = field(default_factory=time.monotonic_ns)
    uid:        uuid.UUID = field(default_factory=uuid.uuid4)
    channel:    uuid.UUID = None
    sender:     uuid.UUID = None
    group:      list[uuid.UUID] = None
    action:     enum.Enum = None
    content:    str = None

"""
Time: the moment the performative was created/received.(2)Channel: the medium used to exchange the performative.(3)Sender: the identi er of the proclet creating the performative.(4)Set  of  receivers: the identi ers of the proclets receiving the performative, i.e. alist of recipients.(5)Action: the type of the performative.(6)Content: the actual information that is being exchanged.
"""

"""
    Describing behaviour of Processes with Many-to-Many Interactions.
    Fahland (2019)

"""
class Proclet:
    """
    A Proclet instance is a callable object with a finite lifetime.

    Proclets: A framework for lightweight interacting workflow processes.
    Van der Aalst, Barthelmess, Ellis, Wainer (2001)

    """

    groups = defaultdict(ChainMap)

    def __init__(self, id=None):
        self.uid = uid or uuid.uuid4()

class GroupTests(unittest.TestCase):
    """
    A performative has by definition one sender, but can have multiple recipients.
    The sender is always represented by a procid, i.e. the identifer of a proclet instance.
    However, the list of recipients can be a mixture of procid's and classid's, i.e. one can send performatives
    to both proclet instances and proclet classes.
    A performative sent to a proclet class is received by all proclet instances of that class
    """
    pass

class ProcletTests(unittest.TestCase):

    def test_performative(self):
        perf = Performative()
        self.fail(perf)
