def common_create(table_name, success_msg='', _vars=None):
    form = SQLFORM(db[table_name])
    if form.process().accepted:
        response.flash = T(success_msg)
        redirection(URL('index'))
    elif form.errors:
        response.flash = T('form has errors')

    return dict(form=form)


def common_update(table_name, args, _vars=None, success_msg=''):
    """
    """

    next_url = _vars.next if _vars else URL('index')

    row = db[table_name](args(0))
    if not row:
        raise HTTP(404, T('row NOT FOUND'))

    form = SQLFORM(db[table_name], row)
    if form.process().accepted:
        response.flash = 'form accepted'
        redirect(next_url)
    elif form.errors:
        response.flash=  'form has errors'
    return dict(form=form, row=row)


def common_delete(table_name, args, _vars=None):
    """
    args: request.args
    """

    if not args:
        raise HTTP(400)
    query = (db[table_name].id < 0)
    for arg in args:
        query |= (db[table_name].id == arg)
    db(query).update(is_active=False)
    session.info = T('Item hidden')
    redirect(URL('index'))


def common_undelete(table_name, args, _vars=None):
    """
    args: request.args
    """

    if not args:
        raise HTTP(400)
    query = (db[table_name].id < 0)
    for arg in args:
        query |= (db[table_name].id == arg)
    db(query).update(is_active=True)
    session.info = T('Item now visible')
    redirect(URL('index'))


def common_index(table_name, fields=[], supert_vars={}):
    """
    """

    query = db[table_name].is_active == True
    return SUPERT(query, (db[table_name].ALL), fields=fields, **supert_vars)
