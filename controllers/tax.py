# -*- coding: utf-8 -*-
#
# Author: Daniel J. Ramirez

def create():
    return common_create('tax')


def get():
    pass

def update():
    return common_update('tax', request.args)


def delete():
    common_delete('tax', request.args)


def index():
    taxes = common_index('tax')
    data = data = super_table('tax', ['name', 'percentage', 'symbol'], taxes)

    return locals()
