# -*- coding: utf-8 -*-
#
# Author: Daniel J. Ramirez

#
# A bag is a storage for items that will be sold.
#

from decimal import Decimal as D


# TODO on every bag opertation check if the bag is completed, when a bag is completed the user should not be able to modify it.

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
    subtotal = money_format(DQ(subtotal))
    taxes = money_format(DQ(taxes))
    total = money_format(DQ(total))
    quantity = DQ(quantity)
    return dict(subtotal=subtotal, taxes=taxes, total=total, quantity=quantity)


def modify_bag_item():
    """
        args:
            bag_item_id
    """

    bag_item = db.bag_item(request.args(0))
    if not bag_item:
        raise HTTP(404)
    bag_item.quantity = request.vars.quantity if request.vars.quantity else bag_item.quantity
    if not bag_item.id_item.allow_fractions:
        bag_item.quantity = remove_fractions(bag_item.quantity)

    bag_item.update_record()
    bag_data = refresh_bag_data(bag_item.id_bag.id)
    return dict(status='ok', bag_item=bag_item, **bag_data)


def set_bag_item(bag_item):
    item = db.item(bag_item.id_item)
    # bag_item.name = item.name
    bag_item.base_price = money_format(DQ(item.base_price)) if item.base_price else 0
    bag_item.price2 = money_format(DQ(item.price2)) if item.price2 else 0
    bag_item.price3 = money_format(DQ(item.price3)) if item.price3 else 0
    bag_item.sale_price = money_format(DQ(bag_item.sale_price or 0))

    bag_item.measure_unit = item.id_measure_unit.symbol

    bag_item.barcode = item_barcode(item)
    stocks = item_stock(item, session.store)
    bag_item.stock = stocks['quantity'] if stocks else 0

    return bag_item


def select_bag():
    """ Set the specified bag as the current bag. The current bag will be available as session.current_bag

        args:
            bag_id

    """

    try:
        bag = db((db.bag.id == request.args(0)) & (db.bag.created_by == auth.user.id) & (db.bag.id_store == session.store)).select().first()
        if not bag:
            raise HTTP(404)
        session.current_bag = bag.id
        subtotal = 0
        taxes = 0
        total = 0
        quantity = 0
        bag_items = []
        for bag_item in db(db.bag_item.id_bag == bag.id).select():
            subtotal += bag_item.sale_price * bag_item.quantity
            taxes += bag_item.sale_taxes * bag_item.quantity
            total += (bag_item.sale_price + bag_item.sale_taxes) * bag_item.quantity
            quantity += bag_item.quantity
            bag_item_modified = set_bag_item(bag_item)
            bag_items.append(bag_item_modified)
        subtotal = money_format(DQ(subtotal))
        taxes = money_format(DQ(taxes))
        total = money_format(DQ(total))

        return dict(bag=bag, bag_items=bag_items, subtotal=subtotal, total=total, taxes=taxes, quantity=quantity)
    except:
        import traceback
        traceback.print_exc();


def add_bag_item():
    """
        args:
            id_item
    """

    item = db.item(request.args(0))
    id_bag = session.current_bag

    if not item or not id_bag:
        raise HTTP(404)

    bag_item = db((db.bag_item.id_item == item.id)
                & (db.bag_item.id_bag == id_bag)
                ).select().first()
    if not bag_item:
        id_bag_item = db.bag_item.insert(id_bag=id_bag, id_item=item.id, quantity=1, sale_price=item.base_price, product_name=item.name,
            sale_taxes=item_taxes(item, item.base_price))
        bag_item = db.bag_item(id_bag_item)
    else:
        bag_item.quantity += 1
        bag_item.update_record()
    bag_item = set_bag_item(bag_item)

    bag_data = refresh_bag_data(id_bag)

    return dict(bag_item=bag_item, **bag_data)


def delete_bag_item():
    """
        args:
            id_bag_item
    """

    bag_item = db.bag_item(request.args(0))
    db(db.bag_item.id == request.args(0)).delete()
    bag_data = refresh_bag_data(bag_item.id_bag.id)
    return dict(status="ok", **bag_data)


def discard_bag():
    """
        args:
            id_bag

    """

    try:
        bag = db((db.bag.id == session.current_bag) & (db.bag.created_by == auth.user.id)).select().first()
        removed_bag = session.current_bag
        if not bag:
            raise HTTP(404)
        db(db.bag_item.id_bag == bag.id).delete()
        db(db.bag.id == bag.id).delete()

        other_bag = db((db.bag.is_active == True) & (db.bag.created_by == auth.user.id) & (db.bag.id_store == session.store)).select().first()
        if other_bag:
            session.current_bag = other_bag.id

        return dict(other_bag=other_bag, removed=removed_bag)
    except:
        import traceback
        traceback.print_exc()

def change_bag_item_sale_price():
    price_index = request.args(0)
    bag_item = db.bag_item(request.args(1))
    access_code = request.args(2)

    if not (price_index or bag_item or access_code):
        raise HTTP(400)
    user = db((db.auth_user.access_code == access_code)).select().first()
    if user:
        if auth.has_membership(None, user.id, role='VIP seller'):
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
    else:
        raise HTTP(401)

    bag_data = refresh_bag_data(bag_item.id_bag.id)

    return dict(status="ok", **bag_data)


def create():
    """
    """

    bag = db.bag.insert(id_store=session.store, completed=False)
    session.current_bag = bag.id

    return dict(bag=bag)
