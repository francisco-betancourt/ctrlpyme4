# -*- coding: utf-8 -*-
#
# Author: Daniel J. Ramirez

def create():
    return common_create('payment_opt')

def get():
    pass

def update():
    return common_update('payment_opt',request.args)

def delete():
    common_delete('payment_opt',request.args)

def index():
    payment_opts = db((db.payment_opt.id > 0) & (db.payment_opt.is_active == True)).select()
    return locals()
