# -*- coding: utf-8 -*-
#
# Author: Daniel J. Ramirez

def create():
    return common_create('trait_category')


def get():
    trait_category = db.trait_category(request.args(0))
    redirect(URL('trait', 'index', vars={'trait_category': trait_category.id}))


def update():
    return common_update('trait_category', request.args)


def delete():
    return common_delete('trait_category', request.args)


def index():
    rows = common_index('trait_category')
    data = super_table('trait_category', ['name'], rows, extra_options=lambda row: [option_btn('', URL('get', args=row.id), 'View')])
    return locals()
