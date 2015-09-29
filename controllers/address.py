# -*- coding: utf-8 -*-
#
# Author: Daniel J. Ramirez

def create():
    return common_create('address')

def get():
    pass

def update():
    return common_update('address',request.args)


def delete():
    common_delete('address',request.args)


def address_row(row, fields):
    address = ""
    for field in fields:
        address += row[field] + ' '
    return TR(TD(address))


def index():
    """ """

    rows = db(db.address.is_active == True).select()
    data = None
    if rows:
        data = super_table('address', ['street', 'exterior', 'interior'], rows, row_function=address_row, custom_headers=['Address'])
    return locals()
