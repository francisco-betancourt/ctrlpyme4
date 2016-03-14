# -*- coding: utf-8 -*-
#
# Author: Daniel J. Ramirez


@auth.requires_membership('Items management')
def create():
    return common_create('trait_category')


@auth.requires_membership('Items management')
def get():
    trait_category = db.trait_category(request.args(0))
    redirect(URL('trait', 'index', vars={'trait_category': trait_category.id}))


@auth.requires_membership('Items management')
def update():
    return common_update('trait_category', request.args)


@auth.requires_membership('Items management')
def delete():
    return common_delete('trait_category', request.args)


@auth.requires_membership('Items management')
def index():
    data = common_index('trait_category', ['name'], dict(options_func=lambda row: supert_default_options(row) + (OPTION_BTN('details', URL('get', args=row.id)),) ) )
    return locals()
