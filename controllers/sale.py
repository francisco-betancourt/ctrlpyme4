# -*- coding: utf-8 -*-
#
# Author: Daniel J. Ramirez

def create():
    # current bag must be set, because the seller need to review the bag before sell it.
    bag = db.bag(session.current_bag)
    if not bag:
        raise HTTP(404)
    # get bag items data
    bag_items = db(db.bag_item.id_bag == bag.id).select()
    total = 0
    subtotal = 0
    reward_points = 0
    quantity = 0
    for bag_item in bag_items:
        # since created bags does not remove stock, there could be more bag_items than stock items, so we need to check if theres enough stock to satisfy this sale, and if there is not, then we need to notify the seller or user
        stock = db( (db.stock.id_item == bag_item.id_item)
                  & (db.stock.quantity > 0)
                  ).select(orderby=db.stock.id_purchase).first()
        if not stock:
            print "not stock"
        subtotal += bag_item.sale_price * bag_item.quantity
        total += (bag_item.sale_price + bag_item.sale_taxes) * bag_item.quantity
        quantity += bag_item.quantity
        reward_points += bag_item.id_item.reward_points or 0
    form = SQLFORM(db.sale)
    form.vars.id_bag = bag.id
    form.vars.subtotal = DQ(subtotal)
    form.vars.total = DQ(total)
    form.vars.quantity = DQ(quantity)
    form.vars.reward_points = reward_points
    if form.process().accepted:
        response.flash = 'form accepted'
    elif form.errors:
        response.flash = 'form has errors'
    return dict(form=form)


def get():
    pass


def update():
    return common_update('sale', request.args)


def delete():
    return common_delete('sale', request.args)


def index():
    rows = common_index('sale')
    data = super_table('sale', ['consecutive', 'subtotal', 'total'], rows)
    return locals()
