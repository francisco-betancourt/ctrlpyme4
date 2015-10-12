# -*- coding: utf8 -*-

@auth.requires_membership('Items management')
def create():
    return common_create('brand')


@auth.requires_membership('Items management')
def update():
    return common_update('brand',request.args)


@auth.requires_membership('Items management')
def delete():
    common_delete('brand',request.args)


@auth.requires_membership('Items management')
def index():
    rows = db(db.brand.is_active == True).select()
    data = None
    if rows:
        data = super_table('brand', ['name'], rows)
    return locals()
