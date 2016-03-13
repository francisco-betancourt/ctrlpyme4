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
from uuid import uuid4
from gluon.storage import Storage


def INFO(text, btn_text=None, btn_url=None, btn_target=None):
    d = {
        'text': text
    }
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


def get_notifications():
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
                title=T("Accounts receivable"), description=T('Accounts receivable unsettled'), url=URL('account_receivable', 'index')
            ))
    if auth.has_membership('Accounts receivable'):
        accounts_p = db(db.account_receivable.is_settled == False).select()
        if accounts_r:
            notifications.append(Storage(
                title=T("Accounts payable"), description=T('Accounts payable unsettled'), url=URL('account_payable', 'index')
            ))

    return notifications

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



def get_wavg_days_in_shelf(item, id_store=None):
    q = (db.bag_item.id_bag == db.bag.id) & (db.bag_item.id_item == item)  & (db.bag_item.wavg_days_in_shelf != None)
    days = db(q).select(db.bag_item.wavg_days_in_shelf)
    if not days:
        return None
    avg_days_in_shelf = 0
    for day in days:
        avg_days_in_shelf += day.wavg_days_in_shelf
    return avg_days_in_shelf / len(days)


def item_taxes(item, price):
    total = 0
    for tax in item.taxes:
        total += (price or 0) * D((tax.percentage or 0) / 100.0)
    return DQ(total)


def item_stock(item, id_store=None, include_empty=False, id_bag=None, max_date=None):
    """ Returns all the stocks for the specified item and store, if id_store is 0 then the stocks for every store will be retrieved """

    stocks = None

    # this is something like a service, it does not have existences, so its always available
    if not item.has_inventory:
        return dict(stocks=None, quantity=float('inf'))

    if item.is_bundle:
        bundle_items = db(db.bundle_item.id_bundle == item.id).select()
        min_bundle = float('inf')
        for bundle_item in bundle_items:
            stocks, qty = item_stock(bundle_item.id_item, id_store, include_empty, id_bag).itervalues()
            min_bundle = min(min_bundle, qty / bundle_item.quantity)
        return dict(stocks=None, quantity=min_bundle)

    query = (db.stock_item.id_item == item.id)
    if id_store > 0:
        query &= db.stock_item.id_store == id_store
    if not include_empty:
        query &= db.stock_item.stock_qty > 0
    if max_date:
        query &= db.stock_item.created_on < max_date
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


def check_bag_items_integrity(bag_items, allow_out_of_stock=False):
    """ verify item stocks and remove unnecessary items """
    out_of_stock_items = []
    for bag_item in bag_items:
        # delete bag item when the item has 0 quantity
        if bag_item.quantity <= 0:
            db(db.bag_item.id == bag_item.id).delete()
        qty = item_stock(bag_item.id_item, session.store)['quantity']
        if bag_item.quantity > qty and not allow_out_of_stock:
            out_of_stock_items.append(bag_item)
    if out_of_stock_items and auth.has_membership('Employee'):
        session.flash = T('Some items are out of stock or are inconsistent')
        auto_bag_selection()
        redirection()


def get_valid_bag(id_bag, completed=False):
    try:
        query = (db.bag.id == id_bag)
        query &= db.bag.created_by == auth.user.id
        query &= db.bag.completed == completed
        if not auth.user.is_client:
            query &= db.bag.id_store == session.store
        bag = db(query).select().first()
        return bag
    except:
        import traceback as tb
        tb.print_exc()
        return None


def item_discounts(item):
    """ returns the maximum applicable discounts for the specified item """

    # get the current offer groups
    offer_groups = db((db.offer_group.starts_on < request.now) & (db.offer_group.ends_on > request.now)).select()
    if not offer_groups:
        return []

    final_query = db.discount.id < 0
    base_query = (db.discount.is_coupon == False) & (db.discount.code == '')
    for offer_group in offer_groups:
        # for every group query all applicable discounts
        query = db.discount.id_item == item.id
        if item.id_brand:
            query |= db.discount.id_brand == item.id_brand.id
        for category in item.categories:
            query |= db.discount.id_category == category.id
        query &= db.discount.id_offer_group == offer_group.id
        final_query |= query
    final_query &= base_query

    # combinable discounts
    c_discounts = db(final_query & (db.discount.is_combinable == True)).select()
    # non combinable discounts
    nc_discounts = db(final_query & (db.discount.is_combinable == False)).select()

    # calculate the sum of combinable discounts
    c_discounts_p = 0
    for c_discount in c_discounts:
        c_discounts_p += c_discount.percentage
    # get the maximum no combinable discount
    if nc_discounts:
        max_nc_discount = nc_discounts.first()
        for nc_discount in nc_discounts:
            if max_nc_discount.percentage < nc_discount.percentage:
                max_nc_discount = nc_discount
    else:
        return c_discounts
    # return the max discount
    if max_nc_discount.percentage > c_discounts_p:
        return [max_nc_discount]
    else:
        return c_discounts


