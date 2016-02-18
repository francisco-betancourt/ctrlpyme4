# -*- coding: utf-8 -*-
#
# Author: Daniel J. Ramirez

#
# A bag is a storage for items that will be sold.
#

from decimal import Decimal as D
from decimal import ROUND_FLOOR
from math import floor


def get_valid_bag(id_bag, completed=False):
    try:
        query = (db.bag.id == id_bag)
        query &= (db.bag.created_by == auth.user.id)
        query &= (db.bag.completed == completed)
        if not auth.user.is_client:
            query &= (db.bag.id_store == session.store)
        bag = db(query).select().first()
        return bag
    except:
        import traceback as tb
        tb.print_exc()
        return None


def money_format(value):
    return '$ ' + str(value)



def refresh_bag_data(id_bag):
    bag = db.bag(id_bag)

    bag_items = db(db.bag_item.id_bag == bag.id).select()

    subtotal = D(0)
    taxes = D(0)
    total = D(0)
    quantity = D(0)
    for bag_item in bag_items:
        subtotal += bag_item.sale_price * bag_item.quantity
        taxes += bag_item.sale_taxes * bag_item.quantity
        total += (bag_item.sale_taxes + bag_item.sale_price) * bag_item.quantity
        quantity += bag_item.quantity
    bag.update_record(subtotal=DQ(subtotal), taxes=DQ(taxes), total=DQ(total))
    subtotal = money_format(DQ(subtotal, True))
    taxes = money_format(DQ(taxes, True))
    total = money_format(DQ(total, True))
    quantity = DQ(quantity, True, True)

    return dict(subtotal=subtotal, taxes=taxes, total=total, quantity=quantity)


@auth.requires(auth.has_membership('Sales bags')
            or auth.has_membership('Clients')
            )
def modify_bag_item():
    """
        modifies the bag_item quantity.

        args:
            bag_item_id
    """

    bag_item = db.bag_item(request.args(0))
    if not get_valid_bag(bag_item.id_bag):
        raise HTTP(403)
    if not bag_item:
        raise HTTP(404)

    is_online_sale = False
    if auth.has_membership('Clients'):
        is_online_sale = True

    old_qty = bag_item.quantity
    bag_item.quantity = request.vars.quantity if request.vars.quantity else bag_item.quantity
    if not bag_item.id_item.allow_fractions:
        bag_item.quantity = remove_fractions(bag_item.quantity)
    bag_item.quantity = DQ(bag_item.quantity)

    if not is_online_sale:
        qty = item_stock(db.item(bag_item.id_item), session.store, id_bag=session.current_bag)['quantity']
        diff = (old_qty - bag_item.quantity) if (old_qty - bag_item.quantity) > 0 else 0
        if qty + diff < bag_item.quantity - old_qty:
            bag_item.quantity = max(old_qty, qty + old_qty)

    bag_item.update_record()
    bag_data = refresh_bag_data(bag_item.id_bag.id)
    return dict(status='ok', bag_item=bag_item, **bag_data)


def set_bag_item(bag_item, discounts=[]):
    """ modifies bag item data, in order to display it properly, this method does not modify the database """
    item = bag_item.id_item
    # bag_item.name = item.name

    discount_p = DQ(1.0) - (bag_item.sale_price / (bag_item.sale_price + bag_item.discount))
    item.base_price -= item.base_price * discount_p
    bag_item.base_price = money_format(DQ(item.base_price, True)) if item.base_price else 0
    bag_item.price2 = money_format(DQ(item.price2 - item.price2 * discount_p, True)) if item.price2 else 0
    bag_item.price3 = money_format(DQ(item.price3 - item.price3 * discount_p, True)) if item.price3 else 0
    bag_item.sale_price = money_format(DQ(bag_item.sale_price or 0, True))

    bag_item.measure_unit = item.id_measure_unit.symbol

    bag_item.barcode = item_barcode(item)
    stocks = item_stock(item, session.store)
    bag_item.has_inventory = item.has_inventory
    bag_item.stock = stocks['quantity'] if stocks else 0
    bag_item.discount_percentage = int(discount_p * D(100.0))

    return bag_item


@auth.requires(auth.has_membership('Sales bags')
            or auth.has_membership('Clients')
            )
