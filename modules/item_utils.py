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
from gluon import current

from common_utils import *


def item_barcode(item):
    return item.sku or item.ean or item.upc


def get_wavg_days_in_shelf(item, id_store=None):
    db = current.db
    q = (db.bag_item.id_bag == db.bag.id) & (db.bag_item.id_item == item)  & (db.bag_item.wavg_days_in_shelf != None)
    if id_store:
        q &= db.bag.id_store == id_store
    days = db(q).select(db.bag_item.wavg_days_in_shelf)
    if not days:
        return None
    avg_days_in_shelf = 0
    for day in days:
        avg_days_in_shelf += day.wavg_days_in_shelf
    return avg_days_in_shelf / len(days)


def item_url(_name, _id):
    url_name = "%s%s" % (urlify_string(_name), _id)
    return url_name


def item_taxes(item, price):
    total = 0
    for tax in item.taxes:
        total += (price or 0) * D((tax.percentage or 0) / 100.0)
    return DQ(total)


def item_stock(item, id_store=None, include_empty=False, id_bag=None, max_date=None):
    """ Returns all the stocks for the specified item and store, if id_store is 0 then the stocks for every store will be retrieved """

    db = current.db
    stocks = None

    # this is something like a service, it does not have existences, so its always available
    if not item.has_inventory:
        return dict(stocks=None, quantity=2**64) # hack since theres a problem including float('inf')

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



def item_discounts(item):
    """ returns the maximum applicable discounts for the specified item """
    db = current.db
    request = current.request

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

    price = D(0) if not price else price
    new_price = price
    discounts = item_discounts(item)
    for discount in discounts:
        new_price -= new_price * DQ(discount.percentage / 100.0)
    new_price += item_taxes(item, new_price)

    item.new_price = (price or 0) + item_taxes(item, price)
    discount_percentage = 0
    try:
        # unable to calculate discount percentage with new price 0
        discount_percentage = int((1 - (new_price / item.new_price)) * 100)
    except:
        pass
    item.new_price = str(DQ(item.new_price, True))
    item.discounted_price = str(DQ(new_price, True))
    item.discount_percentage = discount_percentage



def fix_item_quantity(item, quantity):
    """ given an item and a quantity, returns a fixed quantity based on the item allow_fraction parameter """

    quantity = max(0, quantity)  # does not allow negative quantities
    if item.allow_fractions:
        return DQ(quantity, True)
    else:
        return remove_fractions(quantity)


def active_item(item_id):
    db = current.db
    return db((db.item.id == item_id) & (db.item.is_active == True)).select().first()


# def get_popular_items(start_date=None, end_date=None, amount=10, id_store=None):
#     db = current.db
#
#     """ Naive method to get the most bagged items """
#     q_sum = db.bag_item.quantity.sum()
#     data = []
#     for item in db(db.item.is_active == True).select():
#         query = db.bag_item.id_bag == db.bag.id
#         query &= db.bag_item.id_item == item.id
#         if start_date:
#             query &= db.bag_item.created_on >= start_date
#         if end_date:
#             query &= db.bag_item.created_on <= end_date
#         if id_store:
#             query &= db.bag.id_store == id_store
#         counter = db(query).select(q_sum).first()[q_sum] or 0
#         data.append((item, counter))
#     data.sort(key=lambda tup: tup[1], reverse=True)
#     data = data[:amount]
#     data = [d[0] for d in data[:amount]] # remove counter
#     return data



def _remove_stocks(item, quantity, sale_date):
    """ remove the specified item quantity from available stocks """
    session = current.session

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
    """ Remove stocks for all the bag items specified """
    db = current.db

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
    db = current.db

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
