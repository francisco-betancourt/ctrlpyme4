# -*- coding: utf-8 -*-
#
# Author: Daniel J. Ramirez

store_extra_fields = ['extra1', 'extra2', 'extra3']


@auth.requires_membership('Admin')
def create():
    form = SQLFORM(db.store)
    if form.process().accepted:
        for extra_field in store_extra_fields:
            db.store_config.insert(id_store=form.vars.id, param_name=extra_field, param_value="", param_type="string")
        response.flash = 'form accepted'
    elif form.errors:
        response.flash = 'form has errors'
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
    data = common_index('store', ['name'], dict(show_id=True, extra_options=lambda row : [
                option_btn('', URL('get', args=row.id), action_name=T("View"))
            ]))
    return locals()
