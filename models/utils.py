# -*- coding: utf-8 -*-
#
# Author: Daniel J. Ramirez

import urllib
import re
from decimal import Decimal as D
import math


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
    taxes = 1 if item.taxes else 0
    for tax in item.taxes:
        taxes *= tax.percentage / 100.0
    return DQ(D(price) * D(taxes))


def item_stock(item, id_store):
    """ Returns all the stocks for the specified item and store, if id_store is 0 then the stocks for every store will be retrieved """

    stocks = None
    if id_store > 0:
        stocks = db((db.stock_item.id_item == item.id)
                  & (db.stock_item.id_store == id_store)
                  & (db.stock_item.stock_qty > 0)
                  ).select(orderby=db.stock_item.created_on)
    else:
        stocks = db((db.stock_item.id_item == item.id)
                  & (db.stock_item.stock_qty > 0)
                   ).select(orderby=db.stock_item.created_on)
    if stocks:
        quantity = 0
        for stock in stocks:
            quantity += stock.quantity
        return dict(stocks=stocks, quantity=quantity)
    else:
        return dict(stocks=None, quantity=0)
