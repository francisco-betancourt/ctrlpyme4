# -*- coding: utf-8 -*-
#
# Author: Daniel J. Ramirez

def create():
    """ """

    form = SQLFORM(db.payment_opt)
    if form.process().accepted:
        response.flash = 'form accepted'
    elif form.errors:
        response.flash = 'form has errors'

    return dict(form=form)


def get():
    pass


def update():
    pass


def delete():
    pass


def list():
    """ """

    payment_opts = db(db.payment_opt.id > 0).select()

    return locals()
