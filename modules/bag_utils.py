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

from common_utils import *
from constants import BAG_ACTIVE, BAG_COMPLETE, BAG_FOR_ORDER, BAG_ORDER_COMPLETE
import item_utils
from item_utils import item_discounts, item_barcode, item_stock_qty

from cp_errors import *


ALLOW_OUT_OF_STOCK = True



def new(id_store, now, user):
    """ """

    db = current.db

    return db.bag.insert(
        id_store=id_store, completed=False,
        created_on=now, modified_on=now, created_by=user.id
    )


def add_bag_item(bag, item, quantity=None, sale_price=None):
    """ """

    db = current.db

    sale_price = sale_price if sale_price else item.base_price

    bag_item = db(
          (db.bag_item.id_item == item.id)
        & (db.bag_item.id_bag == bag.id)
    ).select().first()

    # when quantity is not specified, avoid stock checking (the API user knows what he is doing)
    if not quantity:
        stock_qty = item_stock_qty(item, bag.id_store, id_bag=bag.id)
        if item.has_inventory:
            stock_qty = DQ(stock_qty)

        base_qty = base_qty = 1 if stock_qty >= 1 or ALLOW_OUT_OF_STOCK else stock_qty % 1 # modulo to consider fractionary items
        # if there is no stock notify the user
        if base_qty <= 0:
            raise CP_OutOfStockError()
        quantity = base_qty

    # create item taxes string, the string contains the tax name and its percentage, see db.py > bag_item table for more info
    if not bag_item:
        item_taxes_str = ''
        for tax in item.taxes:
            item_taxes_str += '%s:%s' % (tax.name, tax.percentage)
            if tax != item.taxes[-1]:
                item_taxes_str += ','
        discounts = item_discounts(item)
        sale_price = item_utils.discount_data(discounts, sale_price)[0]
        discount = item.base_price - sale_price
        id_bag_item = db.bag_item.insert(
            id_bag=bag.id, id_item=item.id, quantity=quantity,
            sale_price=sale_price, discount=discount,
            product_name=item.name, item_taxes=item_taxes_str,
            sale_taxes=item_utils.item_taxes(item, sale_price)
        )
        bag_item = db.bag_item(id_bag_item)
    else:
        bag_item.quantity += base_qty
        bag_item.update_record()

    return bag_item


def complete(bag):

    db = current.db
    auth = current.auth

    # delete all items with no quantity
    db(
          (db.bag_item.id_bag == bag.id)
        & ~(db.bag_item.quantity > 0)
    ).delete()

    # check if all the bag items are consistent
    bag_items = db(db.bag_item.id_bag == bag.id).iterselect()
    # delete the bag if there are no items
    if not bag_items:
        db(db.bag.id == bag.id).delete()
        raise CP_EmptyBagError()

    out_of_stock_items = out_of_stock_items_exists(bag_items, True)
    check_bag_items_integrity(bag_items, True) # allow out of stock items

    # clients create orders
    if auth.has_membership(None, bag.created_by.id, 'Clients'):
        bag.is_on_hold = True
        bag.update_record()
        return

    bag.status = BAG_COMPLETE
    bag.completed = True
    bag.update_record()
    auto_bag_selection()


def auto_bag_selection():
    auth = current.auth
    db = current.db
    session = current.session
    request = current.request

    # admin cannot sell
    if auth.has_membership('Admin'):
        return
    # Automatic bag creation

    current_bag = None
    base_bag_query = (db.bag.created_by == auth.user.id) & (db.bag.status != BAG_COMPLETE) & (db.bag.is_paid == False)
    if not auth.user.is_client:
        base_bag_query &= db.bag.id_store == session.store
    # check if the current session bag is valid
    if session.current_bag:
        session_bag_query = base_bag_query & (db.bag.id == session.current_bag)
        current_bag = db(session_bag_query).select().first()
        # check if there exist some active bag
        if not current_bag:
            current_bag = db(base_bag_query).select().first()

    # create a new bag if the user does not have one
    if not current_bag:
        new_bag_id = new(session.store, request.now, auth.user)
        current_bag = db.bag(new_bag_id)
    # in this case the user almost paid a bag but something happened and the bag state was left as BAG_ORDER_COMPLETE, so we have to set it as active
    if current_bag.status == BAG_ORDER_COMPLETE and not current_bag.is_paid and not current_bag.is_sold and auth.user.is_client:
        current_bag.status = BAG_ACTIVE
        current_bag.update_record()

    session.current_bag = current_bag.id
    return current_bag


