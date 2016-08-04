# -*- coding: utf-8 -*-
#
# Copyright (C) 2016 Bet@net
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#
# Author Daniel J. Ramirez <djrmuv@gmail.com>

from gluon import current
from gluon import URL
from gluon.contrib.appconfig import AppConfig
## once in production, remove reload=True to gain full speed
CONF = AppConfig()


# constants definitions
FLOW_BASIC = 0  # seller and manager

# one person list the items, other checkouts and other delivers
FLOW_MULTIROLE = 1

# reduce the common employee permissions to the mimimum
FLOW_IRON_FIST = 2



class AccessCard:
    data = {}
    def __init__(self, data):
        self.data = data

    def name(self):
        return self.data['name']

    def description(self):
        return self.data['description']

    def groups(self):
        return self.data['groups']


class Workflow:
    _cards = []
    _data = {}

    def __init__(self, cards, data):
        self._cards = cards
        self._data = data

    def cards(self):
        return self._cards

    def card(self, index):
        if len(self._cards) > index:
            return self._cards[index]
        else:
            raise None


def get_workflows():
    T = current.T

    return [
        Workflow([
            AccessCard({
                'name': T('Seller'),
                'description': T('Employees with this card can create and delete and sell bags (checkout and deliver items), modify basic items information like its name, categories and pictures, return items'),
                'groups': ['Items info', 'Sales bags', 'Sales checkout', 'Sales invoices', 'Sales delivery', 'Sales returns', 'Sale orders']
            }),
            AccessCard({
                'name': T('Manager'),
                'description': T('Manager employees can create inventories, make purchases, change item prices, sell items at diferent prices, create invoices, make cash outs and view analytic data'),
                'groups': ['Manager', 'Inventories', 'Purchases', 'Items management', 'Items prices', 'Items info', 'Sales bags', 'Sales checkout', 'Sales invoices', 'Sales delivery', 'Sales returns', 'Sales invoices', 'VIP seller', 'Analytics', 'Sale orders', 'Stock transfers', 'Offers', 'Accounts payable', 'Accounts receivable', 'Highlights', 'Cash out', 'Product loss', 'Safe config'
                ]
            })
        ], {}),
        Workflow([
            AccessCard({
                'name': T('Bags'),
                'description': T('Employees with this card can create bag but they can\'t checkout or deliver products'),
                'groups': ['Sales bags']
            }),
            AccessCard({
                'name': T('Checkout'),
                'description': T('Employees with this card can process a bag ticket in order to checkout, but they can\'t deliver the merchandise'),
                'groups': ['Sales checkout', 'Sales invoices', 'Sales returns', 'Sale orders']
            }),
            AccessCard({
                'name': T('Delivery'),
                'description': T('Employees with this card can deliver merchandise already paid'),
                'groups': ['Sales delivery']
            }),
            AccessCard({
                'name': T('Manager'),
                'description': T('Manager employees can create inventories, make purchases, change item prices, sell items at diferent prices, create invoices, make cash outs and view analytic data'),
                'groups': ['Manager', 'Inventories', 'Purchases', 'Items management', 'Items prices', 'Items info', 'Sales bags', 'Sales checkout', 'Sales invoices', 'Sales delivery', 'Sales returns', 'Sales invoices', 'VIP seller', 'Analytics', 'Sale orders', 'Stock transfers', 'Offers', 'Accounts payable', 'Accounts receivable', 'Highlights', 'Cash out', 'Product loss', 'Safe config'
                ]
            })
        ], {})
    ]

WORKFLOW_DATA = get_workflows()


# sale events
SALE_DEFERED = 'defered'
SALE_DELIVERED = 'delivered'
SALE_CREATED = 'created'
SALE_PAID = 'paid'


BAG_ACTIVE = 0
BAG_COMPLETE = 1
BAG_FOR_ORDER = 2
BAG_ORDER_COMPLETE = 3


# cache names
CACHED_POPULAR_ITEMS = 0

TAX_TRANSFER = 1
TAX_RETAIN = 2

STRIPE_PK = CONF.take('stripe.public_key')
STRIPE_SK = CONF.take('stripe.secure_key')
