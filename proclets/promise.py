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
from collections import Counter
from collections import defaultdict
from collections import deque
from collections import namedtuple
import enum
import functools
import logging
import random
import sys
import uuid

from proclets.channel import Channel
from proclets.proclet import Proclet
from proclets.types import Init
from proclets.types import Exit
from proclets.types import Termination


class Promise(Proclet):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.log = logging.getLogger(self.name)
        self.actions = {}
        self.contents = defaultdict(dict)
        self.fruition = defaultdict(functools.partial(Fruition, 1))
        self.requests = defaultdict(deque)

    @property
    def result(self):
        mappings = [
            next(
                (Attribution(m.content, ts=m.ts, uid=m.sender) for m in reversed(v) if m.action == Exit.deliver),
                Attribution()
            )
            for c in self.channels.values()
            for v in c.view(self.uid).values()
        ]
        return ChainMap(*reversed(list(filter(None, mappings))))

    @property
    def pending(self):
        return [
            j for j, v in self.fruition.items() if v.value not in (5, 7, 8, 9)
        ]

    @property
    def effort(self):
        return Counter(k for m in self.result.maps for k in m)

    def dispatched(self, job, *args):
        args = args or Proclet
        return [p for p in self.domain if isinstance(p, args) and job in p.requests]

    def pro_init(self, this, **kwargs):
        for c in self.channels.values():
            for n, m in enumerate(
                c.respond(self, this, actions=self.actions, contents=self.contents)
            ):
                self.contents[m.action] = m.content or self.contents[Init.request]
                job = tuple(self.contents[m.action].items())
                self.fruition[job] = self.fruition[job].trigger(m.action)

                if m.action == Init.request:
                    self.requests[job].append(m)
                yield m

        if all(i == Fruition.construction for i in self.fruition.values()):
            self.log.debug(self.requests, extra={"proclet": self})
            yield

    def pro_exit(self, this, **kwargs):
        for j, v in self.requests.items():
            for m in v:
                r = m.channel.reply(
                    self, m, action=Exit.deliver, content=dict(j)
                )
                self.fruition[j] = self.fruition[j].trigger(r.action)
                yield r

        self.log.debug(self.fruition, extra={"proclet": self})
        yield