def discount_data(discounts, price):
    new_price = price
    for discount in discounts:
        new_price -= new_price * D(discount.percentage / 100.0)
    return new_price, (D(1.0) - (new_price / price)) * D(100)

def apply_discount(discounts, price):
    return discount_data(discounts, price)[0]

def get_discount_percentage(bag_item):
    return (D(1) - bag_item.sale_price / (bag_item.sale_price + bag_item.discount)) * D(100)



def fix_item_price(item, price):
    """ modifies the item data based on discounts and taxes """

    new_price = price
    discounts = item_discounts(item)
    for discount in discounts:
        new_price -= new_price * DQ(discount.percentage / 100.0)
    new_price += item_taxes(item, new_price)

    item.new_price = price + item_taxes(item, price)
    discount_percentage = int((1 - (new_price / item.new_price)) * 100)
    item.new_price = str(DQ(item.new_price, True))
    item.discounted_price = str(DQ(new_price, True))
    item.discount_percentage = discount_percentage


def get_random_wallet_code():
    return str(uuid4()).split('-')[0] # is this random enough?

def new_wallet(balance=0):
    wallet_code = get_random_wallet_code()
    return db.wallet.insert(wallet_code=wallet_code, balance=balance)


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
    # admin cannot sell
    if auth.has_membership('Admin'):
        return
    # Automatic bag creation
    # check if theres a current bag
    bag_query = (db.bag.created_by == auth.user.id) & (db.bag.completed == False)
    # if the user is employee then select bags by store
    if not auth.user.is_client:
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



def _remove_stocks(item, quantity, sale_date):
    if not item.has_inventory:
        return 0, 0
    if not quantity:
        return 0, 0
    original_qty = quantity
    stock_items, quantity = item_stock(item, session.store).itervalues()
    quantity = DQ(quantity)
    total_buy_price = 0
    wavg_days_in_shelf = 0
    for stock_item in stock_items:
        if not quantity:
            return 0, 0
        stock_qty = DQ(stock_item.stock_qty) - DQ(original_qty)
        stock_item.stock_qty = max(0, stock_qty)
        stock_item.update_record()
        quantity = abs(stock_qty)

        total_buy_price += original_qty * (stock_item.price or 0)
        days_since_purchase = (sale_date - stock_item.created_on).days
        wavg_days_in_shelf += days_since_purchase
    wavg_days_in_shelf /= original_qty

    return total_buy_price, wavg_days_in_shelf


def remove_stocks(bag_items):
    for bag_item in bag_items:
        #TODO:50 implement stock removal for bag items with serial number
        if bag_item.id_item.has_serial_number:
            pass
        else:
            bag_item_total_buy_price = 0
            # when we have a bundle, we have to remove stocks for every item in the bundle. Since bundles cannot be purchased, we have to consider its average days in shelf, as the average of its bundle items weighted average days in shelf
            if bag_item.id_item.is_bundle:
                total_wavg_days_in_shelf = 0
                bundle_items_qty = 0
                bundle_items = db(db.bundle_item.id_bundle == bag_item.id_item.id).select()
                for bundle_item in bundle_items:
                    bundle_items_qty += 1
                    total_buy_price, wavg_days_in_shelf = _remove_stocks(bundle_item.id_item, bundle_item.quantity, bag_item.created_on)
                    total_wavg_days_in_shelf += wavg_days_in_shelf
                    bag_item_total_buy_price += total_buy_price
                total_wavg_days_in_shelf /= bundle_items_qty

                bag_item.total_buy_price = bag_item_total_buy_price
                bag_item.wavg_days_in_shelf = total_wavg_days_in_shelf

                bag_item.update_record()
            else:
                total_buy_price, wavg_days_in_shelf = _remove_stocks(bag_item.id_item, bag_item.quantity, bag_item.created_on)
                bag_item.total_buy_price = total_buy_price
                bag_item.wavg_days_in_shelf = wavg_days_in_shelf

                bag_item.update_record()


def reintegrate_stock(item, returned_qty, avg_buy_price, target_field, target_id):
    stock_item = db((db.stock_item[target_field] == target_id) & (db.stock_item.id_item == item.id)).select().first()
    if stock_item:
        stock_item.purchase_qty += returned_qty
        stock_item.stock_qty += returned_qty
        stock_qty.update_record()
    else:
        target_data = {target_field: target_id}
        db.stock_item.insert(id_item=item.id,
                             purchase_qty=returned_qty,
                             price=avg_buy_price,
                             stock_qty=returned_qty,
                             id_store=session.store,
                             taxes=0, **target_data
                             )
