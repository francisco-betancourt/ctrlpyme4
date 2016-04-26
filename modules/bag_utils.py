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
from item_utils import item_discounts, item_barcode, item_stock


def auto_bag_selection():
    auth = current.auth
    db = current.db
    session = current.session

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
        new_bag_id = db.bag.insert(created_by=auth.user.id, completed=False, id_store=session.store)
        current_bag = db.bag(new_bag_id)
    # in this case the user almost paid a bag but something happened and the bag state was left as BAG_ORDER_COMPLETE, so we have to set it as active
    if current_bag.status == BAG_ORDER_COMPLETE and not current_bag.is_paid and not current_bag.is_sold:
        current_bag.status = BAG_ACTIVE
        current_bag.update_record()

    session.current_bag = current_bag.id
    return current_bag


def refresh_bag_data(id_bag):
    db = current.db

    bag = db(db.bag.id == id_bag).select(for_update=True).first()
    if bag.status != BAG_ACTIVE:
        return

    bag_items = db(db.bag_item.id_bag == bag.id).select()

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
    subtotal = money_format(DQ(subtotal, True))
    taxes = money_format(DQ(taxes, True))
    total = money_format(DQ(total, True))
    quantity = DQ(quantity, True, True)

    return dict(subtotal=subtotal, taxes=taxes, total=total, quantity=quantity)


def check_bag_items_integrity(bag_items, allow_out_of_stock=False):
    """ verify item stocks and remove unnecessary items """
    session = current.session
    db = current.db

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


def check_bag_owner(id_bag):
    """ checks if the specified bag belongs to the current user """
    db = current.db
    auth = current.auth

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


def set_bag_item(bag_item, discounts=[]):
    """ modifies bag item data, in order to display it properly, this method does not modify the database """
    session = current.session

    item = bag_item.id_item
    # bag_item.name = item.name

    discount_p = DQ(1.0) - (bag_item.sale_price / (bag_item.sale_price + (bag_item.discount or 0) ))
    item.base_price -= item.base_price * discount_p
    bag_item.total_sale_price = str(DQ(bag_item.sale_price + bag_item.sale_taxes, True))
    bag_item.base_price = money_format(DQ(item.base_price, True)) if item.base_price else 0
    bag_item.price2 = money_format(DQ(item.price2 - item.price2 * discount_p, True)) if item.price2 else 0
    bag_item.price3 = money_format(DQ(item.price3 - item.price3 * discount_p, True)) if item.price3 else 0
    bag_item.sale_price = money_format(DQ(bag_item.sale_price or 0, True))

    bag_item.measure_unit = item.id_measure_unit.symbol

    bag_item.barcode = item_barcode(item)
    stocks = item_stock(item, session.store)
    bag_item.has_inventory = item.has_inventory
    bag_item.stock = stocks['quantity'] if stocks else 0
    bag_item.discount_percentage = int(discount_p * D(100.0))

    return bag_item


def bag_selection_return_format(bag):
    db = current.db

    bag_items = []
    for bag_item in db(db.bag_item.id_bag == bag.id).select():
        bag_item_modified = set_bag_item(bag_item)
        bag_items.append(bag_item_modified)
    quantity = DQ(bag.quantity, True, True)
    subtotal = money_format(DQ(bag.subtotal, True))
    taxes = money_format(DQ(bag.taxes, True))
    total = money_format(DQ(bag.total, True))

    return dict(bag=bag, bag_items=bag_items, subtotal=subtotal, total=total, taxes=taxes, quantity=quantity)


def get_valid_bag(id_bag, completed=False):
    """ Return a bag if theres a bag white the specified id, and that bag was created by the currently logged in user, and if the user is employee then it check if the bag belongs to the current store """
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
