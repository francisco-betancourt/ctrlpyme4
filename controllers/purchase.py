# -*- coding: utf-8 -*-
#
# Author: Daniel J. Ramirez


import json
from decimal import Decimal as D


# #TODO:40 implement XML purchase
@auth.requires_membership('Purchases')
def create():
    """
        vars:
            is_xml: if true, then the form will accept an xml file
    """

    is_xml = request.vars.is_xml == 'True'
    new_purchase_id = db.purchase.insert(id_store=session.store)
    if not is_xml:
        redirect(URL('fill', args=new_purchase_id))


@auth.requires_membership('Purchases')
def create_from_order():
    """ Given a sale order, creates a purchase and adds all the order missing items to the purchase

        args: [id_order]
    """

    order = db.sale_order(request.args(0))
    if not order:
        raise HTTP(404)
    missing_items = []

    # check if the order items are in stock
    for bag_item in db(db.bag_item.id_bag == order.id_bag.id).select():
        stock, quantity = item_stock(bag_item.id_item, session.store).itervalues()
        item_ready = (quantity >= bag_item.quantity)
        if not item_ready:
            # if the item is a bundle add the contained items to the purchase
            if bag_item.id_item.is_bundle:
                for bundle_item in db((db.bundle_item.id_bundle == bag_item.id_item.id)).select():
                    stock, qty = item_stock(bundle_item.id_item, session.store).itervalues()
                item_ready = (quantity >= bag_item.quantity * bundle_item.quantity)
                if not item_ready:
                    missing_items.append(
                        dict(
                            qty=(bag_item.quantity * bundle_item.quantity) - qty
                            , item=bundle_item.id_item
                        )
                    )
            else:
                missing_items.append(dict(item=bag_item.id_item, qty=bag_item.quantity - quantity))

    if missing_items:
        new_purchase = db.purchase.insert(id_store=session.store)
        for missing_item in missing_items:
            db.stock_item.insert(id_purchase=new_purchase, id_credit_note=None, id_inventory=None, id_store=session.store, purchase_qty=missing_item['qty'], id_item=missing_item['item'].id, base_price=missing_item['item'].base_price, price2=missing_item['item'].price2, price3=missing_item['item'].price3)

    redirect(URL('fill', args=new_purchase, vars=dict(is_xml=False)))



def stock_item_formstyle(form, fields):
    form.add_class('form-inline')
    parent = FIELDSET()
    parent.append(INPUT(type='text', _class="form-control"))
    parent.append(INPUT(type='text', _class="form-control"))


    return parent


def response_stock_item(stock_item):
    """ Returns relevant stock_item information """

    serials = stock_item.serial_numbers.replace(',', ',\n') if stock_item.serial_numbers else ''
    res = {
          "id": stock_item.id
        , "id_item": stock_item.id_item
        , "item": { "name": stock_item.id_item.name,
                    "barcode": item_barcode(stock_item.id_item)
                  }
        , "purchase_qty": str(stock_item.purchase_qty or 0)
        , "price": str(DQ(stock_item.price or 0))
        , "base_price": str(DQ(stock_item.base_price or 0))
        , "price2": str(DQ(stock_item.price2 or 0))
        , "price3": str(DQ(stock_item.price3 or 0))
        , "taxes": str(DQ(stock_item.taxes) or 0)
        , "serial_numbers": serials
    }

    return res


@auth.requires_membership('Purchases')
def add_stock_item():
    """ Used to add a stock_item to the specified purchase, this method will return a form to edit the newly created purchase item

        args:
            purchase_id
            item_id
    """

    try:
        purchase = db.purchase(request.args(0))
        item = db.item(request.args(1))
        if not purchase or not item:
            raise HTTP(404)
        if purchase.is_done:
            raise HTTP(405)
        if item.is_bundle or not item.has_inventory:
            raise HTTP(403)
        stock_item = db((db.stock_item.id_item == item.id) &
                           (db.stock_item.id_purchase == purchase.id)
                          ).select().first()
        if not stock_item:
            stock_item = db.stock_item.insert(id_purchase=purchase.id, id_item=item.id, base_price=item.base_price, price2=item.price2, price3=item.price3, purchase_qty=1)
            stock_item = db.stock_item(stock_item)
            stock_item = response_stock_item(stock_item)
        # else:
        #     stock_item.purchase_qty += 1
        #     stock_item.update_record()
        return locals()
    except:
        import traceback
        traceback.print_exc()


