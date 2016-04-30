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

import urllib
import re
from decimal import Decimal as D
import math
import json
import random
from uuid import uuid4

from gluon import *
from gluon.storage import Storage
# from gluon import current


def INFO(text, btn_text=None, btn_url=None, btn_target=None):
    d = { 'text': text }
    if btn_text and btn_url:
        d['btn'] = {
            'text': btn_text,
            'href': btn_url,
            'target': btn_target
        }
    return d


rmap = {  'á': 'a', 'Á': 'a' , 'é': 'e', 'É': 'e' , 'í': 'i', 'Í': 'i'
        , 'ó': 'o', 'Ó': 'o' , 'ú': 'u', 'Ú': 'u'
       }
def replace_match(match):
    key = match.group(0)
    if rmap.has_key(key):
        return rmap[key]
    return ""
regex = re.compile('(á|é|í|ó|ú|Á|É|Í|Ó|Ú)')

def urlify_string(string):
    s = regex.sub(replace_match, string)
    s = urllib.quote(s)
    return s



def money_format(value):
    return '$ ' + str(value)


def get_notifications():
    auth = current.auth
    db = current.db
    T = current.T

    notifications = []
    # check pending orders
    if auth.has_membership('Sale orders'):
        pending_orders = db(db.sale_order.is_ready == False).select()
        if pending_orders:
            notifications.append(Storage(
                title=T("Sale order"), description=T('Some sale orders are pending'), url=URL('sale_order', 'index')
            ))

    if auth.has_membership('Accounts payable'):
        accounts_r = db(db.account_receivable.is_settled == False).select()
        if accounts_r:
            notifications.append(Storage(
                title=T("Accounts receivable"), description=T('Accounts receivable')+' '+T('unsettled'), url=URL('account_receivable', 'index')
            ))
    if auth.has_membership('Accounts receivable'):
        accounts_p = db(db.account_receivable.is_settled == False).select()
        if accounts_r:
            notifications.append(Storage(
                title=T("Accounts payable"), description=T('Accounts payable')+' '+T('unsettled'), url=URL('account_payable', 'index')
            ))

    return notifications


def DQ(value, lite=False, normalize=False):
    """ Decimal Quantized """

    if normalize:
        return D(value or 0).normalize()
    if lite:
        return D(value or 0).quantize(D('.00'))
    else:
        return D(value or 0).quantize(D('.000000'))


def remove_fractions(value):
    """ Return integer decimal representation """

    return D(math.floor(float(value))).quantize(D('1'))







def get_random_wallet_code():
    return str(uuid4()).split('-')[0] # is this random enough?

def new_wallet(balance=0):
    db = current.db
    wallet_code = get_random_wallet_code()
    return db.wallet.insert(wallet_code=wallet_code, balance=balance)


def is_wallet(payment_opt):
    if not payment_opt:
        return False
    return payment_opt.name == 'wallet'


def get_wallet_payment_opt():
    db = current.db
    return db(db.payment_opt.name == 'wallet').select().first()


def json_categories_tree(item=None, selected_categories=[], visible_categories=[]):
    """ Creates a json representation of the categories tree, this representation is used with bootstrap treeview """
    db = current.db

    categories = db((db.category.is_active == True)).select(orderby=~db.category.parent)
    if len(categories)==0:
        return []
    current_category = categories.first().parent
    categories_children = {}
    current_tree = []
    categories_selected_text = ""
    for category in categories:
        if category.parent != current_category:
            categories_children[current_category] = current_tree
            current_tree = []
            current_category = category.parent
        # current_tree.append({'text': category.name})
        child = {'text': category.name, 'category_id': category.id}
        if category.id in selected_categories:
            if child.has_key('state'):
                child['state']['selected'] = True
            else:
                child['state'] = {'selected': True};
        if item:
            if category.id in item.categories:
                child['state'] = {'checked': True};
                categories_selected_text += str(category.id) + ','
        if categories_children.has_key(category.id):
            child['nodes'] = categories_children[category.id]
            current_tree.append(child)
            if category.parent:
                del categories_children[category.id]
        else:
            current_tree.append(child)
    categories_children[current_category] = current_tree
    current_tree = []
    # the categories_children array contains the master categories.
    categories_tree = []
    for subtree in categories_children.itervalues():
        categories_tree.append(subtree)
    # json object from python dict
    categories_tree = json.dumps(categories_tree[0])

    return categories_tree