@service.jsonrpc
@service.jsonrpc2
def select_bag():
    """ Set the specified bag as the current bag. The current bag will be available as session.current_bag

        args: [bag_id]

    """

    bag = get_valid_bag(request.args(0))
    if not bag:
        raise HTTP(404)
    session.current_bag = bag.id
    subtotal = 0
    taxes = 0
    total = 0
    quantity = 0
    bag_items = []
    try:
        for bag_item in db(db.bag_item.id_bag == bag.id).select():
            subtotal += bag_item.sale_price * bag_item.quantity
            taxes += bag_item.sale_taxes * bag_item.quantity
            total += (bag_item.sale_price + bag_item.sale_taxes) * bag_item.quantity
            quantity += bag_item.quantity
            bag_item_modified = set_bag_item(bag_item)
            bag_items.append(bag_item_modified)
        quantity = DQ(quantity, True, True)
        subtotal = money_format(DQ(subtotal, True))
        taxes = money_format(DQ(taxes, True))
        total = money_format(DQ(total, True))

        return dict(bag=bag, bag_items=bag_items, subtotal=subtotal, total=total, taxes=taxes, quantity=quantity)
    except:
        import traceback
        traceback.print_exc();


@auth.requires(auth.has_membership('Sales bags')
            or auth.has_membership('Clients')
            )
def add_bag_item():
    """
        args:
            id_item
    """

    is_online_sale = False
    if auth.has_membership('Clients'):
        is_online_sale = True

    try:
        item = db.item(request.args(0))
        bag = get_valid_bag(session.current_bag)

        id_bag = bag.id if bag else None

        if not item or not id_bag:
            raise HTTP(404)

        bag_item = db((db.bag_item.id_item == item.id)
                    & (db.bag_item.id_bag == id_bag)
                    ).select().first()

        item_stock_qty = DQ(item_stock(item, session.store, id_bag=session.current_bag)['quantity'])

        # if theres no stock notify the user
        if not bag_item:
            base_qty = 1 if item_stock_qty >= 1 or is_online_sale else item_stock_qty % 1
            if base_qty <= 0:
                return dict(status="out of stock")
            item_taxes_str = ''
            for tax in item.taxes:
                item_taxes_str += '%s:%s' % (tax.name, tax.percentage)
                if tax != item.taxes[-1]:
                    item_taxes_str += ','
            discounts = item_discounts(item)
            sale_price = discount_data(discounts, item.base_price)[0]
            discount = item.base_price - sale_price
            id_bag_item = db.bag_item.insert(id_bag=id_bag, id_item=item.id, quantity=base_qty, sale_price=sale_price, discount=discount, product_name=item.name, item_taxes=item_taxes_str,
                sale_taxes=item_taxes(item, item.base_price))
            bag_item = db.bag_item(id_bag_item)
        else:
            base_qty = item_stock_qty if item_stock_qty < 1 and not is_online_sale else 1
            if base_qty <= 0:
                return dict(status="out of stock")
            bag_item.quantity += base_qty
            bag_item.update_record()

        bag_item = set_bag_item(bag_item)
        bag_data = refresh_bag_data(id_bag)

        return dict(bag_item=bag_item, **bag_data)
    except:
        import traceback
        traceback.print_exc()


@auth.requires(auth.has_membership('Sales bags')
            or auth.has_membership('Clients')
            )
def delete_bag_item():
    """
        args:
            id_bag_item
    """

    bag_item = db.bag_item(request.args(0))
    if not get_valid_bag(bag_item.id_bag):
        raise HTTP(401)
    db(db.bag_item.id == request.args(0)).delete()
    bag_data = refresh_bag_data(bag_item.id_bag.id)
    return dict(status="ok", **bag_data)


@auth.requires_membership('Sales bags')
def discard_bag():
    try:
        bag = get_valid_bag(session.current_bag)
        if not bag:
            raise HTTP(401)
        removed_bag = session.current_bag
        if not bag:
            raise HTTP(404)
        db(db.bag_item.id_bag == bag.id).delete()
        db(db.bag.id == bag.id).delete()

        auto_bag_selection()

        return dict(other_bag=db.bag(session.current_bag), removed=removed_bag)
    except:
        import traceback
        traceback.print_exc()