@auth.requires_membership('Purchases')
def delete_stock_item():
    """ This function removes the specified stock item, this function actually deletes the record

        args:
            stock_item_id
    """

    stock_item_id = request.args(0)
    if not stock_item_id:
        raise HTTP(400)

    db(db.stock_item.id == stock_item_id).delete()

    return dict(status="ok")


def postprocess_stock_item(stock_item):
    stock_item.serial_numbers = stock_item.serial_numbers.replace('_', ',') if stock_item.serial_numbers else None
    # primitive serial number count verification
    # if stock_item.serial_numbers:
    #     stock_items_count = stock_item.serial_numbers.split(',')
    #     if not stock_items_count[-1]:
    #         stock_items_count.pop()
    #     print len(stock_items_count)
    # else:
    #     stock_item.serial_numbers = None

    # recalculate the taxes.
    total_tax = 1 if stock_item.id_item.taxes else 0
    for tax in stock_item.id_item.taxes:
        total_tax *= tax.percentage / 100.0
    stock_item.taxes = D(stock_item.price or 0) * D(total_tax)
    if not stock_item.id_item.allow_fractions:
        stock_item.purchase_qty = DQ(remove_fractions(stock_item.purchase_qty))
    return stock_item


@auth.requires_membership('Purchases')
def modify_stock_item():
    """ This functions allows the modification of a stock item, by specifying the modified fields via url arguments.

        args:
            stock_item_id
            param_name
            param_value
    """

    stock_item = db.stock_item(request.args(0))
    if not stock_item:
        raise HTTP(404)
    if stock_item.id_purchase.is_done:
        raise HTTP(405)
    try:
        param_name = request.args(1)
        param_value = request.args(2)

        if param_name in ['purchase_qty', 'price', 'serial_numbers', 'base_price', 'price2', 'price3']:
            stock_item[param_name] = param_value
            stock_item = postprocess_stock_item(stock_item)
            stock_item.update_record()

        return response_stock_item(stock_item)
    except:
        import traceback
        traceback.print_exc()
        raise HTTP(400)


@auth.requires_membership('Purchases')
def add_item_and_stock_item():
    """ Adds the item specified by the form, then add a purchase item whose id_item is the id of the newly created item, and its id_purchase is the specified purchase

        args
            id_purchase
        vars:
            all the item form fields

    """

    purchase = db.purchase(request.args(0))
    if not purchase:
        raise HTTP(404)
    if purchase.is_done:
        raise HTTP(405)

    item_data = dict(request.vars)

    # change string booleans to python booleans
    item_data['has_inventory'] = True if request.vars.has_inventory == 'true' else False
    item_data['allow_fractions'] = True if request.vars.allow_fractions == 'true' else False
            # categories
    if request.vars.categories and request.vars.categories != 'undefined':
        item_data['categories'] = []
        for c in request.vars.categories.split(','):
            try:
                item_data['categories'].append(int(c))
            except:
                pass
    else:
        item_data['categories'] = None

    # add the traits
    if request.vars.traits and request.vars.traits != 'undefined':
        item_data['traits'] = []
        for c in request.vars.traits.split(','):
            try:
                item_data['traits'].append(int(c))
            except:
                pass
    else:
        item_data['traits'] = None
    if request.vars.taxes and request.vars.taxes != 'undefined':
        item_data['taxes'] = []
        for c in request.vars.taxes.split(','):
            try:
                item_data['taxes'].append(int(c))
            except:
                pass
    else:
        item_data['taxes'] = None
    print item_data
    try:
        item_data['created_by'] = auth.user.id

        ret = db.item.validate_and_insert(**item_data)
        if not ret.errors:
            item = db.item(ret.id)
            url_name = "%s%s" % (urlify_string(item_data['name']), item.id)
            db.item(ret.id).update_record(url_name=url_name)

            stock_item = db.stock_item.insert(id_purchase=purchase.id, id_item=item.id, purchase_qty=1, base_price=item_data['base_price'], price2=item_data['price2'], price3=item_data['price3'])
            stock_item = response_stock_item(db.stock_item(stock_item))
            return dict(item=item, stock_item=stock_item)
        else:
            return dict(errors=ret.errors)
    except:
        import traceback
        traceback.print_exc()


