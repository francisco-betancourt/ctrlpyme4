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
import os
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
        v = D(value or 0)
        return v.quantize(D(1)) if v == v.to_integral() else v.normalize()
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


def json_categories_tree(
    item=None, selected_categories=None, visible_categories=None
):
    """ Creates a json representation of the categories tree, this representation is used with bootstrap treeview """
    db = current.db

    if selected_categories is None:
        selected_categories = []
    if visible_categories is None:
        visible_categories = []

    subs = db(
        (db.category.is_active == True)
        & (db.category.parent != None)
    ).select(orderby=~db.category.parent).as_list()
    parents = db(
        (db.category.is_active == True)
        & (db.category.parent == None)
    ).select().as_list()
    categories = subs + parents
    if len(categories) == 0:
        return []
    current_category = categories[0]['parent']
    categories_children = {}
    current_tree = []
    categories_selected_text = ""
    for category in categories:
        category = Storage(category)
        if category.parent != current_category:
            categories_children[current_category] = current_tree
            current_tree = []
            current_category = category.parent
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
            del categories_children[category.id]
        else:
            current_tree.append(child)
    # json object from python dict
    # current_tree contains the tree.
    categories_tree = json.dumps(current_tree)
    del current_tree
    if item:
        item.categories_selected_text = categories_selected_text

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


def full_address(address):
    return "%s %s %s %s %s %s %s %s" % (address.street, address.exterior, address.interior, address.neighborhood, address.city, address.municipality, address.state_province, address.postal_code)


def current_url():
    request = current.request
    return URL(request.controller, request.function, args=request.args, vars=request.vars)


def valid_account(payment):
    if payment.id_payment_opt.requires_account and not payment.account or payment.id_payment_opt.requires_account and payment.account and len(payment.account) != 4:
        return False
    return True



def select_store(only_auto_select=False):
    """ Goes to store selection screen if there are multiple stores, and
        auto selects the only store in other case, use only_auto_select
        to avoid going to store_selection page and just auto select when only
        one store is available
    """

    auth = current.auth
    session = current.session
    request = current.request
    db = current.db

    if not auth.user or auth.user.is_client or session.store:
        return

    q = (db.store.id < 0)
    store_memberships = db(
        (db.auth_membership.group_id == db.auth_group.id) &
        (db.auth_membership.user_id == auth.user.id) &
        (db.auth_group.role.like('Store %'))
    ).iterselect(db.auth_group.role)
    for store_membership in store_memberships:
        store_id = int(store_membership.role.split(' ')[1])
        q |= db.store.id == store_id
    stores = db((q) & (db.store.is_active == True)).select()

    if len(stores) == 1:
        session.store = stores.first().id
    elif not only_auto_select:
        redirect(URL('user', 'store_selection', vars=dict(_next=URL(request.controller, request.function, args=request.args or [], vars=request.vars or {})))
        )

    return


def precheck():
    """ user prechecks """
    auth = current.auth
    session = current.session
    request = current.request
    db = current.db

    select_store()


def css_path(file_name):
    request = current.request
    return os.path.join(request.folder, 'static/css/%s' % file_name)

def js_path(file_name):
    request = current.request
    return os.path.join(request.folder, 'static/js/%s' % file_name)


def time_interval_query(tablename, start_date, end_date):
    db = current.db
    return (db[tablename].created_on >= start_date) & (db[tablename].created_on < end_date)


def host_base_url():
    """ Returns the app base url """

    return URL('', '', host=True).split('/' + request.controller)[0]


# def error_dict(msg)
