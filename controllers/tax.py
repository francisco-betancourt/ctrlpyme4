# -*- coding: utf-8 -*-
#
# Author: Daniel J. Ramirez

@auth.requires(auth.has_membership('Admin') or auth.has_membership('Manager'))
def create():
    return common_create('tax')


@auth.requires(auth.has_membership('Admin') or auth.has_membership('Manager'))
def get():
    pass

@auth.requires(auth.has_membership('Admin') or auth.has_membership('Manager'))
def update():
    return common_update('tax', request.args)


@auth.requires(auth.has_membership('Admin') or auth.has_membership('Manager'))
def delete():
    common_delete('tax', request.args)


@auth.requires(auth.has_membership('Admin') or auth.has_membership('Manager'))
def index():
    taxes = common_index('tax')
    data = data = super_table('tax', ['name', 'percentage', 'symbol'], taxes)

    return locals()
