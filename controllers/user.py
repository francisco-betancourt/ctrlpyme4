# -*- coding: utf-8 -*-
#
# Author: Daniel J. Ramirez

def create():
    return common_create('auth_user')


def get():
    pass


def update():
    return common_update('auth_user', request.args)


def delete():
    return common_delete('auth_user', request.args)


def index():
    rows = db(db.auth_user.id > 0).select()
    return locals()
