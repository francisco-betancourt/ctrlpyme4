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

def index():
    """ """
    addresses = db(db.address.is_active == True).select()
    return locals()
