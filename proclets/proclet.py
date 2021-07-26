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
import operator
import uuid
import warnings
import weakref


class Proclet:
    """
    Proclets are callable objects which generate (yield) other objects.
    Their workflow is defined as a net of *places* and *transitions*.
    Each Proclet instance maintains a *marking* which determines which transitions
    are enabled at any particular time.

    To use Proclets, first define a subclass::

        class MyProc(Proclet):

            ...

    Add behaviour by defining one or more `transition` methods.
    A reference to the method itself gets passed in as the parameter `this` when it is called::

        def pro_one(self, this, **kwargs):
            ...

        def pro_two(self, this, **kwargs):
            ...

    Publish the workflow net as a directed graph::

        @property
        def net(self):
            return {
                self.pro_one: [self.pro_two],
                self.pro_two: []
            }

    Use the :meth:`~proclets.proclet.Proclet.create` method to obtain an instance::

        p = MyProc.create()

    When you call the Proclet, those transition methods will be enabled in the order
    defined by the :attr:`~proclets.proclet.Proclet.net`. When a transition method
    yields `None`, then operation flows on to the next.

    Proclets will run forever if you let them. To halt operation, a transition may raise a
    :class:`proclets.types.Termination` exception, which you can handle in the calling routine::

        while True:
            try:
                for msg in p():
                    print(msg)
            except Termination:
                break

    """

    population = weakref.WeakValueDictionary()
    """
    This class attribute dictionary stores every created Proclet instance by its unique `uid`.

    """

    @classmethod
    def create(cls, *args, fmt="{cls.__name__}_{0:03}", **kwargs):
        """
        This is the class factory method by which to create all Proclet objects.

        New proclets are registered in the :attr:`~proclets.proclet.Proclet.population` dictionary
        so they can be retrieved by unique `uid`.

        Keyword arguments may be any of the following (all are optional):

        :param uid:     A unique identifier for the object. Generated if not supplied.
        :param name:    A human-readable name for the object.
                        If not supplied, len(:attr:`~proclets.proclet.Proclet.population`) is
                        passed to the format string `fmt` to generate one.
        :param channels:    A dictionary of named :class:`~proclets.channel.Channel` objects.
        :param group:   Contains the `uid` s of other Proclets to communicate with.
        :param marking: An initial numerical marking to enable Proclet transitions declared in the
                        :attr:`~proclets.proclet.Proclet.net`.
        :param slate:   The instance attribute `slate` stores the number of times a transition has blocked.
                        You can initialise that via this parameter.
        :param tally:   The instance attribute `tally` stores the number of times a transition has been enabled.
                        You can initialise that via this parameter.
        :param priority:    A numerical value for relative priority of execution.
                            Smaller values have higher priority.

        :type uid: uuid.UUID
        :type name: str
        :type channels: dict
        :type group: set
        :type marking: set
        :type slate: Counter
        :type tally: Counter
        :type priority: int

        """
        name = fmt.format(len(cls.population) + 1, cls=cls)
        kwargs["name"] = kwargs.get("name", name)
        kwargs["marking"] = kwargs.get("marking", set()).copy()
        rv = cls(*args, **kwargs)
        cls.population[rv.uid] = rv
        return rv

    @staticmethod
    def build_arcs(net):
        n = 0
        for k, v in net.items():
            if not n:
                yield n, (None, k)
            for i in v:
                n += 1
                yield n, (k, i)

    def __init__(
        self, *args,
        uid=None, name=None, channels=None, group=None,
        marking=None, slate=None, tally=None, priority=None
    ):
        self.uid = uid or uuid.uuid4()
        self.name = name or self.uid
        self.channels = channels or {}
        self.group = group or set()
        self.marking = marking or {0}
        self.slate = slate or Counter()
        self.tally = tally or Counter()
        self.priority = priority
        self.arcs = dict(self.build_arcs(self.net))
        self.domain = []

    def __call__(self, **kwargs):
        procs = [
            (p.priority if p.priority is not None else len(p.tally), p)
            for p in [self] + self.domain
        ]
        while procs:
            procs.sort(key=operator.itemgetter(0))
            priority, p = procs.pop(0)
            if p is not self:
                yield from p(**kwargs)
            else:
                n = 1
                for fn in self.enabled:
                    events = fn(fn, **kwargs) or []
                    for obj in events:
                        if obj is None:
                            # Transition is complete
                            self.marking -= self.i_nodes[fn]
                            self.marking.update(self.o_nodes[fn])
                            n = self.slate[fn] = 0
                        elif isinstance(obj, Proclet):
                            # Transition spawns a new Proclet
                            if obj not in self.domain:
                                self.domain.append(obj)
                                procs.append(
                                    (obj.priority if obj.priority is not None else len(obj.tally), obj)
                                )
                        yield obj
                    self.slate[fn.__name__] += n
                    self.tally[fn.__name__] += 1

    @property
    def net(self):
        """
        This dictionary maps transition methods to a list of those which follow them in the net flow.

        """
        return {}

    @property
    def enabled(self):
        """
        The list of methods currently enabled by token positions.

        """
        return [i for k, i in sorted(
            ((self.tally[i.__name__], i)
            for i in self.net if self.i_nodes[i].issubset(self.marking)),
            key=operator.itemgetter(0))]

    @functools.cached_property
    def i_nodes(self):
        """
        This dictionary maps transition methods to the numerical marking which enables them.

        """
        rv = defaultdict(set)
        ordinals = {i: n for n, i in enumerate(self.net)}
        for p, (s, d) in self.arcs.items():
            if None in (s, d) or ordinals[s] < ordinals[d]:
                # An arc to a subsequent transition creates a place
                rv[d].add(p)
        return rv

    @functools.cached_property
    def o_nodes(self):
        """
        This dictionary maps transition methods to the numerical marking they generate when fired.

        """
        rv = defaultdict(set)
        ordinals = {i: n for n, i in enumerate(self.net)}
        for p, (s, d) in self.arcs.items():
            if None not in (s, d) and ordinals[s] >= ordinals[d]:
                # An arc back to a previous transition does not create a place
                try:
                    p = ordinals[d] and sorted(self.i_nodes[s])[0]
                except IndexError:
                    warnings.warn(f"Missing an arc to {self.__class__.__name__}.{s.__name__}")
            rv[s].add(p)
        return rv
