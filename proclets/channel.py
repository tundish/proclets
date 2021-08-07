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
import itertools
import operator
import queue
import time
import uuid

from proclets.proclet import Proclet
from proclets.types import Performative


class Channel:
    """
    Channels provide a service somewhat like an email client; they deliver
    Performative_ s to an inbox corresponding to the `uid`
    of the Proclet recipient.

    These messages can be retrieved one at a time, after the manner of a queue.
    There are also higher-level methods which allow Proclets to process messages in batches.

    By default, messages are only delivered once. However, each Proclet transition may
    independently access the channel; to do that, pass `this` to the `party` parameter
    of the channel method.


    """
    def __init__(self, maxlen=None):
        self.store = defaultdict(functools.partial(deque, maxlen=maxlen))
        self.ready = defaultdict(Counter)

    def qsize(self, uid: uuid.UUID, party=None) -> int:
        """
        Return the number of items in the channel.

        """
        if party not in self.ready[uid]:
            self.ready[uid][party] = len(self.store[uid])
        return self.ready[uid][party]

    def empty(self, uid: uuid.UUID, party=None) -> bool:
        """
        Return True if the channel is empty, False otherwise.

        """
        return self.qsize(uid, party=party) == 0

    def full(self, uid: uuid.UUID, party=None):
        return False

    def put(self, item: Performative):
        n = 0
        if not item.group:
            return

        for uid in item.group:
            for party in self.ready[uid] or [None]:
                self.ready[uid][party] += 1
            self.store[uid].append(item)
            n += 1
        return n

    def get(self, uid: uuid.UUID, party=None):
        if self.empty(uid, party=party):
            raise queue.Empty

        item = self.store[uid][-self.ready[uid][party]]
        self.ready[uid][party] -= 1
        return item

    def send(self, **kwargs):
        """
        Submit a message for delivery.

        :param sender:  Uid of the sender.
        :param group:   Contains uids of intended recipients.
        :type  sender:  uuid.UUID
        :type  group:   list

        All keyword arguments are those of a Performative_.

        """
        kwargs["channel"] = kwargs.get("channel", self)
        msg = Performative(**kwargs)
        msg.connect = msg.connect or msg.uid
        sent = self.put(msg)
        for i in range(sent or 0):
            yield msg

    def receive(self, p: Proclet, party=None) -> Performative:
        """
        Yield all undelivered messages intended for the Proclet.

        """
        while not self.empty(p.uid, party):
            yield self.get(p.uid, party)

    def reply(self, p: Proclet, m: Performative, **kwargs) -> Performative:
        """
        Proclet `p` having received a message `m`; use it to craft a reply to its sender.
        This method preserves `context` and `connection` of messages.
        Keyword arguments are those of a Performative_.

        """
        msg = Performative(**dict(
            kwargs, sender=p.uid, group={m.sender},
            channel=m.channel, connect=m.connect, context=m.context,
        ))
        if self.put(msg):
            return msg

    def respond(
        self, p: Proclet, party=None,
        actions: dict=None, contents: dict=None, context: set=None,
        ) -> Performative:
        """
        Process undelivered messages for `p` as a batch.
        Yields each generated reply as a Performative_.

        :param actions:     Maps incoming message actions to a corresponding action in the generated reply.
        :param contents:    Maps incoming message actions to corresponding content in the generated reply.
        :param context:     If supplied, add extra context to the reply.
        :type actions:      dict
        :type contents:     dict
        :type context:      set

        """
        while not self.empty(p.uid, party):
            m = self.get(p.uid, party)
            yield m
            action = actions and actions.get(m.action)
            content = contents and contents.get(m.action)
            context = m.context and m.context.copy().union(context or set())
            if action is not None:
                yield from self.send(
                    sender=p.uid, group={m.sender},
                    action=action, content=content,
                    connect=m.connect or m.uid,
                    context=context
                )
            elif m.action in actions:
                yield None

    def view(self, uid: uuid.UUID):
        """
        Scan the entire Channel for messages sent and received by the Proclet with `uid`.

        Returns an dictionary containing sequences of messages having the same `connect`
        ids. The items in each sequence are the connected messages in the order
        they were generated.

        """
        msgs = sorted(itertools.chain.from_iterable(self.store.values()), key=operator.attrgetter("ts"))
        rv = defaultdict(list)
        for m in msgs:
            if m.sender == uid or uid in m.group:
                rv[m.connect].append(m)
        return rv

