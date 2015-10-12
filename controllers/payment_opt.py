# -*- coding: utf-8 -*-
#
# Author: Daniel J. Ramirez


@auth.requires_membership('Admin')
def create():
    return common_create('payment_opt')


@auth.requires_membership('Admin')
def get():
    pass


@auth.requires_membership('Admin')
def update():
    return common_update('payment_opt',request.args)


@auth.requires_membership('Admin')
def delete():
    common_delete('payment_opt',request.args)


@auth.requires_membership('Admin')
def index():
    rows = db(db.payment_opt.is_active == True).select()
    data = super_table('payment_opt', ['name', 'allow_change', 'credit_days'], rows)
    return locals()
