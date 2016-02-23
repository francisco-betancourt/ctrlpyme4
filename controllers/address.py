# -*- coding: utf-8 -*-
#
# Author: Daniel J. Ramirez

@auth.requires_membership('Admin')
def create():
    form = SQLFORM(db.address)
    if form.process().accepted:
        response.flash = T('form accepted')
        if request.vars._next:
            request.vars._next += '/%s' % form.vars.id
        redirection()
    elif form.errors:
        response.flash = T('form has errors')
    return dict(form=form)


@auth.requires_membership('Admin')
def get():
    pass

@auth.requires_membership('Admin')
def update():
    return common_update('address',request.args)


@auth.requires_membership('Admin')
def delete():
    common_delete('address',request.args)


@auth.requires_membership('Admin')
def address_row(row, fields):
    address = ""
    for field in fields:
        address += row[field] + ' '
    return TR(TD(address))


@auth.requires_membership('Admin')
def index():
    """ """

    data = common_index('address', ['street', 'exterior', 'interior'], dict(row_function=address_row, custom_headers=['Address']))
    return locals()
