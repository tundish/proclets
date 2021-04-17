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
import functools
import queue
import time
import uuid


@dataclass(order=True)
class Performative:

    ts:         int = field(default_factory=time.monotonic_ns)
    uid:        uuid.UUID = field(default_factory=uuid.uuid4)
    channel:    uuid.UUID = None
    sender:     uuid.UUID = None
    group:      list[uuid.UUID] = None
    action:     enum.Enum = None
    content:    str = None


class Channel:
    """
    Information is only available locally, hence synchronization can only occur at a channel.

    Describing behaviour of Processes with Many-to-Many Interactions.
    Fahland (2019)

    """
    def __init__(self):
        self.q = defaultdict(queue.PriorityQueue)
