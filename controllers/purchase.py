# -*- coding: utf-8 -*-
#
# Author: Daniel J. Ramirez


import json
from decimal import Decimal as D


@auth.requires_membership('Purchases')
def create():
    """
        vars:
            is_xml: if true, then the form will accept an xml file
    """

    is_xml = request.vars.is_xml

    form = SQLFORM(db.purchase)

    if form.process().accepted:
        response.flash = 'form accepted'
        redirect(URL('fill', args=form.vars.id))
    elif form.errors:
        response.flash = 'form has errors'
    return dict(form=form)

    return common_create('purchase')



def purchase_item_formstyle(form, fields):
    form.add_class('form-inline')
    parent = FIELDSET()
    parent.append(INPUT(type='text', _class="form-control"))
    parent.append(INPUT(type='text', _class="form-control"))


    return parent


@auth.requires_membership('Purchases')
def add_purchase_item():
    """ Used to add a purchase_item to the specified purchase, this method will return a form to edit the newly created purchase item

        args:
            purchase_id
            item_id
    """

    purchase = db.purchase(request.args(0))
    item = db.item(request.args(1))
    if not purchase or not item:
        raise HTTP(404)
    purchase_item = db((db.purchase_item.id_item == item.id) &
                       (db.purchase_item.id_purchase == purchase.id)
                      ).select().first()
    if not purchase_item:
        purchase_item = db.purchase_item.insert(id_purchase=purchase.id, id_item=item.id)
        purchase_item = db.purchase_item(purchase_item)
    return locals()


@auth.requires_membership('Purchases')
def delete_purchase_item():
    """ This function removes the specified purchase item, this function actually deletes the record

        args:
            purchase_item_id
    """

    purchase_item_id = request.args(0)
    if not purchase_item_id:
        raise HTTP(400)

    db(db.purchase_item.id == purchase_item_id).delete()

    return dict(status="ok")


def postprocess_purchase_item(purchase_item):
    purchase_item.serial_numbers = purchase_item.serial_numbers.replace('_', ',') if purchase_item.serial_numbers else None
    # primitive serial number count verification
    # if purchase_item.serial_numbers:
    #     purchase_items_count = purchase_item.serial_numbers.split(',')
    #     if not purchase_items_count[-1]:
    #         purchase_items_count.pop()
    #     print len(purchase_items_count)
    # else:
    #     purchase_item.serial_numbers = None

    # recalculate the taxes.
    total_tax = 1 if purchase_item.id_item.taxes else 0
    for tax in purchase_item.id_item.taxes:
        total_tax *= tax.percentage / 100.0
    purchase_item.taxes = D(purchase_item.price or 0) * D(total_tax)
    if not purchase_item.id_item.allow_fractions:
        purchase_item.quantity = D(purchase_item.quantity).to_integral_value()
    return purchase_item


@auth.requires_membership('Purchases')
def modify_purchase_item():
    """ This functions allows the modification of a purchase item, by specifying the modified fields via url arguments.

        args:
            purchase_item_id
            param_name
            param_value
    """

    purchase_item = db.purchase_item(request.args(0))
    if not purchase_item:
        raise HTTP(404)
    try:
        purchase_item[request.args(1)] = request.args(2)

        purchase_item = postprocess_purchase_item(purchase_item)
        purchase_item.update_record()

        res = {
            'taxes': purchase_item.taxes.quantize(D('.000000'))
            , 'quantity': purchase_item.quantity
        }

        return res
    except:
        import traceback
        traceback.print_exc()
        raise HTTP(400)


