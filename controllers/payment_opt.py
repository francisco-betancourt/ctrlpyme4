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
    rows = db(db.payment_opt.is_active == True).select()
    data = super_table('payment_opt', ['name', 'allow_change', 'credit_days'], rows)
    return locals()
