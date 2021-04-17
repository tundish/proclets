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

from proclets.performative import Performative


class Proclet:
    """
    A Proclet instance is a callable object with a finite lifetime.

    Proclets: A framework for lightweight interacting workdag processes.
    Van der Aalst, Barthelmess, Ellis, Wainer (2001)

    """

    groups = defaultdict(ChainMap)

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
        self, *args, uid=None, channels=None, group=None, marking=None
    ):
        self.uid = uid or uuid.uuid4()
        self.channels = channels or {}
        self.group = group or set()
        self.arcs = dict(self.build_arcs(self.dag))
        self.marking = marking or {0}
        self.pending = {self.uid: self}

    def __call__(self, **kwargs):
        for proc in list(self.pending.values()):
            if proc is not self:
                yield from proc(**kwargs)
                continue

            marking = set()
            for fn in proc.dag:
                i_nodes = proc.i_nodes[fn]
                if i_nodes.issubset(proc.marking):
                    results = []
                    while not results or any(
                        i.uid in self.pending for i in filter(None, results)
                    ):
                        results = list(fn(**kwargs))

                    for obj in results:
                        if obj is None:
                            # Transition complete
                            proc.marking -= i_nodes
                            marking.update(proc.o_nodes[fn])
                            continue
                        elif isinstance(obj, Proclet):
                            self.pending[obj.uid] = obj
                            yield obj
                        elif isinstance(obj, Performative):
                            try:
                                obj.channel.put(obj)
                            except (AttributeError,):
                                pass
                            finally:
                                yield obj

            proc.marking = marking

    @property
    def dag(self):
        return {}

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
