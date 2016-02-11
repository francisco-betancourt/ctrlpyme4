# -*- coding: utf-8 -*-
#
# Author: Daniel J. Ramirez

@auth.requires_membership('Offers')
def create():
    form = SQLFORM(db.offer_group)
    if form.process().accepted:
        redirect(URL('fill', args=form.vars.id))
    elif form.errors:
        response.flash = T('form has errors')
    return dict(form=form)


@auth.requires_membership('Offers')
def fill():
    """ args: [id_offer_group] """
    offer_group = db.offer_group(request.args(0))

    return locals()


@auth.requires_membership('Offers')
def index():
    data = super_table('offer_group', ['name'], (db.offer_group), options_function=lambda row : [option_btn('pencil', URL('fill', args=row.id))])

    return locals()
