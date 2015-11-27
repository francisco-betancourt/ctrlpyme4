# -*- coding: utf-8 -*-
#
# Author: Daniel J. Ramirez

@auth.requires_membership('Client')
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
    # if not ready:
    #     form.errors.


def ready():
    """
        args [order_id]
    """

    order = db.sale_order(request.args(0))
    if not order:
        raise HTTP(404)
    ready = True
    # check if the order item are in stock
    for bag_item in db(db.bag_item.id_bag == order.id_bag.id).select():
        stock, quantity = item_stock(bag_item.id_item).itervalues()
        ready &= (quantity >= bag_item.quantity)

    form = SQLFORM.factory()
    if form.process(onvalidation=validate_ready).accepted:
        pass

    return locals()


def delete():
    return common_delete('name', request.args)


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
    rows = common_index('sale_order')
    data = super_table('sale_order', ['is_ready'], rows, options_function=client_order_options, show_id=True)
    return locals()
