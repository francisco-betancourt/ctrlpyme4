# -*- coding: utf-8 -*-
#
# Author: Daniel J. Ramirez

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


def update():
    return common_update('name', request.args)


def delete():
    return common_delete('name', request.args)


def index():
    rows = common_index('name')
    return locals()
