# -*- coding: utf-8 -*-
#
# Author: Daniel J. Ramirez

import urllib
import re
from decimal import Decimal as D
import math
import json
from uuid import uuid4


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


def item_barcode(item):
    return item.sku or item.ean or item.upc


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


def item_taxes(item, price):
    total = 0
    for tax in item.taxes:
        total += (price or 0) * D((tax.percentage or 0) / 100.0)
    return DQ(total)


def item_stock(item, id_store=None, include_empty=False, id_bag=None):
    """ Returns all the stocks for the specified item and store, if id_store is 0 then the stocks for every store will be retrieved """

    stocks = None

    # this is somthing like a service, it does not have existences, so its always available
    if not item.has_inventory:
        return dict(stocks=None, quantity=1)

    if item.is_bundle:
        bundle_items = db(db.bundle_item.id_bundle == item.id).select()
        min_bundle = float('inf')
        for bundle_item in bundle_items:
            stocks, qty = item_stock(bundle_item.id_item, id_store, include_empty, id_bag).itervalues()
            min_bundle = min(min_bundle, qty / bundle_item.quantity)
        return dict(stocks=None, quantity=min_bundle)

    query = (db.stock_item.id_item == item.id)
    if id_store > 0:
        query &= (db.stock_item.id_store == id_store)
    if not include_empty:
        query &= (db.stock_item.stock_qty > 0)
    bag_item_count = 0
    if id_bag:
        # check bundle items containing the specified item
        bundles = db((db.bundle_item.id_bundle == db.bag_item.id_item)
                   & (db.bag_item.id_item == db.item.id)
                   & (db.item.is_bundle == True)
                   & (db.bag_item.id_bag == id_bag)
        ).select(db.bag_item.ALL, groupby=db.bag_item.id)
        for bundle in bundles:
            bundle_item = db((db.bundle_item.id_bundle == bundle.id_item.id) & (db.bundle_item.id_item == item.id)).select().first()
            if bundle_item:
                bag_item_count += bundle_item.quantity * bundle.quantity
        # this is the same item in bag
        bag_item = db((db.bag_item.id_item == item.id) & (db.bag_item.id_bag == id_bag) & (db.bag_item.quantity > 0)).select().first()
        bag_item_count += bag_item.quantity if bag_item else 0
    stocks = db(query).select(orderby=db.stock_item.created_on)
    if stocks:
        quantity = 0
        for stock in stocks:
            quantity += stock.stock_qty
        quantity -= bag_item_count
        return dict(stocks=stocks, quantity=quantity)
    else:
        return dict(stocks=None, quantity=0)


def new_wallet(balance=0):
    return db.wallet.insert(wallet_code=uuid4(), balance=balance)


def is_wallet(payment_opt):
    if not payment_opt:
        return False
    return payment_opt.name == 'wallet'


def get_wallet_payment_opt():
    return db(db.payment_opt.name == 'wallet').select().first()


def fix_item_quantity(item, quantity):
    """ given an item and a quantity, returns a fixed quantity based on the item allow_fraction parameter """

    quantity = max(0, quantity)  # does not allow negative quantities
    if item.allow_fractions:
        return DQ(quantity, True)
    else:
        return remove_fractions(quantity)


def json_categories_tree(item=None, selected_categories=[], visible_categories=[]):
    """ Creates a json representation of the categories tree, this representation is used with bootstrap treeview """

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


def search_query(table_name, fields, terms):
    query = (db[table_name].id < 0)
    for field in fields:
        print db[table_name][field]
        # query |= (db[table_name][field].contains(terms))



def redirection(url=None):
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



def auto_bag_selection():
    # Automatic bag creation
    # check if theres a current bag
    bag_query = (db.bag.created_by == auth.user.id) & (db.bag.completed == False)
    if auth.has_membership('Employee') or auth.has_membership('Admin') or auth.has_membership('Sales bags'):
        bag_query &= (db.bag.id_store == session.store)
    current_bag = db(bag_query).select().first()

    # create a new bag if the user does not have one
    if not current_bag:
        new_bag_id = db.bag.insert(created_by=auth.user.id, completed=False, id_store=session.store)
        current_bag = db.bag(new_bag_id)

    session.current_bag = current_bag.id


def current_url():
    return URL(request.controller, request.function, args=request.args, vars=request.vars)


def valid_account(payment):
    if payment.id_payment_opt.requires_account and not payment.account or payment.id_payment_opt.requires_account and payment.account and len(payment.account) != 4:
        return False
    return True
