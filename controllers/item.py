# -*- coding: utf-8 -*-
#
# Author: Daniel J. Ramirez

def create():

    form_fields = []

    # brand
    field = SELECT(OPTION(""))
    brands = db(db.brand.id > 0).select()
    for brand in brands:
        field.append(OPTION(brand.name))
    form_fields.append(field)

    # categories
    


    form = FORM()
    for form_field in form_fields:
        form.append(form_field)
    #
    # form = SQLFORM(db.item)
    # if form.process().accepted:
    #     response.flash = T('item added')
    #     redirect(URL('index'))
    # elif form.errors:
    #     response.flash = T('form has errors')

    return dict(form=form)


def get():
    pass


def update():
    return common_update('item', request.args)


def delete():
    return common_delete('item', request.args)


def index():
    rows = common_index('item')
    return locals()
