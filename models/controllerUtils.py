def common_create(table_name, success_msg=''):
    form = SQLFORM(db[table_name])
    if form.process().accepted:
        response.flash = T(success_msg)
        redirect(URL('list'))
    elif form.errors:
        response.flash = T('form has errors')

    return dict(form=form)


def common_update(table_name, args, success_msg=''):
    """
    args: [measure_unit_id]
    """

    row = db[table_name](args(0))
    if not row:
        raise HTTP(404, T('row NOT FOUND'))

    form = SQLFORM(db[table_name], row)
    if form.process().accepted:
        response.flash = 'form accepted'
        redirect(URL('list'))
    elif form.errors:
        response.flash = 'form has errors'
    return dict(form=form)


def common_delete(table_name, args):
    """
    args: request.args
    """

    if not args:
        raise HTTP(400)
    query = (db[table_name].id < 0)
    for arg in args:
        query |= (db[table_name].id == arg)
    db(query).update(is_active=False)
    redirect(URL('list'))
