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
def add_item_discount():
    """ args: [id_offer_group] """
    offer_group = db.offer_group(request.args(0))

    return dict()


@auth.requires_membership('Offers')
def fill():
    """ args: [id_offer_group] """
    offer_group = db.offer_group(request.args(0))

    # get all offers
    discounts = db(db.discount.id_offer_group == offer_group.id).select()

    # item_discount_form = SQLFORM(db.item_discount)
    # item_discount_form.vars.id_offer_group = offer_group.id
    # if item_discount_form.process().accepted:
    #     response.flash = T('Discount added')
    # elif item_discount_form.errors:
    #     response.flash = T('form has errors')

    return locals()


@auth.requires_membership('Offers')
def index():
    data = super_table('offer_group', ['name'], (db.offer_group), options_function=lambda row : [option_btn('pencil', URL('fill', args=row.id))])

    return locals()
