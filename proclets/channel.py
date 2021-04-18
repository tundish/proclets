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

from collections import Counter
from collections import defaultdict
from collections import deque
from dataclasses import dataclass
from dataclasses import field
import enum
import functools
import queue
import time
import uuid

from proclets.performative import Performative
from proclets.proclet import Proclet


class Channel:
    """
    Information is only available locally, hence synchronization can only
    occur at a channel.

    Describing behaviour of Processes with Many-to-Many Interactions.
    Fahland (2019)

    """
    def __init__(self):
        self.store = defaultdict(deque)
        self.ready = Counter()

    def qsize(self, uid):
        return self.ready[uid]

    def empty(self, uid):
        return self.ready[uid] == 0

    def full(self, uid):
        return False

    def put(self, item: Performative):
        n = 0
        if not item.group:
            return

        for uid in item.group:
            self.ready[uid] += 1
            self.store[uid].appendleft(item)
            n += 1
        return n

    def get(self, uid):
        if not self.ready[uid]:
            raise queue.Empty
        self.ready[uid] -= 1
        item = self.store[uid][self.ready[uid]]
        return item

    def send(self, **kwargs):
        kwargs["channel"] = kwargs.get("channel", self)
        item = Performative(**kwargs)
        sent = self.put(item)
        for i in range(sent):
            yield item

    def respond(self, p: Proclet, actions: dict, contents: dict=None):
        while not self.empty(p.uid):
            m = self.get(p.uid)
            action = actions.get(m.action)
            content = contents and contents.get(m.action) or p.marking
            if action:
                yield from self.send(
                    sender=p.uid, group=[m.sender],
                    action=action, content=content
                )
            elif m.action in actions:
                yield None
