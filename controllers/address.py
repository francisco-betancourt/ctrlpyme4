# -*- coding: utf-8 -*-
#
# Author: Daniel J. Ramirez

@auth.requires(auth.has_membership('Admin') or auth.has_membership('Manager'))
def create():
    return common_create('address')

@auth.requires(auth.has_membership('Admin') or auth.has_membership('Manager'))
def get():
    pass

@auth.requires(auth.has_membership('Admin') or auth.has_membership('Manager'))
def update():
    return common_update('address',request.args)


@auth.requires(auth.has_membership('Admin') or auth.has_membership('Manager'))
def delete():
    common_delete('address',request.args)


@auth.requires(auth.has_membership('Admin') or auth.has_membership('Manager'))
def address_row(row, fields):
    address = ""
    for field in fields:
        address += row[field] + ' '
    return TR(TD(address))


@auth.requires(auth.has_membership('Admin') or auth.has_membership('Manager'))
def index():
    """ """

    data = common_index('address', ['street', 'exterior', 'interior'], dict(row_function=address_row, custom_headers=['Address']))
    return locals()