@auth.requires_membership('Purchases')
def update_value():
    purchase = db.purchase(request.args(0))
    if not purchase:
        raise HTTP(404)
    if purchase.is_done:
        raise HTTP(405)
    field_name = request.vars.keys()[0]
    valid_fields = []
    for field in db.purchase:
        if field.name == 'id':
            continue
        if field.writable:
            valid_fields.append(field.name)
    if field_name in valid_fields:
        params = {field_name: request.vars[field_name]}
        r = db(db.purchase.id == request.args(0)).validate_and_update(**params)
        purchase = db.purchase(request.args(0))
        return {field_name: purchase[field_name]}
    return locals()


@auth.requires_membership('Purchases')
def fill():
    """ Used to add items to the specified purchase
    args:
        purchase_id

    """

    purchase = db.purchase(request.args(0))
    if not purchase:
        raise HTTP(404)
    if purchase.is_done:
        raise HTTP(405)

    buttons = [
          A(T('Commit'), _class="btn btn-primary", _href=URL('commit', args=purchase.id))
        , A(T('Complete later'), _class="btn btn-default", _href=URL('save', args=purchase.id))
        , A(T('Cancel'), _class="btn btn-default", _href=URL('cancel', args=purchase.id))
    ]
    form = SQLFORM(db.purchase, purchase.id, buttons=buttons, formstyle="bootstrap3_stacked", showid=False, _id="purchase_form")

    stock_items = db(db.stock_item.id_purchase == purchase.id).select()
    stock_items_json = []
    for stock_item in stock_items:
        serials = stock_item.serial_numbers.replace(',', ',\n') if stock_item.serial_numbers else ''

        stock_items_json.append(response_stock_item(stock_item))
    stock_items_json = json.dumps(stock_items_json)
    stock_items_script = SCRIPT('stock_items = %s;' % stock_items_json)

    return locals()


@auth.requires_membership('Purchases')
def cancel():
    """ Cancel the purchase, deleting the purchase record and all its stock items
        args [purchase_id]
    """

    purchase = db.purchase(request.args(0))
    if not purchase:
        raise HTTP(404)
    if purchase.is_done:
        raise HTTP(405)

    db(db.stock_item.id_purchase == request.args(0)).delete()
    db(db.purchase.id == request.args(0)).delete()

    redirect(URL('index'))


@auth.requires_membership('Purchases')
def commit():
    """ Commits the purchase

        args:
            purchase_id
    """

    purchase = db.purchase(request.args(0))
    if not purchase:
        raise(HTTP, 404)
    if purchase.is_done:
        raise HTTP(405)

    # #TODO:70 purchase total should match the amount stablished by the purchase items

    # generate stocks for every purchase item
    stock_items = db(db.stock_item.id_purchase == purchase.id).select()
    for stock_item in stock_items:
        stock_item = postprocess_stock_item(stock_item)
        stock_item.stock_qty = stock_item.purchase_qty
        stock_item.id_store = session.store
        # set the stock quantity to the purchased quantity
        stock_item.update_record()
        # update the item prices
        item = db.item(stock_item.id_item)
        item.base_price = stock_item.base_price
        item.price2 = stock_item.price2
        item.price3 = stock_item.price3
        item.update_record()
    purchase.is_done = True
    purchase.update_record()

    redirection(URL('index'))
    # redirect()



@auth.requires_membership('Purchases')
def save():
    redirect(URL('index'))


@auth.requires_membership('Purchases')
def get():
    """
        args: [purchase_id]
    """
    purchase = db.purchase(request.args(0))
    if not purchase:
        raise HTTP(404)
    if not purchase.is_done:
        raise HTTP(405)

    def stock_item_row(row, fields):
        tr = TR()
        tr.append(row.id_item.name)
        for field in fields[1:]:
            tr.append(row[field])
        return tr


    purchase_items = db(db.stock_item.id_purchase == purchase.id).select()
    purchase_items_table = super_table('stock_item', ['id_item', 'purchase_qty', 'price', 'taxes'], db.stock_item.id_purchase == purchase.id, options_enabled=False, row_function=stock_item_row)

    return locals()


@auth.requires_membership('Purchases')
def update():
    """
        args:
            purchase_id
        vars:
            is_xml: if true, then the form will accept an xml file
    """

    redirect(URL('fill', args=request.args))


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
    data = common_index('purchase', ['invoice_number', 'subtotal', 'total'], dict(options_function=purchase_options))
    return locals()
