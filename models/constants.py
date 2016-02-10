# -*- coding: utf-8 -*-
#
# Author: Daniel J. Ramirez

# constants definitions
FLOW_BASIC = 0  # seller and manager
FLOW_MULTIROLE = 1
FLOW_CUSTOM = 2



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
    _flow = {}
    _data = {}

    def __init__(self, cards, data):
        self._cards = cards
        self._flow = data['flow']
        self._data = data

    def cards(self):
        return self._cards

    def card(self, index):
        if len(self._cards) > index:
            return self._cards[index]
        else:
            raise None

    def next(self, controller, function, user):
        key = '%s_%s' % (controller, function)
        if self._flow.has_key(key):
            if user.access_card_index in self._flow[key]['required']:
                return self._flow[key]['next']
            else:
                return self._flow[key]['invalid']


WORKFLOW_DATA = [
    Workflow(
        [
            AccessCard({
                'name': T('Seller'),
                'description': T('Employees with this card can create and delete and sell bags (checkout and deliver items), modify basic items information like its name, categories and pictures, return items'),
                'groups': ['Items info', 'Sales bags', 'Sales checkout', 'Sales invoices', 'Sales delivery', 'Sales returns', 'Sale orders']
            }),
            AccessCard({
                'name': T('Manager'),
                'description': T('Manager employees can create inventories, make purchases, change item prices, sell items at diferent prices, create invoices, make cash outs and view analytic data'),
                'groups': ['Manager', 'Inventories', 'Purchases', 'Items management', 'Items prices', 'Items info', 'Sales bags', 'Sales checkout', 'Sales invoices', 'Sales delivery', 'Sales returns', 'Sales invoices', 'VIP seller', 'Analytics', 'Sale orders', 'Stock transfers'
                ]
            })
        ],
        {
            'flow': {
                'bag_complete': {
                    'next': URL('sale', 'create'),
                    'required': [0, 1],
                    'invalid': URL('bag', 'ticket')
                },
            }
        }
    )
]


#TODO move this to config
EMAIL_SENDER = ''
EMAIL_TLS = True
EMAIL_SERVER = 'smtp.mandrillapp.com:587'
EMAIL_LOGIN = ''
