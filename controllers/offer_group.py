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
def add_discount():
    """
        args: [id_offer_group]
        vars: [target_id, target_name, percentage, code, is_coupon, is_combinable]
    """

    offer_group = db.offer_group(request.args(0))
    if not offer_group:
        raise HTTP(404)
    print request.vars

    error = None
    msg = T('Discount added')
    target_name = request.vars.target_name
    if not target_name in ['id_item', 'id_brand', 'id_category']:
        error = T('Invalid target')
    try:
        target_id = int(request.vars.target_id)
    except:
        error = T('Invalid target')
    percentage = request.vars.percentage
    code = request.vars.code
    is_coupon = request.vars.is_coupon == 'true'
    is_combinable = request.vars.is_combinable == 'true'

    if not error:
        discount_data = {
            'id_offer_group':  offer_group.id
            , target_name: target_id
            , 'percentage': percentage
            , 'code': code
            , 'is_coupon': is_coupon
            , 'is_combinable': is_combinable
        }
        ret = db.discount.validate_and_insert(**discount_data)
        if ret.errors:
            error = T('Something went wrong')

    msg = error if error else msg
    session.info = msg
    redirect(URL('fill', args=offer_group.id));


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
