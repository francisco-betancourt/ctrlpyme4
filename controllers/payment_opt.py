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
    data = common_index('payment_opt', ['name', 'allow_change', 'credit_days'])
    return locals()