def redirection(url=None):
    session = current.session
    request = current.request
    _next = session._next or request.vars._next
    if _next:
        session._next = None
        redirect(_next)
    elif url:
        redirect(url)
    else:
        redirect(URL('default', 'index'))


def hex_to_rgb(hexv):
    nhexv = hexv
    if hexv[0] == '#':
        nhexv = hexv[1:]
    r = int(nhexv[0] + nhexv[1], 16)
    g = int(nhexv[2] + nhexv[3], 16)
    b = int(nhexv[4] + nhexv[5], 16)

    return r, g, b


def hex_to_css_rgba(hexv, alpha):
    r, g, b = hex_to_rgb(hexv)
    return "rgba(%d, %d, %d, %f)" % (r, g, b, float(alpha))


def rgb_to_hex(r,g,b):
    return '#%02X%02X%02X' % (r, g, b)

def dim_hex(hexv):
    r,g,b = hex_to_rgb(hexv)
    return rgb_to_hex(max(0, r - 20), max(0, g - 20), max(0, b - 20))

def bright_hex(hexv):
    r,g,b = hex_to_rgb(hexv)
    return rgb_to_hex(min(255, r + 20), min(255, g + 20), min(255, b + 20))

def random_color_mix(hexv):
    r,g,b = hex_to_rgb(hexv);

    r = int((r + random.randint(0, 255)) / 2)
    g = int((g + random.randint(0, 255)) / 2)
    b = int((b + random.randint(0, 255)) / 2)

    return rgb_to_hex(r, g, b)

    # mean = (r + g + b) / 3
    # sd = int(math.sqrt((r - mean) ** 2 + (g - mean) ** 2 + (b - mean) ** 2))


def color_mix(hex1, hex2):
    r1,g1,b1 = hex_to_rgb(hex1);
    r2,g2,b2 = hex_to_rgb(hex2);

    r = int((r1 + r2) / 2)
    g = int((g1 + g2) / 2)
    b = int((b1 + b2) / 2)

    return rgb_to_hex(r, g, b)


def pie_data_format(records):
    data = {'labels': [], 'datasets': [
        {
            'data': [],
            'backgroundColor': []
        }
    ]}
    for record in records:
        f_color = record.c_color if record.c_color else random_color_mix(PRIMARY_COLOR)
        data['labels'].append(record.c_label)
        data['datasets'][0]['data'].append(record.c_value)
        data['datasets'][0]['backgroundColor'].append(f_color)
    return data



def current_url():
    request = current.request
    return URL(request.controller, request.function, args=request.args, vars=request.vars)


def valid_account(payment):
    if payment.id_payment_opt.requires_account and not payment.account or payment.id_payment_opt.requires_account and payment.account and len(payment.account) != 4:
        return False
    return True



def precheck():
    """ user prechecks """
    auth = current.auth
    session = current.session
    request = current.request
    db = current.db

    if auth.user and not auth.user.is_client:
        # select the first store if theres only one
        if not session.store:
            stores = db(db.store.is_active == True).select()
            if len(stores) == 1:
                session.store = stores.first().id
            else:
                # store selection page
                # admin has access to all the stores
                if not auth.has_membership('Store %s' % session.store) and not auth.has_membership('Admin'):
                    redirect(URL('user', 'store_selection', vars=dict(_next=URL(request.controller, request.function, args=request.args or [], vars=request.vars or {})))
                    )