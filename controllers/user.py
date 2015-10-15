# -*- coding: utf-8 -*-
#
# Author: Daniel J. Ramirez


@auth.requires_membership('Admin')
def create():
    return common_create('auth_user')


@auth.requires_membership('Admin')
def get():
    pass


@auth.requires_membership('Admin')
def update():
    return common_update('auth_user', request.args)


@auth.requires_membership('Admin')
def delete():
    return common_delete('auth_user', request.args)


@auth.requires_membership('Admin')
def index():
    rows = db(db.auth_user.id > 0).select()
    data = super_table('auth_user', ['email'], rows)
    return locals()


@auth.requires_login()
def post_login():
    # set the current bag, if theres is one
    if not session.current_bag:
        some_active_bag = db((db.bag.is_active == True)
                           & (db.bag.completed == False)
                           & (db.bag.created_by == auth.user.id)
                           ).select().first()
        if some_active_bag:
            session.current_bag = some_active_bag.id
    redirect(URL('default', 'index'))
