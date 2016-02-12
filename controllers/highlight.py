# -*- coding: utf-8 -*-
#
# Author: Daniel J. Ramirez

def create():
    return common_create('highlight')


def update():
    return common_update('highlight', request.args)


def delete():
    return common_delete('highlight', request.args)


def index():
    data = common_index('highlight', ['title'], super_table_vars=dict())
    return locals()
