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

import logging
import sys

from proclets.channel import Channel
from proclets.promise import Promise
from proclets.types import Init
from proclets.types import Exit
from proclets.types import Fruition
from proclets.types import Termination


class Brew(Promise):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.actions = {
            Exit.deliver: Exit.confirm,
        }
        self.kettle = None

    @property
    def net(self):
        return {
            self.pro_filling: [self.pro_boiling, self.pro_missing],
            self.pro_missing: [self.pro_claiming],
            self.pro_boiling: [self.pro_brewing],
            self.pro_claiming: [self.pro_inspecting, self.pro_claiming],
            self.pro_inspecting: [self.pro_approving],
            self.pro_approving: [self.pro_brewing],
            self.pro_brewing: [self.pro_serving],
            self.pro_serving: [],
        }

    def pro_filling(self, this, **kwargs):
        self.log.info("", extra={"proclet": self})
        self.kettle = 20
        yield

    def pro_missing(self, this, **kwargs):
        self.log.info("", extra={"proclet": self})
        jobs = [tuple({k: v}.items()) for k, v in kwargs.items()]
        if all(self.fruition[j] == Fruition.construction for j in jobs):
            yield

        for j in jobs:
            if self.fruition[j] == Fruition.inception:
                p = Kit.create(
                    name=f"find_{j[0][0]}",
                    channels=self.channels,
                    group=[self.uid],
                )
                yield p

                m = next(self.channels["public"].send(
                    sender=self.uid, group=[p.uid],
                    action=Init.request, content=dict(j)))
                self.fruition[j] = self.fruition[j].trigger(m.action)
                yield m

        for m in self.channels["public"].respond(self, this, actions=self.actions, contents=self.contents):
            self.contents[m.action] = m.content or self.contents[Init.request]
            try:
                j = tuple(m.content.items())
            except AttributeError:
                self.log.debug(m, extra={"proclet": self})
            else:
                self.fruition[j] = self.fruition[j].trigger(m.action)
            finally:
                yield m

    def pro_boiling(self, this, **kwargs):
        self.log.info(self.kettle, extra={"proclet": self})
        while self.kettle <= 90:
            self.kettle += 10
            return
        yield

    def pro_claiming(self, this, **kwargs):
        senders = {i.uid for i in self.domain if isinstance(i, Kit)}
        for m in self.channels["public"].respond(
            self, this, actions=self.actions, contents=self.contents, senders=senders
        ):
            self.contents[m.action] = m.content
            try:
                j = tuple(m.content.items())
            except AttributeError:
                return
            else:
                self.fruition[j] = self.fruition[j].trigger(m.action)
                self.log.debug(self.fruition, extra={"proclet": self})
                yield

    def pro_inspecting(self, this, **kwargs):
        self.log.info("", extra={"proclet": self})
        jobs = [tuple({k: v}.items()) for k, v in kwargs.items() if k in ("mugs", "spoons")]
        if all(
            self.dispatched(j, Tidy) and self.fruition[j] == Fruition.construction for j in jobs
        ):
            yield

        for j in jobs:
            if self.dispatched(j, Tidy):
                continue

            self.fruition[j] = Fruition.inception
            p = Tidy.create(
                name=f"clean_{j[0][0]}",
                channels=self.channels,
                group=[self.uid],
            )
            yield p

            m = next(self.channels["public"].send(
                sender=self.uid, group=[p.uid],
                action=Init.request, content=dict(j)
            ))
            self.fruition[j] = self.fruition[j].trigger(m.action)
            yield m

    def pro_approving(self, this, **kwargs):
        self.log.info("", extra={"proclet": self})
        while any(i != Fruition.completion for i in self.fruition.values()):
            for m in self.channels["public"].receive(self, this):
                yield m
                j = tuple(m.content.items())
                if j in self.fruition:
                    self.fruition[j] = self.fruition[j].trigger(m.action)
                    r = self.channels["public"].reply(self, m, action=Exit.confirm, content=dict(j))
                else:
                    r = self.channels["public"].reply(self, m, action=Exit.decline)
                yield r
                self.fruition[j] = self.fruition[j].trigger(r.action)
        else:
            yield

    def pro_brewing(self, this, **kwargs):
        self.log.info("", extra={"proclet": self})
        yield

    def pro_serving(self, this, **kwargs):
        self.log.info("", extra={"proclet": self})
        if not self.pending:
            raise Termination()
            yield


class Kit(Promise):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.actions = {
            Init.request: Init.promise,
        }

    @property
    def net(self):
        return {
            self.pro_init: [self.pro_finding],
            self.pro_finding: [self.pro_exit],
            self.pro_exit: [],
        }

    def pro_finding(self, this, **kwargs):
        self.log.info("", extra={"proclet": self})
        for job in self.fruition:
            for k in dict(job):
                self.log.info(f"Finding {k}", extra={"proclet": self})
        yield


class Tidy(Promise):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.actions = {
            Init.request: Init.promise,
        }

    @property
    def net(self):
        return {
            self.pro_init: [self.pro_cleaning],
            self.pro_cleaning: [self.pro_exit],
            self.pro_exit: [],
        }

    def pro_cleaning(self, this, **kwargs):
        self.log.info("", extra={"proclet": self})
        for j in self.fruition:
            self.log.info(f"Cleaning {j[0][0]}", extra={"proclet": self})
        yield


def promise(**kwargs):
    name = kwargs.pop("name", "brew_tea")
    channels = {"public": Channel()}
    return Brew.create(name=name, channels=channels, **kwargs)


def execute(p: Promise, **kwargs):
    while True:
        try:
            for m in p(**kwargs):
                logging.debug(m, extra={"proclet": p})
                if m is not None:
                    yield m
        except Termination:
            return
        except Exception as e:
            logging.exception(e, extra={"proclet": p})
            yield None


if __name__ == "__main__":
    logging.basicConfig(
        style="{", format="{proclet.name:>16}|{funcName:>14}|{message}",
        level=logging.INFO,
    )
    p = promise()
    for n, m in enumerate(execute(p, mugs=2, tea=2, milk=2, spoons=1, sugar=1)):
        if n > 75:
            break
        if m is None:
            sys.exit(1)

    sys.exit(0)
