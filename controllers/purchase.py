# -*- coding: utf-8 -*-
#
# Copyright (C) 2016 Bet@net
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#
# Author Daniel J. Ramirez <djrmuv@gmail.com>


precheck()

import json
from decimal import Decimal as D
from datetime import date, timedelta, datetime
import item_utils
from item_utils import item_barcode
import purchase_utils
# from cfdi import *


# #TODO:40 implement XML purchase
@auth.requires_membership('Purchases')
def create():
    """
        vars: is_xml: if true, then the form will accept an xml file
    """

    is_xml = request.vars.is_xml == 'True'
    new_purchase_id = purchase_utils.new(session.store, request.now, auth.user)
    if not is_xml:
        redirect(URL('fill', args=new_purchase_id))
    else:
        form = SQLFORM(db.purchase, fields=['purchase_xml'])

        return dict(form=form)


# @auth.requires_membership('Purchases')
# def create_from_xml():
#     """
#         vars: is_xml: if true, then the form will accept an xml file
#     """
#
#     is_xml = request.vars.is_xml == 'True'
#     new_purchase_id = db.purchase.insert(id_store=session.store)
#     if not is_xml:
#         redirect(URL('fill', args=new_purchase_id))


@auth.requires_membership('Purchases')
def create_from_order():
    """ Given a sale order, creates a purchase and adds all the order missing items to the purchase

        args: [id_order]
    """

    from bag_utils import get_ordered_items_count


    order = db.sale_order(request.args(0))
    if not order:
        raise HTTP(404)
    missing_items = []

    # check if the order items are in stock
    for bag_item in db(db.bag_item.id_bag == order.id_bag.id).iterselect():
        quantity = item_stock_qty(bag_item.id_item, session.store)
        order_items_qty = get_ordered_items_count(order.id, bag_item.id_item.id)
        # the needed quantity will be the total amount of required items to satisfy the specified order and the previous orders.
        needed_qty = bag_item.quantity + order_items_qty
        item_ready = (quantity >= needed_qty)
        if not item_ready:
            # if the item is a bundle add the contained items to the purchase
            if bag_item.id_item.is_bundle:
                for bundle_item in db((db.bundle_item.id_bundle == bag_item.id_item.id)).select():
                    qty = item_stock_qty(bundle_item.id_item, session.store)
                item_ready = (quantity >= needed_qty * bundle_item.quantity)
                if not item_ready:
                    missing_items.append(
                        dict(
                            qty=(bag_item.quantity * bundle_item.quantity) - qty
                            , item=bundle_item.id_item
                        )
                    )
            else:
                missing_items.append(dict(item=bag_item.id_item, qty=needed_qty - quantity))

    if missing_items:
        new_purchase = purchase_utils.new(session.store, request.now, auth.user)
        for missing_item in missing_items:
            db.stock_item.insert(id_purchase=new_purchase, id_credit_note=None, id_inventory=None, id_store=session.store, purchase_qty=missing_item['qty'], id_item=missing_item['item'].id, base_price=missing_item['item'].base_price, price2=missing_item['item'].price2, price3=missing_item['item'].price3)
    else:
        session.info = T('No missing items')
        redirect(URL('sale_order', 'ready', args=order.id))

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
    item_name = stock_item.id_item.name + item_utils.concat_traits(stock_item.id_item)

    res = {
          "id": stock_item.id
        , "id_item": stock_item.id_item
        , "item_name": item_name
        , "item_barcode": item_barcode(stock_item.id_item)
        , "purchase_qty": str(stock_item.purchase_qty or 0)
        , "price": str(DQ(stock_item.price or 0))
        , "base_price": str(DQ(stock_item.base_price or 0))
        , "price2": str(DQ(stock_item.price2 or 0))
        , "price3": str(DQ(stock_item.price3 or 0))
        , "taxes": str(DQ(stock_item.taxes) or 0)
        , "serial_numbers": serials
        , "earnp_base_price": 0
        , "earnp_price2": 0
        , "earnp_price3": 0
    }

    if stock_item.price:
        price = DQ(stock_item.price) + DQ(stock_item.taxes)
        for target in ['base_price', 'price2', 'price3']:
            earnp = DQ(
                (stock_item[target] / price - 1) * 100, True, True
            )
            res['earnp_' + target] = earnp

    return res


