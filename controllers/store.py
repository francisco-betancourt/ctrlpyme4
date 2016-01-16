# -*- coding: utf-8 -*-
#
# Author: Daniel J. Ramirez


@auth.requires_membership('Admin')
def create():
    form = SQLFORM(db.store)
    if form.process().accepted:
        # insert store group
        db.auth_group.insert(role='Store %s' % form.vars.id)
        response.flash = T('form accepted')
        redirect(URL('index'))
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

def stores_options_function(row):
    """ Returns a column with an edit, delete and csd options"""
    td = TD()
    td.append(option_btn('pencil', URL('update', args=row.id)))
    td.append(option_btn('eye-slash', onclick='delete_rows("/%s", "", "")' % (row.id)))
    td.append(option_btn('key', URL('seals',args=row.id)))
    return td

@auth.requires_membership('Admin')
def index():
    data = common_index('store', ['name'], dict(show_id=True,options_function=stores_options_function)
    )
    return locals()

@auth.requires_membership('Admin')
def seal(s):
    store = db.store(request.args(0))
    if not store:
        raise HTTP(404,T('Store NOT FOUND'))
    db.store.id.readable=False
    form=SQLFORM(db.store,store,fields=['certificate','private_key'])
    print form[0],len(form[0])
    form[0].insert(2,DIV(
        LABEL(T('CSD password'),_class="control-label col-sm-3",_for="csdpass",_id="store_csdpass_label"),
        DIV(INPUT(_name="csdpass",_class="form-control string",_type="text"),_class="col-sm-9"),_class="form-group hidden",_id="store_csdpass__row"))

    return locals()
