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

from proclets.proclet import Proclet
from proclets.types import Performative


class Channel:
    """
    Information is only available locally, hence synchronization can only
    occur at a channel.

    Describing behaviour of Processes with Many-to-Many Interactions.
    Fahland (2019)

    """
    def __init__(self, maxlen=None):
        self.store = defaultdict(functools.partial(deque, maxlen=maxlen))
        self.ready = defaultdict(Counter)

    def qsize(self, uid, party=None) -> int:
        """
        Return the number of items in the channel.

        """
        if party not in self.ready[uid]:
            self.ready[uid][party] = len(self.store[uid])
        return self.ready[uid][party]

    def empty(self, uid, party=None) -> bool:
        """
        Return True if the channel is empty, False otherwise.

        """
        return self.qsize(uid, party=party) == 0

    def full(self, uid, party=None):
        return False

    def put(self, item: Performative):
        n = 0
        if not item.group:
            return

        for uid in item.group:
            for party in self.ready[uid] or [None]:
                self.ready[uid][party] += 1
            self.store[uid].appendleft(item)
            n += 1
        return n

    def get(self, uid, party=None):
        if self.empty(uid, party=party):
            raise queue.Empty

        self.ready[uid][party] -= 1
        item = self.store[uid][self.ready[uid][party]]
        return item

    def send(self, **kwargs):
        kwargs["channel"] = kwargs.get("channel", self)
        item = Performative(**kwargs)
        sent = self.put(item)
        for i in range(sent):
            yield item

    def receive(self, p: Proclet, party=None):
        while not self.empty(p.uid, party):
            yield self.get(p.uid, party)

    def respond(
        self, p: Proclet, party=None,
        actions: dict=None, contents: dict=None, context: set=None,
        ):
        while not self.empty(p.uid, party):
            m = self.get(p.uid, party)
            action = actions and actions.get(m.action)
            content = contents and contents.get(m.action) or p.marking
            context = m.context and m.context.copy().union(context or set())
            if action is not None:
                yield from self.send(
                    sender=p.uid, group=[m.sender],
                    action=action, content=content,
                    connect=m.connect or m.uid,
                    context=context
                )
            elif m.action in actions:
                yield action
