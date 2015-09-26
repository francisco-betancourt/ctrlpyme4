# -*- coding: utf-8 -*-
#
# Author: Daniel J. Ramirez

def create():
    return common_create('supplier')


def get():
    pass


def update():
    return common_update('supplier', request.args)


def delete():
    return common_delete('supplier', request.args)


def index():
    rows = common_index('supplier')
    data = None
    if rows:
        data = super_table('supplier', ['business_name'], rows)
    return locals()
