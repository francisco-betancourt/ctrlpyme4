# -*- coding: utf-8 -*-
#
# Author: Daniel J. Ramirez

#
# A bag is a storage for items, that will be saled.
#

from decimal import Decimal as D



def modify_bag_item():
    """
        args:
            bag_item_id
    """

    bag_item = db.bag_item(request.args(0))
    if not bag_item:
        raise HTTP(404)
    bag_item.quantity = request.vars.quantity if request.vars.quantity else bag_item.quantity
    bag_item.sale_price = request.vars.sale_price if request.vars.sale_price else bag_item.sale_price

    bag_item.update_record()
    return dict(status='ok')


def set_bag_item(bag_item):
    item = db.item(bag_item.id_item)
    bag_item.name = item.name
    bag_item.base_price = D(item.base_price or 0).quantize(D('.000000'))
    bag_item.barcode = item_barcode(item)
    bag_item.sale_taxes = item_taxes(item, item.base_price or 0)

    return bag_item


def select_bag():
    """ Set the specified bag as the current bag. The current bag will be available as session.current_bag

        args:
            bag_id

    """

    try:
        bag = db((db.bag.id == request.args(0)) & (db.bag.created_by == auth.user.id)).select().first()
        if not bag:
            raise HTTP(404)
        session.current_bag = bag.id
        subtotal = 0
        total = 0
        bag_items = []
        for bag_item in db(db.bag_item.id_bag == bag.id).select():
            bag_item_modified = set_bag_item(bag_item)
            bag_items.append(bag_item_modified)
            subtotal += bag_item.base_price * bag_item.quantity
            total += (bag_item.base_price + bag_item.sale_taxes) * bag_item.quantity
            bag_item_modified.base_price = str(bag_item_modified.base_price)

        return dict(bag=bag, bag_items=bag_items, subtotal=subtotal, total=total)
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

    bag_item = db(db.bag_item.id_item == item.id).select().first()
    if not bag_item:
        id_bag_item = db.bag_item.insert(id_bag=id_bag, id_item=item.id, quantity=1)
        bag_item = db.bag_item(id_bag_item)
    else:
        bag_item.quantity += 1
        bag_item.update_record()
    bag_item = set_bag_item(bag_item)

    return dict(bag_item=bag_item)


def delete_bag_item():
    """
        args:
            id_bag_item
    """

    db(db.bag_item.id == request.args(0)).delete()
    return dict(status="ok")


def discard_bag():
    """
        args:
            id_bag

    """

    bag = db((db.bag.id == session.current_bag) & (db.bag.created_by == auth.user.id))
    removed_bag = session.current_bag
    if not bag:
        raise HTTP(404)
    db(db.bag_item.id_bag == bag.id).delete()
    db(db.bag.id == bag.id).delete()

    other_bag = db((db.bag.is_active == True) & (db.bag.created_by == auth.user.id)).select().first()
    if other_bag:
        session.current_bag = other_bag.id

    return dict(other_bag=other_bag, removed=removed_bag)


def create():
    """
    """

    bag = db.bag.insert(id_store=None, completed=False)
    session.current_bag = bag.id

    return dict(bag=bag)
