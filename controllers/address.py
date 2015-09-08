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
    pass

def list():
    """
    #args: [company_id]

    """

    # company = db.company(request.args(0))
    # if not company:
    #     raise HTTP(404)

    addresses = db(db.address.id > 0).select()

    return locals()
