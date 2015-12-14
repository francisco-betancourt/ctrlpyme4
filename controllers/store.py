# -*- coding: utf-8 -*-
#
# Author: Daniel J. Ramirez

store_extra_fields = ['extra1', 'extra2', 'extra3']


@auth.requires_membership('Admin')
def create():
    form = SQLFORM(db.store)
    if form.process().accepted:
        # insert store group
        db.auth_group.insert(role='Store_%s' % form.vars.id)
        response.flash = T('form accepted')
    elif form.errors:
        response.flash = T('form has errors')
    return dict(form=form)


@auth.requires_membership('Admin')
def get():
    store = db.store(request.args(0))
    if not store:
        raise HTTP(404, T('Store NOT FOUND'))

    store_config = db(db.store_config.id_store == store.id).select()
    store_roles = db(db.store_role.id_store == store.id).select()
    return locals()


@auth.requires_membership('Admin')
def update():
    return common_update('store', request.args, _vars=request.vars)


@auth.requires_membership('Admin')
def delete():
    return common_delete('store', request.args)


@auth.requires_membership('Admin')
def index():
    data = common_index('store', ['name'], dict(show_id=True, )
    )
    return locals()