def valid_purchase(purchase):
    if not purchase:
        raise HTTP(404, "Purchase not found")
    if purchase.is_done:
        raise HTTP(405, "Purchase is done")


def create_new_stock_item(purchase, item):
    """ Create and settup stock item """

    price = 0
    if item.id_brand and item.id_brand.earnp_base:
        price = item.base_price / (1 + item.id_brand.earnp_base / 100)

    if not price:
        # get prices from the last stock items
        last_stock_item = db( db.stock_item.id_item == item.id ).select(
            db.stock_item.price
        ).last()
        price = last_stock_item.price if last_stock_item else 1

    taxes = item_utils.item_taxes(item, 1)
    price /= 1 + taxes

    stock_item = db.stock_item.insert(
        id_purchase=purchase.id, id_item=item.id, purchase_qty=1,
        price=price,
        taxes=price * taxes,
        base_price=item.base_price,
        price2=item.price2,
        price3=item.price3
    )

    purchase.items_subtotal += price
    purchase.items_total += price + price * taxes
    purchase.update_record()
    
    return stock_item


@auth.requires_membership('Purchases')
def add_stock_item():
    """ Used to add a stock_item to the specified purchase, this method will return a form to edit the newly created purchase item

        args:
            purchase_id
            item_id
    """

    purchase = db.purchase(request.args(0))
    item = db.item(request.args(1))
    valid_purchase(purchase)
    if not item:
        raise HTTP(404)
    if item.is_bundle or not item.has_inventory:
        raise HTTP(403)


    stock_item = db(
        (db.stock_item.id_item == item.id) &
        (db.stock_item.id_purchase == purchase.id)
    ).select().first()
    if not stock_item:
        stock_item_id = create_new_stock_item(purchase, item)
    redirect(URL('fill', args=[purchase.id, stock_item_id]))
    return locals()


def stock_items_buy_price(stock_item):
    """ Returns the total stock item buy price, considering taxes and 
        quantity """
    return (D(stock_item.price or 0) + D(stock_item.taxes or 0)) * D(stock_item.purchase_qty or 0)


@auth.requires_membership('Purchases')
def delete_stock_item():
    """ This function removes the specified stock item, this function actually deletes the record

        args:
            stock_item_id
    """

    stock_item = db.stock_item(request.args(0))
    if not stock_item:
        raise HTTP(400)
    valid_purchase(stock_item.id_purchase)

    purchase = db.purchase(stock_item.id_purchase.id)
    purchase.items_subtotal -= stock_items_buy_price(stock_item) - stock_item.taxes * stock_item.purchase_qty
    purchase.items_total -= stock_items_buy_price(stock_item)
    purchase.update_record()
    stock_item.delete_record()

    redirect(URL('fill', args=[stock_item.id_purchase.id]))


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
def update_stock_item_price():
    """ Used to update the stock item price, considering earning percentages or custom prices """

    stock_item =  db.stock_item(request.args(0))
    purchase = db.purchase(stock_item.id_purchase.id)
    valid_purchase(purchase)

    target = request.vars.target
    ep = 0
    price = 0
    try:
        ep = D(request.vars.ep or 0)
        price = D(request.vars.price or 0)
    except:
        raise HTTP(405, "Invalid arguments")
    if not stock_item:
        raise HTTP(404, "Stock item not found")
    if not target in ['base_price', 'price2', 'price3']:
        raise HTTP(405, "Invalid target")


    # try to get earning percentage from brand
    if not price and not ep:
        ep_target = 'earning_percentage_'
        if target == 'base_price':
            ep_target += 'base'
        if target == 'price2':
            ep_target += '2'
        if target == 'price3':
            ep_target += '3'
        ep = stock_item.id_item.id_brand[ep_target]
        if not ep:
            raise HTTP(405)

    old_total_price = stock_items_buy_price(stock_item)
    old_subtotal_price = old_total_price - stock_item.taxes * stock_item.purchase_qty

    new_price = stock_item[target]
    purchase_price = D(stock_item.price or 0) + D(stock_item.taxes or 0)
    if price:
        new_price = price
    elif ep:
        new_price = purchase_price + ep / 100 * purchase_price

    stock_item[target] = new_price
    stock_item = postprocess_stock_item(stock_item)
    stock_item.update_record()

    new_total_price = stock_items_buy_price(stock_item)
    new_subtotal_price = new_total_price - stock_item.taxes * stock_item.purchase_qty
    price_diff = old_total_price - new_total_price
    purchase.items_total -= price_diff

    subprice_diff = old_subtotal_price - new_subtotal_price

    purchase.items_subtotal -= subprice_diff
    purchase.update_record()

    res = response_stock_item(stock_item)
    return res



