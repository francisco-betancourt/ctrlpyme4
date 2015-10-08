# -*- coding: utf-8 -*-
#
# Author: Daniel J. Ramirez

def create():
    return common_create('sale')


def get():
    pass


def update():
    return common_update('sale', request.args)


def delete():
    return common_delete('sale', request.args)


def index():
    rows = common_index('sale')
    data = super_table('sale', ['consecutive', 'subtotal', 'total'], rows)
    return locals()
