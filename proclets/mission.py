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
import random
import sys

from proclets.channel import Channel
from proclets.proclet import Proclet
from proclets.types import Init
from proclets.types import Exit
from proclets.types import Termination


class Control(Proclet):

    @property
    def net(self):
        return {
            self.pro_launch: [self.pro_separation],
            self.pro_separation: [self.pro_reentry],
            self.pro_reentry: [self.pro_recovery, self.pro_reentry],
            self.pro_recovery: [self.pro_complete, self.pro_recovery],
            self.pro_complete: [],
        }

    def pro_launch(self, this, **kwargs):
        logging.info("We are go for launch", extra={"proclet": self})
        self.results = {}
        self.roster = {}
        yield from self.channels["uplink"].send(
            sender=self.uid, group=self.group,
            action=this.__name__,
        )
        yield

    def pro_separation(self, this, **kwargs):
        try:
            sync = next(
                i for i in self.channels["uplink"].receive(self, this)
                if i.action == this.__name__
            )
            logging.debug(sync, extra={"proclet": self})
        except StopIteration:
            return
        else:
            logging.info("Copy your separation", extra={"proclet": self})
            yield

    def pro_reentry(self, this, **kwargs):
        try:
            sync = next(
                i for i in self.channels["beacon"].receive(self, this)
                if i.action == this.__name__
            )
        except StopIteration:
            yield
        else:
            vehicle = self.population[sync.sender].name.lower()
            logging.info(f"Observing reentry of {vehicle}", extra={"proclet": self})
            channels = {k: self.channels[k] for k in ("beacon", "vhf")}
            yield Recovery.create(
                name="Recovery Team",
                target=sync.sender,
                channels=channels,
                group=[self.uid],
            )
            yield

    def pro_recovery(self, this, **kwargs):
        targets = {i.target for i in self.domain} - set(self.results)

        try:
            p = next(i for i in self.domain if self.roster.get(i) not in targets)
            t = next(iter(targets))
            yield from self.channels["vhf"].send(
                sender=self.uid, group={p.uid},
                action=Init.request, context={t},
            )
            self.roster[p] = t
            vehicle = self.population[t].name.lower()
            logging.info(f"Team {p.uid.hex[:3]} briefed for recovery of {vehicle}", extra={"proclet": self})
        except StopIteration:
            pass
        finally:
            yield

    def pro_complete(self, this, **kwargs):
        for msg in self.channels["vhf"].receive(self, this):
            logging.debug(msg, extra={"proclet": self})
            if msg.action == Exit.deliver:
                for i in msg.context:
                    self.results[i] = msg

        if len(self.results) == 2:
            logging.info("Mission complete", extra={"proclet": self})
            raise Termination()


class Recovery(Proclet):

    def __init__(self, target, *args, luck=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.target = target
        self.luck = random.triangular(0, 1, 3/4) if luck is None else luck
        self.duty = None

    @property
    def net(self):
        return {
            self.pro_tasking: [self.pro_recovery],
            self.pro_recovery: [self.pro_standby],
            self.pro_standby: [self.pro_tasking],
        }

    def pro_tasking(self, this, **kwargs):
        logging.info(f"Waiting", extra={"proclet": self})
        try:
            self.duty = list(
                self.channels["vhf"].respond(
                    self, this,
                    actions={Init.request: Init.promise},
                )
            )[0]
            yield
        except IndexError:
            return

    def pro_recovery(self, this, **kwargs):
        vehicle = self.population[next(iter(self.duty.context))].name.lower()
        logging.info(f"Commencing search for {vehicle}", extra={"proclet": self})
        if random.random() < self.luck:
            yield from self.channels["beacon"].send(
                sender=self.uid, group=self.duty.context,
                context=self.duty.context,
                action=this.__name__,
            )
            yield self.channels["vhf"].reply(self, self.duty, action=Exit.deliver)
            logging.info(f"Rendezvous with {vehicle}", extra={"proclet": self})
            yield
        else:
            yield self.channels["vhf"].reply(self, self.duty, action=Exit.abandon)
            logging.info(f"Abandoning search for {vehicle}", extra={"proclet": self})
            yield

    def pro_standby(self, this, **kwargs):
        logging.info(f"Team {self.uid.hex[:3]} standing by", extra={"proclet": self})
        self.duty = None
        yield


class Vehicle(Proclet):

    def __init__(self, *args, orbits=0, **kwargs):
        super().__init__(*args, **kwargs)
        self.orbits = orbits

    @property
    def net(self):
        return {
            self.pro_launch: [self.pro_separation],
            self.pro_separation: [self.pro_orbit],
            self.pro_orbit: [self.pro_reentry],
            self.pro_reentry: [self.pro_recovery],
            self.pro_recovery: [],
        }

    def pro_launch(self, this, **kwargs):
        try:
            sync = next(
                i for i in self.channels["uplink"].receive(self, this)
                if i.action == this.__name__
            )
            logging.debug(sync, extra={"proclet": self})
        except StopIteration:
            return
        else:
            logging.info("Launch phase is complete", extra={"proclet": self})
            yield

    def pro_separation(self, this, **kwargs):
        logging.info("Separation initiated", extra={"proclet": self})
        v = Vehicle.create(
            name="Launch vehicle", orbits=None,
            channels={"beacon": self.channels["beacon"]}, group=self.group,
            marking=self.i_nodes[self.pro_reentry],
        )
        yield v
        yield from self.channels["uplink"].send(
            sender=self.uid, group=self.group, context={v.uid},
            action=this.__name__,
        )
        yield

    def pro_orbit(self, this, **kwargs):
        if self.orbits is None:
            yield

        if self.orbits < 3:
            self.orbits += 1
            logging.info(f"In orbit {self.orbits}", extra={"proclet": self})
        else:
            yield

    def pro_reentry(self, this, **kwargs):
        logging.info("Re-entering atmosphere", extra={"proclet": self})
        yield from self.channels["beacon"].send(
            sender=self.uid, group=self.group,
            action=this.__name__,
        )
        yield

    def pro_recovery(self, this, **kwargs):
        try:
            sync = next(
                i for i in self.channels["beacon"].receive(self, this)
                if i.action == this.__name__
            )
            logging.debug(sync, extra={"proclet": self})
        except StopIteration:
            return
        else:
            logging.info("Signing off", extra={"proclet": self})
            yield


def mission():
    channels = {"uplink": Channel(), "beacon": Channel()}
    v = Vehicle.create(name="Space vehicle", channels=channels)
    c = Control.create(name="Mission control", channels=dict(channels, vhf=Channel()), group=[v.uid])
    v.group = [c.uid]
    return (c, v)


if __name__ == "__main__":
    logging.basicConfig(
        style="{", format="{proclet.name:>16}|{funcName:>14}|{message}",
        level=logging.INFO,
    )
    procs = (c, v) = mission()
    rv = None
    while rv is None:
        for p in procs:
            try:
                for m in p():
                    logging.debug(m, extra={"proclet": p})
            except Termination:
                rv = 0
            except Exception:
                rv = 1

    sys.exit(rv)