@auth.requires_membership('Purchases')
def modify_stock_item():
    """ This functions allows the modification of a stock item, by specifying the modified fields via url arguments.

        args: [stock_item_id, param_name, param_value]
    """

    stock_item = db.stock_item(request.args(0))
    purchase = db.purchase(stock_item.id_purchase.id)
    valid_purchase(purchase)

    if not stock_item:
        raise HTTP(404)
    if stock_item.id_purchase.is_done:
        raise HTTP(405)
    try:

        old_price = stock_items_buy_price(stock_item)
        old_price_only = old_price / stock_item.purchase_qty
        old_price_no_tax = old_price - stock_item.taxes * stock_item.purchase_qty

        param_name = request.args(1)
        param_value = request.args(2)

        if param_name in ['purchase_qty', 'price', 'base_price', 'price2', 'price3']:
            
            stock_item[param_name] = DQ(param_value)
            stock_item = postprocess_stock_item(stock_item)


            # given the purchase price, calculate the proportional prices based on the last earning percentage
            if param_name == 'price':
                for target in ['base_price', 'price2', 'price3']:
                    earnp = DQ(
                        (stock_item[target] / old_price_only - 1), 
                        True, True
                    )
                    new_total_price = stock_item.price + stock_item.taxes
                    stock_item[target] = new_total_price + new_total_price * earnp

            # item base price should not be 0
            if stock_item.base_price <= D(0):
                stock_item.base_price = stock_item.id_item.base_price or D(1)
            stock_item.update_record()

        new_price = stock_items_buy_price(stock_item)
        price_diff = old_price - new_price
        purchase.items_total -= price_diff

        new_price_no_tax = new_price - stock_item.taxes * stock_item.purchase_qty
        subtotal_diff = old_price_no_tax - new_price_no_tax
        purchase.items_subtotal -= subtotal_diff

        purchase.update_record()

        return response_stock_item(stock_item)
    except:
        import traceback
        traceback.print_exc()
        raise HTTP(400)


@auth.requires_membership('Purchases')
def add_item_and_stock_item():
    """ Adds the item specified by the form, then add a purchase item whose id_item is the id of the newly created item, and its id_purchase is the specified purchase

        args: [id_purchase]
        vars: [all the item form fields]

    """
    from item_utils import create_traits_ref_list

    purchase = db.purchase(request.args(0))
    valid_purchase(purchase)

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
        item_data['traits'] = create_traits_ref_list(request.vars.traits)
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
    item_data['created_by'] = auth.user.id

    ret = db.item.validate_and_insert(**item_data)
    if not ret.errors:
        item = db.item(ret.id)
        url_name = "%s%s" % (urlify_string(item_data['name']), item.id)
        db.item(ret.id).update_record(url_name=url_name)

        redirect(URL('add_stock_item', ))

        stock_item_id = create_new_stock_item(purchase, item)
        stock_item = response_stock_item(db.stock_item(stock_item_id))

        return dict(item=item, stock_item=stock_item)
    else:
        return dict(errors=ret.errors)



