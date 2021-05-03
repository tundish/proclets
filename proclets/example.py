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

import enum
from collections import Counter
from collections import defaultdict
from collections import deque
from dataclasses import dataclass
from dataclasses import field
import itertools
import logging
import operator
import queue
import random
import sys
import uuid

from proclets.channel import Channel
from proclets.proclet import Proclet
from proclets.types import Init
from proclets.types import Exit
from proclets.types import Performative


class Product(enum.Enum):
    apple = enum.auto()
    brush = enum.auto()
    cloth = enum.auto()


@dataclass(frozen=True)
class Item:

    uid: uuid.UUID = field(default_factory=uuid.uuid4)
    product: Product = None
    quantity: int = 0


class Order(Proclet):

    @staticmethod
    def report(m):
        try:
            source = Proclet.population[m.sender]
            connect = getattr(m.connect, "hex", "")
            return f"{connect:>36}|{source.name:^20}|{m.action:<14}|{m.content or ''}"
        except AttributeError:
            return "{0}|{1}|Call Proclet  |{2.name} in play".format(" "*36, " "*20, m)
        except (KeyError, TypeError):
            print(m, file=sys.stderr)
            raise

    def __init__(self, items, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.items = items

    @property
    def dag(self):
        return {
            self.pro_create: [self.pro_split],
            self.pro_split: [self.pro_notify],
            self.pro_notify: [self.pro_bill],
            self.pro_bill: [],
        }

    def pro_create(self, this, **kwargs):
        # Stub method for compatibility with Fahland
        yield

    def pro_split(self, this, **kwargs):
        durables, perishables = [], []
        groups = itertools.groupby(self.items, key=operator.attrgetter("product"))
        for p, g in groups:
            if p in (Product.brush, Product.cloth):
                durables.extend(g)
            else:
                perishables.extend(g)

        for items in (durables, perishables):
            if not items: continue
            p = Package.create(items, channels=self.channels)
            yield p
            yield from self.channels["orders"].send(
                sender=self.uid, group=[p.uid],
                action=this.__name__,
            )

        yield

    def pro_notify(self, this, **kwargs):
        for p in self.domain:
            yield from self.channels["orders"].send(
                sender=self.uid, group=[p.uid], connect=self.uid,
                action=Init.request, context=set(self.domain),
                content="{0} item{1}".format(len(p.contents), "s" if len(p.contents) > 1 else "")
            )
        yield

    def pro_bill(self, this, **kwargs):
        try:
            sync = next(
                i for i in self.channels["logistics"].receive(self, this)
                if i.action == this.__name__
            )
        except StopIteration:
            pass
        else:
            self.delivery[next(iter(self.delivery))] = True


class Package(Proclet):

    def __init__(self, contents, *args, luck=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.contents = contents
        self.luck = random.triangular(0, 1, 3/4) if luck is None else luck
        self.delivery = {}
        self.back = {}

    @property
    def dag(self):
        return {
            self.pro_split: [self.pro_load],
            self.pro_load: [
                self.pro_retry, self.pro_deliver, self.pro_undeliver, self.pro_bill, self.pro_finish
            ],
            self.pro_deliver: [self.pro_load],
            self.pro_retry: [self.pro_load],
            self.pro_undeliver: [self.pro_load],
            self.pro_bill: [self.pro_load],
            self.pro_finish: [],
        }

    def pro_split(self, this, **kwargs):
        yield from self.channels["orders"].respond(
            self, this,
            actions={this.__name__: None},
        )

    def pro_load(self, this, **kwargs):
        if not self.delivery:
            d = Delivery.create(
                channels=self.channels,
                group={self.uid},
            )
            self.delivery[d.uid] = None
            yield d

            yield from self.channels["logistics"].send(
                sender=self.uid, group=[d.uid],
                action=this.__name__,
            )

        yield

    def pro_deliver(self, this, **kwargs):
        try:
            sync = next(
                i for i in self.channels["logistics"].receive(self, this)
                if i.action == this.__name__
            )
        except StopIteration:
            pass
        else:
            self.delivery[next(iter(self.delivery))] = True
        finally:
            yield None

    def pro_retry(self, this, **kwargs):
        try:
            sync = next(
                i for i in self.channels["logistics"].receive(self, this)
                if i.action == this.__name__
            )
        except StopIteration:
            pass
        else:
            self.delivery[next(iter(self.delivery))] = None
        finally:
            yield None

    def pro_undeliver(self, this, **kwargs):
        try:
            sync = next(
                i for i in self.channels["logistics"].receive(self, this)
                if i.action == this.__name__
            )
        except StopIteration:
            pass
        else:
            self.delivery[next(iter(self.delivery))] = False
            b = Back.create(
                channels=self.channels,
                group={self.uid},
            )
            self.back[b.uid] = None
            yield b
            yield from self.channels["logistics"].send(
                sender=self.uid, group=[b.uid],
                action="pro_return",
            )
        finally:
            yield None

    def pro_bill(self, this, **kwargs):
        yield

    def pro_finish(self, this, **kwargs):
        d_uid = next(iter(self.delivery), None)
        if d_uid and self.delivery[d_uid] is not None:
            yield from self.channels["logistics"].send(
                sender=self.uid, group=[d_uid],
                action=this.__name__,
            )
            self.delivery.clear()
        #yield None


class Delivery(Proclet):

    @classmethod
    def create(cls, *args, domain=None, fmt="{cls.__name__}_{0:03}", **kwargs):
        domain = domain or cls.population.values()
        try:
            rv = next(i for i in domain if isinstance(i, cls) and i.capacity > len(i.group))
            rv.group.update(kwargs.get("group", set()))
            return rv
        except StopIteration:
            name = fmt.format(len(cls.population) + 1, cls=cls)
            kwargs["name"] = kwargs.get("name", name)
            rv = cls(*args, **kwargs)
            cls.population[rv.uid] = rv
            return rv

    def __init__(self, *args, capacity=2, limit=3, **kwargs):
        super().__init__(*args, **kwargs)
        self.capacity = capacity
        self.limit = limit
        self.retries = Counter()

    @property
    def dag(self):
        return {
            self.pro_load: [self.pro_retry, self.pro_deliver, self.pro_undeliver, self.pro_finish],
            self.pro_retry: [self.pro_next],
            self.pro_deliver: [self.pro_next],
            self.pro_undeliver: [self.pro_next],
            self.pro_next: [self.pro_load, self.pro_retry, self.pro_deliver, self.pro_undeliver, self.pro_finish],
            self.pro_finish: [],
        }

    def pro_load(self, this, **kwargs):
        try:
            sync = next(
                i for i in self.channels["logistics"].receive(self, this)
                if i.action == this.__name__
            )
        except StopIteration:
            pass
        else:
            sync.content = f"Loaded package {sync.sender.hex[:5]}"
            self.retries[sync.sender] = 0
            sync.sender = self.uid
            yield sync
        finally:
            yield None

    def pro_retry(self, this, **kwargs):
        try:
            n, pkg_uid = next(iter(sorted(
                (v, k) for k, v in self.retries.items() if v is not None and v < self.limit
            )))
        except StopIteration:
            pass
        else:
            pkg = self.population[pkg_uid]
            if random.random() > pkg.luck:
                self.retries[pkg_uid] += 1

                yield from self.channels["logistics"].send(
                    sender=self.uid, group=[pkg_uid],
                    action = this.__name__,
                    content = f"Retry {self.retries[pkg_uid]} for {pkg_uid.hex[:5]}",
                )
        finally:
            yield None

    def pro_deliver(self, this, **kwargs):
        try:
            n, pkg_uid = next(iter(sorted((v, k) for k, v in self.retries.items() if v is not None)))
        except StopIteration:
            pass
        else:
            pkg = self.population[pkg_uid]
            if random.random() < pkg.luck:

                yield from self.channels["logistics"].send(
                    sender=self.uid, group=[pkg_uid],
                    action = this.__name__,
                    content = f"Delivered {pkg_uid.hex[:5]} " + (f"after {n} retries" if n else "first time"),
                )
                self.retries[pkg_uid] = None
        finally:
            yield None

    def pro_undeliver(self, this, **kwargs):
        try:
            n, pkg_uid = next(iter(sorted((v, k) for k, v in self.retries.items() if v == self.limit)))
        except StopIteration:
            pass
        else:
            pkg = self.population[pkg_uid]
            yield from self.channels["logistics"].send(
                sender=self.uid, group=[pkg_uid],
                action = this.__name__,
                content = f"Failed to deliver {pkg_uid.hex[:5]}",
            )
            self.retries[pkg_uid] = None
        finally:
            yield None

    def pro_next(self, this, **kwargs):
        yield

    def pro_finish(self, this, **kwargs):
        try:
            sync = next(
                i for i in self.channels["logistics"].receive(self, this)
                if i.action == this.__name__
            )
        except StopIteration:
            pass
        else:
            self.retries[sync.sender] = None
            self.capacity = 0
        finally:
            yield None


class Back(Proclet):

    @property
    def dag(self):
        return {
            self.pro_return: [self.pro_check],
            self.pro_check: [self.pro_bill],
            self.pro_bill: [],
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.package = None

    def pro_return(self, this, **kwargs):
        try:
            sync = next(
                i for i in self.channels["logistics"].receive(self, this)
                if i.action == this.__name__
            )
        except StopIteration:
            pass
        else:
            self.package = sync.sender
            sync.content = f"Returning package {sync.sender.hex[:5]}"
            yield sync
        finally:
            yield None

    def pro_check(self, this, **kwargs):
        yield

    def pro_bill(self, this, **kwargs):
        yield from self.channels["orders"].send(
            sender=self.uid, group=[self.package],
            action = this.__name__,
        )
        yield


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, style="{", format="{message}")
    channels = {"orders": Channel(), "logistics": Channel(), "billing": Channel()}
    choices = list(Product)
    jobs = [
        Order.create([
            Item(product=random.choice(choices), quantity=random.randint(1, 6)),
            Item(product=random.choice(choices), quantity=random.randint(1, 6))
        ], channels=channels),
        Order.create([
            Item(product=random.choice(choices), quantity=random.randint(1, 6)),
            Item(product=random.choice(choices), quantity=random.randint(1, 6))
        ], channels=channels)
    ]
    for n in range(32):
    #while any(i.marking for i in jobs):
        for j in jobs:
            run = list(j())
            for r in run:
                logging.info(j.report(r))
