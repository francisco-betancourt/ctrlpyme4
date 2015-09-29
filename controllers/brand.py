# -*- coding: utf8 -*-

def create():
    return common_create('brand')

def update():
    return common_update('brand',request.args)

def delete():
    common_delete('brand',request.args)

def index():
    rows = db(db.brand.is_active == True).select()
    data = None
    if rows:
        data = super_table('brand', ['name'], rows)
    return locals()
