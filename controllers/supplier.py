# -*- coding: utf-8 -*-
#
# Author: Daniel J. Ramirez

@auth.requires(
       auth.has_membership('Purchases')
    or auth.has_membership('Admin')
    or auth.has_membership('Manager')
)
def create():
    return common_create('supplier')


@auth.requires(
       auth.has_membership('Purchases')
    or auth.has_membership('Admin')
    or auth.has_membership('Manager')
)
def get():
    pass


@auth.requires(
       auth.has_membership('Purchases')
    or auth.has_membership('Admin')
    or auth.has_membership('Manager')
)
def update():
    return common_update('supplier', request.args)


@auth.requires(
       auth.has_membership('Purchases')
    or auth.has_membership('Admin')
    or auth.has_membership('Manager')
)
def delete():
    return common_delete('supplier', request.args)


@auth.requires(
       auth.has_membership('Purchases')
    or auth.has_membership('Admin')
    or auth.has_membership('Manager')
)
def index():
    rows = common_index('supplier')
    data = data = super_table('supplier', ['business_name'], rows)
    return locals()
