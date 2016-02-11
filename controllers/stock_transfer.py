# -*- coding: utf-8 -*-
#
# Author: Daniel J. Ramirez

@auth.requires_membership('Stock transfers')
def ticket():
    """
        args: [id_stock_transfer]
    """

    stock_transfer = db.stock_transfer(request.args(0))
    if not stock_transfer:
        raise HTTP(404)

    print_ticket = request.vars.print_ticket

    items = db(db.bag_item.id_bag == stock_transfer.id_bag.id).select()

    _ticket = create_ticket(T('Stock transfer'), stock_transfer.id_store_from, stock_transfer.created_by, items, stock_transfer.id)

    return dict(ticket=_ticket, print_ticket=print_ticket)


@auth.requires_membership('Stock transfers')
def receive():
    """ args: [id_stock_transfer] """

    stock_transfer = db.stock_transfer(request.args(0))
    if not stock_transfer:
        raise HTTP(404)
    if stock_transfer.is_done:
        raise HTTP(405)

    bag_items = db(db.bag_item.id_bag == stock_transfer.id_bag.id).select()
    for bag_item in bag_items:
        avg_buy_price = DQ(bag_item.total_buy_price) / DQ(bag_item.quantity)

        if bag_item.id_item.is_bundle:
            bundle_items = db(db.bundle_item.id_bundle == bag_item.id_item).select()
            avg_buy_price = DQ(bag_item.total_buy_price) / DQ(bag_item.quantity) / DQ(len(bundle_items)) if bag_item.total_buy_price else 0
            for bundle_item in bundle_items:
                reintegrate_stock(bundle_item.id_item, bundle_item.quantity * bag_item.quantity, avg_buy_price, 'id_stock_transfer', stock_transfer.id)
        else:
            reintegrate_stock(bag_item.id_item, bag_item.quantity, avg_buy_price, 'id_stock_transfer', stock_transfer.id)
    stock_transfer.is_done = True
    stock_transfer.id_store_to = session.store
    stock_transfer.update_record()

    session.info = T('Products added to stock')
    redirect(URL('default', 'index'))

    return locals()


@auth.requires_membership('Stock transfers')
def scan_for_receive():
    return dict()


@auth.requires_membership('Stock transfers')
def index():
    data = super_table('stock_transfer', ['id_store_from', 'id_store_to', 'is_done'], (db.stock_transfer), show_id=True, options_function=lambda row: [option_btn('', action_name='Ticket', action_url=URL('ticket', args=row.id))])

    return locals()
