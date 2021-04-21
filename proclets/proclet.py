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
from dataclasses import dataclass
from dataclasses import field
import enum
import functools
import queue
import time
import uuid


class Proclet:
    """
    A Proclet instance is a callable object with a finite lifetime.

    Proclets: A framework for lightweight interacting workflow processes.
    Van der Aalst, Barthelmess, Ellis, Wainer (2001)

    """

    @staticmethod
    def build_arcs(dag):
        rv = defaultdict(set)
        n = 0
        for k, v in dag.items():
            if not n:
                yield (n, (None, k))
            for i in v:
                n += 1
                yield n, (k, i)

    def __init__(
        self, name, *args,
        uid=None, channels=None, group=None,
        marking=None, slate=None, tally=None,
    ):
        self.uid = uid or uuid.uuid4()
        self.name = name or self.uid
        self.channels = channels or {}
        self.group = group or set()
        self.arcs = dict(self.build_arcs(self.dag))
        self.marking = marking or {0}
        self.slate = slate or Counter()
        self.tally = tally or Counter()
        self.pending = {self.uid: self}

    def __call__(self, **kwargs):
        for proc in list(self.pending.values()):
            if proc is not self:
                yield from proc(**kwargs)
                continue

            n = 1
            marking = set()
            try:
                fn = next(fn for fn in proc.activated)
            except StopIteration:
                return

            for obj in fn(fn, **kwargs):
                if obj is None:
                    # Transition is complete
                    proc.marking -= proc.i_nodes[fn]
                    proc.marking.update(proc.o_nodes[fn])
                    n = self.slate[fn] = 0
                elif isinstance(obj, Proclet):
                    # Transition spawns a new Proclet
                    self.pending[obj.uid] = obj
                    yield obj
                else:
                    yield obj
            self.slate[fn] += n
            self.tally[fn] += 1

    @property
    def dag(self):
        return {}

    @property
    def activated(self):
        return [self.arcs[i][1] for i in sorted(self.marking)]

    @functools.cached_property
    def i_nodes(self):
        rv = defaultdict(set)
        for p, (s, d) in self.arcs.items():
            rv[d].add(p)
        return rv

    @functools.cached_property
    def o_nodes(self):
        rv = defaultdict(set)
        for p, (s, d) in self.arcs.items():
            rv[s].add(p)
        return rv
