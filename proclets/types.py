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

from __future__ import annotations  # Use standard collection for generic typing in Python 3.8
from dataclasses import dataclass
from dataclasses import field
import enum
import time
import uuid


class Attribution(dict):

    def __init__(self, *args, uid=None, ts=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.uid = uid
        self.ts = ts


class Fruition(enum.Enum):
    """
    Terry Winograd, Fernando Flores, Craig Larman

    """
    inception = 1
    elaboration = 2
    construction = 3
    transition = 4
    completion = 5
    discussion = 6
    defaulted = 7
    withdrawn = 8
    cancelled = 9

    def trigger(self, event=None):
        if self.value == 1:
            return {
                Init.request: Fruition.elaboration
            }.get(event, self)
        elif self.value == 2:
            return {
                Init.promise: Fruition.construction,
                Init.counter: Fruition.discussion,
                Init.abandon: Fruition.withdrawn,
                Init.decline: Fruition.withdrawn,
            }.get(event, self)
        elif self.value == 3:
            return {
                Exit.abandon: Fruition.cancelled,
                Exit.deliver: Fruition.transition,
                Exit.decline: Fruition.defaulted,
            }.get(event, self)
        elif self.value == 4:
            return {
                Exit.abandon: Fruition.cancelled,
                Exit.decline: Fruition.construction,
                Exit.confirm: Fruition.completion,
            }.get(event, self)
        elif self.value == 6:
            return {
                Init.promise: Fruition.construction,
                Init.confirm: Fruition.construction,
                Init.counter: Fruition.elaboration,
                Init.abandon: Fruition.withdrawn,
                Init.decline: Fruition.withdrawn,
            }.get(event, self)
        else:
            return self


class FlowException(Exception): pass
class Restitution(FlowException): pass
class Termination(FlowException): pass


class Init(enum.Enum):

    request = enum.auto()
    promise = enum.auto()
    decline = enum.auto()
    confirm = enum.auto()
    counter = enum.auto()
    abandon = enum.auto()
    message = enum.auto()


class Exit(enum.Enum):

    deliver = enum.auto()
    decline = enum.auto()
    confirm = enum.auto()
    abandon = enum.auto()
    message = enum.auto()


@dataclass(order=True)
class Performative:

    ts:         int = field(default_factory=time.monotonic_ns)
    uid:        uuid.UUID = field(default_factory=uuid.uuid4)
    channel:    object = None
    sender:     uuid.UUID = None
    group:      set[uuid.UUID] = None
    connect:    uuid.UUID = None
    context:    set[int] = None
    action:     enum.Enum = None
    content:    object = None

