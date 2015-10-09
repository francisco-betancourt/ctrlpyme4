# -*- coding: utf-8 -*-
#
# Author: Daniel J. Ramirez

#
# A bag is a storage for items, that will be saled.
#

from decimal import Decimal as D


def set_bag_item(bag_item):
    item = db.item(bag_item.id_item)
    bag_item.name = item.name
    bag_item.base_price = item.base_price or 0
    bag_item.barcode = item_barcode(item)
    taxes = 1
    for tax in item.taxes:
        taxes *= tax.percentage / 100.0
    bag_item.sale_taxes = bag_item.base_price * D(taxes)
    print bag_item.sale_taxes.quantize(D('.0000'))

    return bag_item


def select_bag():
    """
        args:
            bag_id
    """

    try:
        bag = db.bag(request.args(0))
        if not bag:
            raise HTTP(404)
        session.current_bag = bag.id
        bag_items = []
        for bag_item in db(db.bag_item.id_bag == bag.id).select():
            bag_items.append(set_bag_item(bag_item))
        return dict(bag=bag, bag_items=bag_items)
    except:
        import traceback
        traceback.print_exc();


def add_bag_item():
    """
        args:
            id_item
            id_bag
    """

    item = db.item(request.args(0))
    id_bag = session.current_bag

    id_bag_item = db.bag_item.insert(id_bag=id_bag, id_item=item.id, quantity=1)
    bag_item = set_bag_item(db.bag_item(id_bag_item))

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

    bag = db.bag(session.current_bag)
    removed_bag = session.current_bag
    if not bag:
        raise HTTP(404)
    db(db.bag_item.id_bag == bag.id).delete()
    db(db.bag.id == bag.id).delete()

    other_bag = db(db.bag.id > 0).select().first()
    if other_bag:
        session.current_bag = other_bag.id

    return dict(other_bag=other_bag, removed=removed_bag)


def create():
    """
    """

    bag = db.bag.insert(id_store=None, completed=False)
    session.current_bag = bag.id

    return dict(bag=bag)
