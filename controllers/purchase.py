# -*- coding: utf-8 -*-
#
# Author: Daniel J. Ramirez


import json


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


def delete_purchase_item():
    """ This function removes the specified purchase item

        args:
            purchase_item_id
    """

    purchase_item_id = request.args(0)
    if not purchase_item_id:
        raise HTTP(400)

    db(db.purchase_item.id == purchase_item_id).delete()

    return dict(status="ok")


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
        purchase_item.update_record()
    except:
        raise HTTP(400)


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
        purchase_items_json.append({
              "id": purchase_item.id
            , "id_item": purchase_item.id_item
            , "item": { "name": purchase_item.id_item.name,
                        "barcode": item_barcode(purchase_item.id_item)
                      }
            , "quantity": str(purchase_item.quantity or 0)
            , "price": str(purchase_item.price or 0)
            , "taxes": str(purchase_item.taxes or 0)
        })
    purchase_items_json = json.dumps(purchase_items_json)
    form[0].append(SCRIPT('purchase_items = %s;' % purchase_items_json))

    return locals()


def get():
    pass


def update():
    return common_update('purchase', request.args)


def delete():
    return common_delete('purchase', request.args)


def index():
    rows = common_index('purchase')
    data = super_table('purchase', ['invoice_number', 'subtotal', 'total'], rows)
    return locals()
