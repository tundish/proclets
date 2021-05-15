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
import functools
import uuid
import weakref


class Proclet:
    """
    Proclets are callable objects which generate (yield) other objects.

    To use Proclets, first define a subclass::

        class MyProc(Proclet):

            ...

    Add behaviour in one or more transition methods::

        def pro_one(self, this, **kwargs):
            ...

        def pro_two(self, this, **kwargs):
            ...

    Publish the workflow net as a directed graph::

        @property
        def dag(self):
            return {
                self.pro_one: [self.pro_two],
                self.pro_two: []
            }

    Use the :meth:`~proclets.proclet.Proclet.create` method to build one::

        p = MyProc.create()

    When you call the proclet, those transition methods will be activated in the order
    defined by the :attr:`DAG<~proclets.proclet.Proclet.dag>`. When a transition method
    yields `None`, then operation flows on to the next.

    :class:`~proclets.types.Termination`.

    So this is sufficient::

        while True:
            for msg in p():
                print(msg)

    """

    population = weakref.WeakValueDictionary()
    """
    This class attribute dictionary stores every created Proclet instance by its unique `uid`.

    """

    @classmethod
    def create(cls, *args, fmt="{cls.__name__}_{0:03}", **kwargs):
        """
        This is the class factory method by which to create all Proclet objects.

        New proclets are registered with the class :attr:`~proclets.proclet.Proclet.population`
        so they can be retrieved by unique `uid`.

        Keyword arguments may be any of the following (all are optional):

        :param uid:     A unique identifier for the object. Generated if not supplied.
        :param name:    A human-readable name for the object.
                        If not supplied, len(:attr:`~proclets.proclet.Proclet.population`) is
                        passed to the format string `fmt` to generate one.
        :param channels:    A dictionary of named :class:`~proclets.channel.Channel` objects.
        :param group:   Contains the `uid` s of other Proclets to communicate with.
        :param marking: An initial marking to enable Proclet transitions declared in the
                        :attr:`DAG<~proclets.proclet.Proclet.dag>`.
        :param slate:   Counts the times a transition (by name) has blocked.
        :param tally:   Counts the times a transition (by name) has been enabled.
        :type uid: uuid.UUID
        :type name: str
        :type channels: dict
        :type group: set
        :type marking: set
        :type slate: Counter
        :type tally: Counter

        """
        name = fmt.format(len(cls.population) + 1, cls=cls)
        kwargs["name"] = kwargs.get("name", name)
        rv = cls(*args, **kwargs)
        cls.population[rv.uid] = rv
        return rv

    @staticmethod
    def build_arcs(dag):
        n = 0
        for k, v in dag.items():
            if not n:
                yield (n, (None, k))
            for i in v:
                n += 1
                yield n, (k, i)

    def __init__(
        self, *args,
        uid=None, name=None, channels=None, group=None,
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
        self.domain = []

    def __call__(self, **kwargs):
        for proc in self.domain:
            yield from proc(**kwargs)

        n = 1
        try:
            fn = next(fn for fn in self.enabled)
        except StopIteration:
            return

        events = fn(fn, **kwargs) or []
        for obj in events:
            if obj is None:
                # Transition is complete
                self.marking -= self.i_nodes[fn]
                self.marking.update(self.o_nodes[fn])
                n = self.slate[fn] = 0
            elif isinstance(obj, Proclet):
                # Transition spawns a new Proclet
                yield obj
                if obj not in self.domain:
                    self.domain.append(obj)
            else:
                yield obj
        self.slate[fn.__name__] += n
        self.tally[fn.__name__] += 1

    @property
    def dag(self):
        """
        This dictionary maps transition methods to a list of those which follow them in the net flow.

        """
        return {}

    @property
    def enabled(self):
        rv = {self.arcs[i][1]: i for i in sorted(self.marking)}
        return list(rv.keys())

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
