# -*- coding: utf-8 -*-
#
# Author: Daniel J. Ramirez

# constants definitions
FLOW_BASIC = 0  # seller and manager
FLOW_MULTIROLE = 1
FLOW_CUSTOM = 2

WORKFLOW_DATA = [
    [
        {
            'name': T('Seller'),
            'description': T('Employees with this card can create and delete and sell bags (checkout and deliver items), modify basic items information like its name, categories and pictures, return items'),
            'groups': ['Items info', 'Sales bags', 'Sales checkout', 'Sales invoices', 'Sales delivery', 'Sales returns']
        },
        {
            'name': T('Manager'),
            'description': T(''),
            'groups': ['Items info', 'Sales bags', 'Sales checkout', 'Sales invoices', 'Sales delivery', 'Sales returns']
        }
    ],
    [],
    []
]


#TODO move this to config
EMAIL_SENDER = ''
EMAIL_TLS = True
EMAIL_SERVER = 'smtp.mandrillapp.com:587'
EMAIL_LOGIN = ''