@auth.requires_membership('Purchases')
def update_value():
    purchase = db.purchase(request.args(0))
    valid_purchase(purchase)

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
    args: [purchase_id, current_stock_item]

    """
    import supert
    Supert = supert.Supert()

    purchase = db.purchase(request.args(0))
    valid_purchase(purchase)
    current_stock_item = db.stock_item(request.args(1))
    if current_stock_item:
        current_stock_item = Storage(response_stock_item(current_stock_item))

    if current_stock_item and current_stock_item.id_purchase != purchase.id:
        session.flash = T('Invalid stock item')
        current_stock_item == None

    buttons = [
          A(T('Commit'), _class="btn btn-primary", _href=URL('commit', args=purchase.id))
        , A(T('Complete later'), _class="btn btn-default", _href=URL('save', args=purchase.id))
        , A(T('Cancel'), _class="btn btn-default", _href=URL('cancel', args=purchase.id))
    ]
    form = SQLFORM(db.purchase, purchase.id, buttons=buttons, formstyle="bootstrap3_stacked", showid=False, _id="purchase_form")


    def stock_item_options(row):
        return supert.OPTION_BTN('edit',
            url=URL('fill', args=[purchase.id, row.id], vars=request.vars)
            , title=T("modify")
        )

    stock_items_table = Supert.SUPERT(
        db.stock_item.id_purchase == purchase.id
        , fields=[
            dict(fields=[ 'id_item.name' ], label_as=T('Name')),
            dict(fields=['id_item','id_item.sku','id_item.ean','id_item.upc' ],
                custom_format=lambda r, f : item_barcode(r[f[0]]),
                label_as=T('Barcode')
            ),
            dict(fields=['purchase_qty'],
                custom_format=lambda r, f : SPAN(DQ(r[f[0]], True, True), _id="s_item_%s_%s" % (r.id, f[0])),
                label_as=T('Quantity')
            ),
            dict(fields=['price', 'taxes'],
                custom_format=lambda r, f : SPAN(DQ(r[f[0]] + r[f[1]], True), _id="s_item_%s_%s" % (r.id, f[0])),
                label_as=T('Buy Price')
            )
        ]
        , options_func=stock_item_options
        , global_options=[]
    )

    return locals()


@auth.requires_membership('Purchases')
def cancel():
    """ Cancel the purchase, deleting the purchase record and all its stock items
        args [purchase_id]
    """

    purchase = db.purchase(request.args(0))
    valid_purchase(purchase)

    db(db.stock_item.id_purchase == request.args(0)).delete()
    db(db.purchase.id == request.args(0)).delete()

    redirect(URL('index'))


@auth.requires_membership('Purchases')
def commit():
    """ Commits the purchase

        args: [purchase_id]
    """

    import purchase_utils


    purchase = db.purchase(request.args(0))
    valid_purchase(purchase)

    # < 1 peso difference allowed
    if abs(purchase.total - purchase.items_total) > D(1):
        session.info = T('Purchase total does not match the items total (calculated total is: $%s)') % DQ(purchase.items_total, True)
        redirect(URL('fill', args=purchase.id))
    # check if the purchase has all the necessary information
    missing_fields = []
    if not purchase.id_payment_opt:
        missing_fields.append(str(T("Payment option")))
    if not purchase.id_supplier:
        missing_fields.append(str(T("Supplier")))
    if not purchase.id_store:
        missing_fields.append(str(T("Store")))
    if missing_fields:
        session.info = T('Please fill the following fields') + ': ' + ', '.join(missing_fields)
        redirect(URL('fill', args=purchase.id))

    purchase_utils.commit(purchase)

    session.info = {
        'text': T('Purchase commited'),
        'btn': dict(href=URL('item', 'labels', vars=dict(id_purchase=purchase.id)), text=T('Print labels'))
    }

    redirect(URL('index'))



@auth.requires_membership('Purchases')
def save():
    redirect(URL('index'))


@auth.requires_membership('Purchases')
def get():
    """
        args: [purchase_id]
    """
    import supert
    Supert = supert.Supert()

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
    purchase_items_table = Supert.SUPERT(
        db.stock_item.id_purchase == purchase.id,
        fields=['id_item.name', 'purchase_qty', 'price', 'taxes'],
        options_enabled=False, searchable=False
    )

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


def purchase_options(row):
    import supert

    buttons = ()
    # edit option
    if not row.is_done:
        buttons += supert.OPTION_BTN('edit', URL('update', args=row.id), title=T('edit')),
    else:
        buttons += supert.OPTION_BTN('receipt', URL('get', args=row.id), title=T('view')),
        buttons += supert.OPTION_BTN('label', URL('item', 'labels', vars=dict(id_purchase=row.id) ), title=T('print labels')),
    # buttons += supert_default_options(row)[1],
    return buttons


@auth.requires_membership('Purchases')
def index():
    data = common_index('purchase', ['invoice_number', 'subtotal', 'total', 'created_on'], dict(options_func=purchase_options, global_options=[]))
    return locals()