@auth.requires_membership('Sales bags')
def change_bag_item_sale_price():
    price_index = request.args(0)
    bag_item = db.bag_item(request.args(1))
    access_code = request.args(2)

    access = False
    if auth.has_membership('Admin') or auth.has_membership('Manager'):
        access = True
    if not (price_index or bag_item or access_code or access):
        raise HTTP(400)
    if not get_valid_bag(bag_item.id_bag):
        raise HTTP(401)
    user = db((db.auth_user.access_code == access_code)).select().first() if access_code else None
    is_vip_seller = auth.has_membership(None, user.id, role='VIP seller') or auth.has_membership(None, user.id, role='Admin') or auth.has_membership(None, user.id, role='Manager') if user else access
    if is_vip_seller:
        # change the item bag item sale price in db
        sale_price = bag_item.sale_price
        if price_index == '1':
            sale_price = bag_item.id_item.base_price
        elif price_index == '2':
            sale_price = bag_item.id_item.price2
        elif price_index == '3':
            sale_price = bag_item.id_item.price3
        bag_item.sale_price = sale_price
        bag_item.sale_taxes = item_taxes(bag_item.id_item, bag_item.sale_price or 0)
        bag_item.update_record()
    else:
        raise HTTP(401)

    bag_data = refresh_bag_data(bag_item.id_bag.id)

    return dict(status="ok", **bag_data)


def check_bag_items_integrity(bag_items):
    out_of_stock_items = []
    for bag_item in bag_items:
        # delete bag item when the item has 0 quantity
        if bag_item.quantity <= 0:
            db(db.bag_item.id == bag_item.id).delete()
        qty = item_stock(bag_item.id_item, session.store)['quantity']
        if bag_item.quantity > qty:
            out_of_stock_items.append(bag_item)
    if out_of_stock_items and (auth.has_membership('Employee') or auth.has_membership('Admin')):
        response.flash = T('Some items are out of stock or are inconsistent')
        auto_bag_selection()
        redirection()


@auth.requires(auth.has_membership('Sales bags')
            or auth.has_membership('Clients')
            )
def complete():
    bag = get_valid_bag(session.current_bag)

    if not bag:
        raise HTTP(404)

    # check if all the bag items are consistent
    bag_items = db(db.bag_item.id_bag == bag.id).select()
    # delete the bag if there are no items
    if not bag_items:
        db(db.bag.id == bag.id).delete()
        auto_bag_selection()
        redirection()

    check_bag_items_integrity(bag_items)

    if auth.has_membership('Clients'):
        bag.is_on_hold = True
        bag.update_record()
        redirect(URL('sale_order', 'create', args=bag.id))
    # _next = WORKFLOW_DATA[COMPANY_WORKFLOW].next(request.controller, request.function, auth.user)
    # redirect(URL(_next, args=bag.id))
    if auth.has_membership('Sales checkout'):
        bag.completed = True
        bag.update_record()
        auto_bag_selection()
        redirect(URL('sale', 'create', args=bag.id))
    else:
        bag.completed = True
        bag.update_record()
        auto_bag_selection()
        redirect(URL('ticket', args=bag.id))


@auth.requires_membership('Stock transfers')
def stock_transfer():
    """ """

    bag = get_valid_bag(session.current_bag)

    if not bag:
        raise HTTP(404)

    # check if all the bag items are consistent
    bag_items = db(db.bag_item.id_bag == bag.id).select()
    # delete the bag if there are no items
    if not bag_items:
        db(db.bag.id == bag.id).delete()
        auto_bag_selection()
        redirection()

    check_bag_items_integrity(bag_items)

    # create stock transfer record
    new_stock_transfer_id = db.stock_transfer.insert(id_store_from=bag.id_store.id, id_bag=bag.id)
    bag.completed = True
    bag.update_record()
    remove_stocks(bag_items)

    redirect(URL('stock_transfer', 'ticket', args=new_stock_transfer_id))


@auth.requires(auth.has_membership('Sales bags')
            or auth.has_membership('Clients')
            )
def ticket():
    """
        args:
            bag_id
    """

    bag = get_valid_bag(request.args(0), completed=True)

    if not bag:
        raise HTTP(404)

    # bag items
    bag_items = db(db.bag_item.id_bag == bag.id).select()

    ticket_barcode = "%010d" % bag.id
    if bag.created_by.is_client:
        ticket = create_ticket(T('Order'), None, None, bag_items, ticket_barcode)
    else:
        ticket = create_ticket(T('Order'), bag.id_store, bag.created_by, bag_items, ticket_barcode)

    return locals()


@auth.requires(auth.has_membership('Sales checkout')
            or auth.has_membership('Admin')
            or auth.has_membership('Manager')
            )
def get():
    """
        args: bag_id
    """

    bag = db((db.bag.completed == True) & (db.bag.id == request.args(0)) & (db.bag.id_store == session.store)).select().first()
    if not bag:
        raise HTTP(404)
    return dict(bag=bag)


@auth.requires_membership('Sales bags')
def create():
    """
    """

    try:
        bag = db.bag.insert(id_store=session.store, completed=False)
        session.current_bag = bag.id

        return dict(bag=bag)
    except:
        import traceback
        traceback.print_exc()
