# -*- coding: utf-8 -*-
#
# Author: Daniel J. Ramirez

@auth.requires(auth.has_membership('Sales')
            or auth.has_membership('Cashier')
            or auth.has_membership('Admin')
            or auth.has_membership('Manager')
            )
def create():
    # current bag must be set, because the seller need to review the bag before sell it.
    bag = db.bag(session.current_bag)
    if not bag:
        raise HTTP(404)
    # get bag items data
    bag_items = db(db.bag_item.id_bag == bag.id).select()
    total = 0
    taxes = 0
    subtotal = 0
    reward_points = 0
    quantity = 0
    for bag_item in bag_items:
        # since created bags does not remove stock, there could be more bag_items than stock items, so we need to check if theres enough stock to satisfy this sale, and if there is not, then we need to notify the seller or user
        stocks, quantity = item_stock(bag_item.id_item, session.store).itervalues()
        # if theres no stock the user needs to modify the bag
        if quantity <= 0:
            print "not stock"
        subtotal += bag_item.sale_price * bag_item.quantity
        taxes += bag_item.sale_taxes * bag_item.quantity
        total += (bag_item.sale_price + bag_item.sale_taxes) * bag_item.quantity
        quantity += bag_item.quantity
        reward_points += bag_item.id_item.reward_points or 0
    form = SQLFORM(db.sale)
    form.vars.id_bag = bag.id
    form.vars.subtotal = DQ(subtotal)
    form.vars.taxes = DQ(taxes)
    form.vars.total = DQ(total)
    form.vars.quantity = DQ(quantity)
    form.vars.reward_points = reward_points
    form.vars.id_store = bag.id_store.id
    if form.process().accepted:
        sale = db.sale(form.vars.id)
        # set sale parameters
        sale.id_bag = bag.id
        sale.subtotal = DQ(subtotal)
        sale.total = DQ(total)
        sale.quantity = DQ(quantity)
        sale.reward_points = reward_points
        sale.id_store = session.store
        sale.update_record()
        response.flash = T('Sale created')
    elif form.errors:
        response.flash = T('form has errors')
    return dict(form=form)


@auth.requires(auth.has_membership('Admin')
            or auth.has_membership('Manager')
            )
def get():
    pass


@auth.requires(auth.has_membership('Admin')
            or auth.has_membership('Manager')
            )
def update():
    return common_update('sale', request.args)


@auth.requires(auth.has_membership('Admin')
            or auth.has_membership('Manager')
            )
def delete():
    return common_delete('sale', request.args)


@auth.requires(auth.has_membership('Admin')
            or auth.has_membership('Manager')
            )
def index():
    rows = common_index('sale')
    data = super_table('sale', ['consecutive', 'subtotal', 'total'], rows)
    return locals()
