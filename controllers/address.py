# -*- coding: utf-8 -*-
#
# Author: Daniel J. Ramirez

def create():

    form = SQLFORM(db.address)
    if form.process().accepted:
        response.flash = T('Address created')
        redirect(URL('list'))
    elif form.errors:
        response.flash = T('form has errors')

    return locals()


def get():
    pass


def update():
    """
    args: [address_id]
    """

    address = db.address(request.args(0))
    if not address:
        raise HTTP(404, T('Address NOT FOUND'))

    form = SQLFORM(db.address, address, showid=False)
    if form.process().accepted:
        response.flash = 'form accepted'
        redirect(URL('list'))
    elif form.errors:
        response.flash = 'form has errors'

    return locals()


def delete():
    """
    args: [id_1, id_2, ..., id_n]
    """

    if not request.args:
        raise HTTP(400)
    query = (db.payment_opt.id < 0)
    for arg in request.args:
        query |= (db.address.id == arg)
    db(query).delete()
    redirect(URL('list'))


def list():
    """ """
    addresses = db(db.address.id > 0).select()

    return locals()
