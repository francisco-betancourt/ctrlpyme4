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


# functions related to purchases


from gluon import current
from gluon.storage import Storage
from common_utils import D, DQ, remove_fractions
from datetime import date, timedelta, datetime


def new(id_store, now, user):
    db = current.db

    return db.purchase.insert(
        id_store=id_store,
        created_on=now,
        modified_on=now,
        created_by=user.id
    )


def postprocess_stock_item(stock_item):
    stock_item.serial_numbers = stock_item.serial_numbers.replace('_', ',') if stock_item.serial_numbers else None
    # primitive serial number count verification
    # if stock_item.serial_numbers:
    #     stock_items_count = stock_item.serial_numbers.split(',')
    #     if not stock_items_count[-1]:
    #         stock_items_count.pop()
    #     print len(stock_items_count)
    # else:
    #     stock_item.serial_numbers = None

    # recalculate the taxes.
    total_tax = 1 if stock_item.id_item.taxes else 0
    for tax in stock_item.id_item.taxes or []:
        total_tax *= tax.percentage / 100.0
    stock_item.taxes = D(stock_item.price or 0) * D(total_tax)
    if not stock_item.id_item.allow_fractions:
        stock_item.purchase_qty = DQ(remove_fractions(stock_item.purchase_qty))
    return stock_item


def commit(purchase):
    """ Given a purchase Row, generates stock for every stock item in associated with the purchase """

    db = current.db

    # generate stocks for every purchase item
    stock_items = db(db.stock_item.id_purchase == purchase.id).iterselect()
    for stock_item in stock_items:
        stock_item = postprocess_stock_item(stock_item)
        stock_item.stock_qty = stock_item.purchase_qty
        stock_item.id_store = purchase.id_store.id
        # set the stock quantity to the purchased quantity
        stock_item.update_record()
        # update the item prices
        item = db.item(stock_item.id_item)
        # base price should not be 0
        if stock_item.base_price > 0:
            item.base_price = stock_item.base_price
            item.price2 = stock_item.price2
            item.price3 = stock_item.price3
        item.update_record()
    purchase.is_done = True
    purchase.update_record()

    # in this case purchase is being paid with creadit so we need to create an account payable
    if purchase.id_payment_opt.credit_days > 0:
        now = purchase.modified_on
        epd = date(now.year, now.month, now.day)
        epd += timedelta(days=purchase.id_payment_opt.credit_days)
        db.account_payable.insert(id_purchase=purchase.id, epd=epd)

    return purchase
