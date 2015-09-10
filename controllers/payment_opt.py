# -*- coding: utf-8 -*-
#
# Author: Daniel J. Ramirez

def create():
    """ """

    form = SQLFORM(db.payment_opt)
    if form.process().accepted:
        response.flash = T('Payment option Added')
        redirect(URL('list'))
    elif form.errors:
        response.flash = T('form has errors')

    return dict(form=form)


def get():
    pass


def update():
    payment_opt = db.payment_opt(request.args(0))
    if not payment_opt:
        raise HTTP(404, T('Payment Option NOT FOUND'))

    form = SQLFORM(db.payment_opt, payment_opt)
    if form.process().accepted:
        response.flash = 'form accepted'
        redirect(URL('list'))
    elif form.errors:
        response.flash = 'form has errors'
    return dict(form=form)


def delete():
    """
    args: [id_1, id_2, ..., id_n]
    """

    if not request.args:
        raise HTTP(400)
    query = (db.payment_opt.id < 0)
    for arg in request.args:
        query |= (db.payment_opt.id == arg)
    db(query).update(is_active=False)
    redirect(URL('list'))


def list():
    """ """

    payment_opts = db((db.payment_opt.id > 0) & (db.payment_opt.is_active == True)).select()

    return locals()
