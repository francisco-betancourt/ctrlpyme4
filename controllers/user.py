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
    if not session.current_bag or db(session.current_bag).id_store != session.store:
        some_active_bag = db((db.bag.is_active == True)
                           & (db.bag.completed == False)
                           & (db.bag.created_by == auth.user.id)
                           & (db.bag.id_store == session.store)
                           ).select().first()
        if some_active_bag:
            session.current_bag = some_active_bag.id
    redirect(URL('default', 'index'))


def post_logout():
    session.store = None
    redirect(URL('default', 'index'))


@auth.requires_login()
def store_selection():
    """ Admin does not need to select a store """

    if session.store or not auth.has_membership('Employee'):
        redirect(URL('default', 'index'))

    form = SQLFORM.factory(
        Field('store', "reference store", label=T('Store'), requires=IS_IN_DB(db, 'store.id', '%(name)s'))
    )

    if form.process().accepted:
        session.store = form.vars.store
        redirect(URL('user', 'post_login'))
        response.flash = "You are in store %s" % db(form.vars.store).name
    elif form.errors:
        response.flash = 'form has errors'
    return dict(form=form)
