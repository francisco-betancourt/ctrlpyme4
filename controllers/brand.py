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
    data = common_index('brand', ['name'])
    return locals()