@auth.requires_membership('Purchases')
def add_item_and_purchase_item():
    """ Adds the item specified by the form, then add a purchase item whose id_item is the id of the newly created item, and its id_purchase is the specified purchase

        args
            id_purchase
        vars:
            all the item form fields

    """

    purchase = db.purchase(request.args(0))
    if not purchase:
        raise HTTP(404)
    item_data = dict(request.vars)
    # change string booleans to python booleans
    item_data['has_inventory'] = True if item_data['has_inventory'] == 'true' else False
    item_data['allow_fractions'] = True if item_data['allow_fractions'] == 'true' else False
            # categories
    item_data['categories'] = [int(c) for c in item_data['categories'].split(',')] if item_data['categories'] else None
    # add the traits
    item_data['traits'] = [int(trait) for trait in item_data['traits'].split(',')] if item_data['traits'] else None
    item_data['taxes'] = [int(trait) for trait in item_data['taxes'].split(',')] if (item_data['taxes'] and item_data['taxes'] != 'null') else None

    try:
        # TODO remove when auth.
        db.item.created_by.requires = None
        db.item.modified_by.requires = None

        ret = db.item.validate_and_insert(**item_data)
        if not ret.errors:
            item = db.item(ret.id)
            url_name = "%s%s" % (urlify_string(item_data['name']), item.id)
            db.item(ret.id).update_record(url_name=url_name)

            purchase_item = db.purchase_item.insert(id_purchase=purchase.id, id_item=item.id, quantity=1)
            return dict(item=item, purchase_item=purchase_item)
        else:
            del ret.errors.created_by
            del ret.errors.modified_by
            return dict(errors=ret.errors)
    except:
        import traceback
        traceback.print_exc()


@auth.requires_membership('Purchases')
def fill():
    """ Used to add items to the specified purchase
    args:
        purchase_id

    """

    purchase = db.purchase(request.args(0))
    if not purchase:
        raise HTTP(404)

    form = SQLFORM.factory(
        Field('barcode', type="string")
        , _id="scan_form", buttons=[]
    )

    purchase_items = db(db.purchase_item.id_purchase == purchase.id).select()
    purchase_items_json = []
    for purchase_item in purchase_items:
        serials = purchase_item.serial_numbers.replace(',', ',\n') if purchase_item.serial_numbers else ''

        purchase_items_json.append({
              "id": purchase_item.id
            , "id_item": purchase_item.id_item
            , "item": { "name": purchase_item.id_item.name,
                        "barcode": item_barcode(purchase_item.id_item)
                      }
            , "quantity": str(purchase_item.quantity or 0)
            , "price": str(purchase_item.price or 0)
            , "taxes": str(purchase_item.taxes or 0)
            , "serial_numbers": serials
        })
    purchase_items_json = json.dumps(purchase_items_json)
    form[0].append(SCRIPT('purchase_items = %s;' % purchase_items_json))

    return locals()


@auth.requires_membership('Purchases')
def commit():
    """ Commits the purchase

        args:
            purchase_id
    """

    purchase = db.purchase(request.args(0))
    if not purchase:
        raise(HTTP, 404)

    # generate stocks for every purchase item
    purchase_items = db(db.purchase_item.id_purchase == purchase.id).select()
    for purchase_item in purchase_items:
        purchase_item = postprocess_purchase_item(purchase_item)
        purchase_item.update_record()
        db.stock.insert(id_store=purchase.id_store, id_purchase=purchase.id, id_item=purchase_item.id_item.id, quantity=purchase_item.quantity)
    purchase.is_done = True
    purchase.update_record()
    redirect(URL('index'))



@auth.requires_membership('Purchases')
def save():
    """ Saves the specified purchase for later use

        args:
            purchase_id
    """

    purchase = db.purchase(request.args(0))
    if not purchase:
        raise(HTTP, 404)
    redirect(URL('index'))


@auth.requires_membership('Purchases')
def get():
    pass


@auth.requires_membership('Purchases')
def update():
    """
        args:
            purchase_id
        vars:
            is_xml: if true, then the form will accept an xml file
    """

    purchase = db.purchase(request.args(0))
    if not purchase:
        raise HTTP(404)
    if purchase.is_done:
        raise HTTP(412)

    is_xml = request.vars.is_xml

    form = SQLFORM(db.purchase, purchase)

    if form.process().accepted:
        response.flash = 'form accepted'
        redirect(URL('fill', args=purchase.id))
    elif form.errors:
        response.flash = 'form has errors'
    return dict(form=form)


@auth.requires_membership('Purchases')
def delete():
    return common_delete('purchase', request.args)


def purchase_options(row):
    td = TD()
    # edit option
    if not row.is_done:
        td.append(option_btn('pencil', URL('update', args=row.id)))
    td.append(option_btn('eye-slash', onclick='delete_rows("/%s", "", "")' % (row.id)))
    return td


@auth.requires_membership('Purchases')
def index():
    rows = common_index('purchase')
    data = super_table('purchase', ['invoice_number', 'subtotal', 'total'], rows, options_function=purchase_options)
    return locals()