def refresh_bag_data(id_bag):
    db = current.db

    bag = db(db.bag.id == id_bag).select(for_update=True).first()
    if bag.status != BAG_ACTIVE:
        return

    bag_items = db(db.bag_item.id_bag == bag.id).iterselect()

    subtotal = D(0)
    taxes = D(0)
    total = D(0)
    quantity = D(0)
    reward_points = 0
    for bag_item in bag_items:
        subtotal += bag_item.sale_price * bag_item.quantity
        taxes += bag_item.sale_taxes * bag_item.quantity
        total += (bag_item.sale_taxes + bag_item.sale_price) * bag_item.quantity
        quantity += bag_item.quantity
        reward_points += bag_item.id_item.reward_points or 0

    bag.update_record(subtotal=DQ(subtotal), taxes=DQ(taxes), total=DQ(total), quantity=quantity, reward_points=DQ(reward_points))

    quantity = DQ(quantity, True, True)

    return dict(subtotal=subtotal, taxes=taxes, total=total, quantity=quantity)


def out_of_stock_items_exists(bag_items, allow_out_of_stock):
    if allow_out_of_stock:
        return False

    for bag_item in bag_items:
        qty = item_stock_qty(bag_item.id_item, bag_item.id_bag.id_store.id)
        if bag_item.quantity > qty:
            return True

    return False



def check_bag_items_integrity(bag_items, allow_out_of_stock=False):
    """ verify item stocks and remove unnecessary items """
    session = current.session
    db = current.db

    out_of_stock_items = []
    for bag_item in bag_items:
        # delete bag item when the item has 0 quantity
        if bag_item.quantity <= 0:
            db(db.bag_item.id == bag_item.id).delete()
        qty = item_stock_qty(bag_item.id_item, session.store)
        if bag_item.quantity > qty and not allow_out_of_stock:
            out_of_stock_items.append(bag_item)
    if out_of_stock_items and auth.has_membership('Employee'):
        session.flash = T('Some items are out of stock or are inconsistent')
        auto_bag_selection()
        redirection()


def check_bag_owner(id_bag):
    """ checks if the specified bag belongs to the current user """
    db = current.db
    auth = current.auth
    session = current.session

    query = (db.bag.id == id_bag)
    query &= db.bag.created_by == auth.user.id
    if not auth.user.is_client:
        query &= db.bag.id_store == session.store
    bag = db(query).select().first()
    if not bag:
        raise HTTP(403)
    return bag


def is_modifiable_bag(id_bag):
    """ if the bag is not modifiable then this function will raise an exception (HTTP 403 status code), the function will return the bag in other case. Conditions for a bag to be modifiable:

        * must be owned by the user who wants to update
        * must have status BAG_ACTIVE
        * must not be paid
        * must belong to the current user store, if the user is a employee
    """
    auth = current.auth
    db = current.db
    session = current.session

    query = (db.bag.id == id_bag)
    query &= db.bag.created_by == auth.user.id
    query &= db.bag.status == BAG_ACTIVE
    query &= db.bag.is_paid == False
    if not auth.user.is_client:
        query &= db.bag.id_store == session.store
    bag = db(query).select().first()
    if not bag:
        raise HTTP(403)
    return bag


