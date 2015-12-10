# -*- coding: utf-8 -*-
#
# Author: Daniel J. Ramirez

@auth.requires_membership('Clients')
def create():
    """
        args [id_bag]
    """

    bag = db.bag(request.args(0))
    if not bag:
        raise HTTP(404)
    if not bag.completed or db(db.sale_order.id_bag == bag.id).select().first():
        raise HTTP(405)
    if bag.created_by != auth.user.id:
        raise HTTP(401)

    new_order = db.sale_order.insert(id_bag=bag.id, id_client=auth.user.id)

    session.info = {'text': T("You're order has been created, we will notify you when it's ready"), 'button': {'text': 'View ticket', 'ref': URL('bag', 'ticket', args=bag.id), 'target': 'blank'}
    }

    redirect(URL('default', 'index'))


def get():
    pass


def validate_ready(form):
    ready == True
    for bag_item in db(db.bag_item.id_bag == form.vars.id_bag).select():
        stock, quantity = item_stock(bag_item.id_item).itervalues()
        ready &= (quantity >= bag_item.quantity)


@auth.requires(
    auth.has_membership('Orders')
    or auth.has_membership('Admin')
    or auth.has_membership('Manager')
)
def ready():
    """
        args [order_id]
    """

    order = db.sale_order(request.args(0))
    if not order:
        raise HTTP(404)
    ready = True
    # check if the order items are in stock
    items = []
    for bag_item in db(db.bag_item.id_bag == order.id_bag.id).select():
        stock, quantity = item_stock(bag_item.id_item).itervalues()
        # consider previous orders
        order_items = db(
            (db.sale_order.id_bag == db.bag.id)
            & (db.bag_item.id_bag == db.bag.id)
            & (db.sale_order.id < order.id)
            & (db.sale_order.is_active == True)
            & (db.sale_order.id_sale == None)
            & (db.bag_item.id_item == bag_item.id_item.id)
        ).select()

        order_items_qty = 0
        for order_item in order_items:
            order_items_qty += order_item.bag_item.quantity

        item_ready = (quantity >= bag_item.quantity + order_items_qty)
        ready &= item_ready
        items.append(dict(bag_item=bag_item, ready=item_ready))

    buttons = [] if ready else [A(T('Purchase order'), _class="btn btn-primary", _href=URL('purchase', 'create_from_order', args=order.id))]
    form = SQLFORM.factory(buttons=buttons)
    if form.process(onvalidation=validate_ready).accepted:
        # notify the user
        pass

    return locals()


@auth.requires(
    auth.has_membership('Orders')
    or auth.has_membership('Admin')
    or auth.has_membership('Manager')
)
def delete():
    return common_delete('sale_order', request.args)


@auth.requires(
    auth.has_membership('Orders')
    or auth.has_membership('Admin')
    or auth.has_membership('Manager')
)
def client_order_options(row):
    td = TD()

    # view ticket
    td.append(option_btn('check', URL('sale_order', 'ready', args=row.id)))
    return td


@auth.requires(
    auth.has_membership('Orders')
    or auth.has_membership('Admin')
    or auth.has_membership('Manager')
)
def index():
    data = common_index('sale_order', ['is_ready'], dict(options_function=client_order_options, show_id=True))
    return locals()
