# -*- coding: utf-8 -*-
#
# Author: Daniel J. Ramirez

@auth.requires_membership('Offers')
def create():
    form = SQLFORM(db.offer_group)
    if form.process().accepted:
        offer_group = db.offer_group(form.vars.id)
        # only admin can create global offers
        if not auth.has_membership('Admin') and offer_group.id_store == None:
            offer_group.id_store = session.store
            offer_group.update_record()

        redirect(URL('fill', args=form.vars.id))
    elif form.errors:
        response.flash = T('form has errors')
    return dict(form=form)


@auth.requires_membership('Offers')
def delete_discount():
    """ args: [id_discount] """

    discount = db.discount(request.args(0))
    if not discount:
        raise HTTP(404)
    discount.delete_record()

    redirect(URL('fill', args=discount.id_offer_group.id))


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

    categories_data_script = SCRIPT("var categories_tree_data = %s" % json_categories_tree())

    return locals()


@auth.requires_membership('Offers')
def update():
    return common_update('offer_group', request.args)


def get():
    """ args: [id_offer_group]"""

    offer_group = db.offer_group(request.args(0))
    if not offer_group:
        raise HTTP(404)

    discounts = db((db.discount.id_offer_group == offer_group.id)
                 & (db.discount.is_coupon == False)
                 & (db.discount.code == '')
                 ).select()

    query = (db.item.id < 0)
    for discount in discounts:
        if discount.id_item:
            query |= (db.item.id == discount.id_item.id)
        if discount.id_brand:
            query |= (db.item.id_brand == discount.id_brand.id)
        if discount.id_category:
            query |= (db.item.categories.contains(discount.id_category.id))
    pages, limits = pages_menu(query, request.vars.page, request.vars.ipp, distinct=db.item.name)
    items = db(query).select(limitby=limits)

    return locals()


def dates_custom_format(row, subfields):
    return '%s - %s' % (row[subfields[0]], row[subfields[1]])


@auth.requires_membership('Offers')
def index():
    def offer_options(row):
        return supert_default_options(row) + (OPTION_BTN('local_offer', URL('fill', args=row.id)), )
    title = T('offer groups')
    offers_query = (db.offer_group.is_active == True)
    if not auth.has_membership('Admin'):
        offers_query &= db.offer_group.id_store == session.store
    data = SUPERT(offers_query, fields=[
        'name', 'starts_on', 'ends_on'
    ], options_func=offer_options)

    return locals()
