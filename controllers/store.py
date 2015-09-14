# -*- coding: utf-8 -*-
#
# Author: Daniel J. Ramirez

def create():
    return common_create('store')


def get():
    store = db.store(request.args(0))
    if not store:
        raise HTTP(404, T('Store NOT FOUND'))

    # store_roles = db(db.store_role.id_store == store.id).select()
    store_config = db(db.store_config.id_store == store.id).select()
    store_roles = db(db.store_role.id_store == store.id).select()
    return locals()


def update():
    return common_update('store', request.args, _vars=request.vars)


def delete():
    return common_delete('store', request.args)


def index():
    stores = common_index('store')
    return locals()
