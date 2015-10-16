# -*- coding: utf-8 -*-
#
# Author: Daniel J. Ramirez

import urllib
import re
from decimal import Decimal as D


rmap = {  'á': 'a', 'Á': 'a' , 'é': 'e', 'É': 'e' , 'í': 'i', 'Í': 'i'
        , 'ó': 'o', 'Ó': 'o' , 'ú': 'u', 'Ú': 'u'
       }
def replace_match(match):
    key = match.group(0)
    print key
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


def DQ(value):
    return D(value).quantize(D('.000000'))


def item_taxes(item, price):
    taxes = 1
    for tax in item.taxes:
        taxes *= tax.percentage / 100.0
    return DQ(D(price) * D(taxes))