def is_complete_bag(id_bag):
    db = current.db
    session = current.session

    bag = db((db.bag.status == BAG_COMPLETE) & (db.bag.id == id_bag) & (db.bag.id_store == session.store)).select().first()
    if not bag:
        raise HTTP(404)
    return dict(bag=bag)


def bag_item_taxes(bag_item, price):
    """ calculates the bag items taxes using the bag item taxes string """
    total = 0
    try:
        for tax_percentage in map(lambda x : int(x.split(':')[1]), bag_item.item_taxes.split(',')):
            total += (price or 0) * D((tax_percentage or 0) / 100.0)
        return DQ(total)
    except:
        return D(0)


def set_bag_item(bag_item, discounts=[]):
    """ modifies bag item data, in order to display it properly, this method does not modify the database """
    session = current.session

    item = bag_item.id_item

    # stores the price without discounts
    real_price = bag_item.sale_price + (bag_item.discount or 0)
    # discount percentage
    discount_p = 0
    try:
        discount_p = DQ(1.0) - bag_item.sale_price / real_price
    except:
        pass
    item.base_price -= item.base_price * discount_p

    bag_item.total_sale_price = str(DQ(bag_item.sale_price + bag_item.sale_taxes, True))
    bag_item.base_price = money_format(DQ(item.base_price, True)) if item.base_price else 0
    bag_item.price2 = money_format(DQ(item.price2 - item.price2 * discount_p, True)) if item.price2 else 0
    bag_item.price3 = money_format(DQ(item.price3 - item.price3 * discount_p, True)) if item.price3 else 0
    bag_item.sale_price = money_format(DQ(bag_item.sale_price or 0, True))


    # add taxes without discounts
    real_price += bag_item_taxes(bag_item, real_price)
    bag_item.price_no_discount = real_price

    bag_item.measure_unit = item.id_measure_unit.symbol

    bag_item.barcode = item_barcode(item)
    bag_item.stock = item_stock_qty(item, session.store)
    bag_item.has_inventory = item.has_inventory
    bag_item.discount_percentage = int(discount_p * D(100.0))
    bag_item.real_price = bag_item.sale_price

    return bag_item


def bag_selection_return_format(bag):
    db = current.db

    bag_items = []
    real_total = 0
    for bag_item in db(db.bag_item.id_bag == bag.id).select():
        bag_item_modified = set_bag_item(bag_item)
        bag_items.append(bag_item_modified)
        real_total += bag_item.price_no_discount
    quantity = DQ(bag.quantity, True, True)

    return dict(bag=bag, bag_items=bag_items, subtotal=bag.subtotal, total=bag.total, taxes=bag.taxes, quantity=quantity, real_total=real_total)


def get_valid_bag(id_bag, completed=False):
    """ Return a bag if theres a bag with the specified id, and that bag was created by the currently logged in user, and if the user is employee then it check if the bag belongs to the current store """
    db = current.db
    auth = current.auth
    session = current.session

    try:
        query = (db.bag.id == id_bag)
        query &= db.bag.created_by == auth.user.id
        # query &= db.bag.completed == completed
        query &= db.bag.status == BAG_COMPLETE if completed else db.bag.status == BAG_ACTIVE
        if not auth.user.is_client:
            query &= db.bag.id_store == session.store
        bag = db(query).select().first()
        return bag
    except:
        import traceback as tb
        tb.print_exc()
        return None



def get_ordered_items_count(id_order, id_item):
    """ """

    db = current.db
    session = current.session

    q_sum = db.bag_item.quantity.sum()
    order_items_qty = db(
          (db.sale_order.id_bag == db.bag.id)
        & (db.bag_item.id_bag == db.bag.id)
        & (db.sale_order.id < id_order)
        & (db.sale_order.is_active == True)
        & (db.sale_order.id_sale == None)
        & (db.sale_order.id_store == session.store)
        & (db.bag_item.id_item == id_item)
    ).select( q_sum ).first()[q_sum] or 0

    return order_items_qty
