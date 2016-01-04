# -*- coding: utf-8 -*-
#
# Author: Daniel J. Ramirez


# def client_order_row(row, fields):
#     tr = TR()
#     # sale status
#     last_log = db(db.sale_log.id_sale == row.id).select().last()
#     sale_event = last_log.sale_event if last_log else None
#     tr.append(TD(T(sale_event or 'Unknown')))
#     for field in fields:
#         tr.append(TD(row[field]))
#     return tr


def client_order_options(row):
    td = TD()

    # view ticket
    td.append(option_btn('', URL('bag', 'ticket', args=row.id_bag.id), action_name=T('View ticket')))
    return td


@auth.requires_membership('Clients')
def client_profile():
    orders = db(db.sale_order.id_client == auth.user.id).select()
    orders_data = None
    orders_data = super_table('sale_order', ['is_ready'], (db.sale_order.id_client == auth.user.id), options_function=client_order_options, show_id=True, selectable=False)
    return locals()


@auth.requires_membership('Admin')
def create_client():
    form = SQLFORM(db.auth_user)
    if form.process().accepted:
        clients_group = db(db.auth_group.role == 'Clients').select().first()
        if clients_group:
            db.auth_membership.insert(user_id=form.vars.id, group_id=clients_group.id)
        response.flash = T('Client created')
        redirect(URL('user', 'clients'))
        # redirection()
    elif form.errors:
        response.flash = T('Error in form')
    return dict(form=form)


@auth.requires_membership('Admin')
def create():
    form = SQLFORM(db.auth_user)
    if form.process().accepted:
        employee_group = db(db.auth_group.role == 'Employee').select().first()
        if employee_group:
            db.auth_membership.insert(user_id=form.vars.id, group_id=employee_group.id)
        response.flash = T('Employee created')
        redirect(URL('user'))
        # redirection()
    elif form.errors:
        response.flash = T('Error in form')
    return dict(form=form)


@auth.requires_membership('Admin')
def get():
    pass


@auth.requires_membership('Admin')
def get_employee():
    """
        args: [id_user]
    """
    employee = db.auth_user(request.args(0))
    if not employee:
        raise HTTP(404)

    stores = db(db.store.is_active == True).select()

    sale_groups = db(db.auth_group.role.contains(['Sales bags', 'Sales checkout', 'Sales invoices', 'Sales delivery', 'Sales returns'])).select()
    item_groups = db(db.auth_group.role.contains(['Items info', 'Items management', 'Items prices'])).select()
    access_groups = db(db.auth_group.role.contains(['Purchases', 'Inventories', 'Manager'])).select()

    perm_groups = [
        {
            'name': T('Sales'),
            'groups': sale_groups
        },
        {
            'name': T('Items'),
            'groups': item_groups
        },
        {
            'name': T('Access'),
            'groups': access_groups
        }
    ]

    return locals()


@auth.requires_membership('Admin')
def remove_employee_membership():
    """
        args: [id_user, group_name]
    """

    employee = db.auth_user(request.args(0))
    group = db(db.auth_group.role == request.args(1).replace('_', ' ')).select().first()

    if not employee or not group:
        raise HTTP(404)

    db((db.auth_membership.group_id == group.id)
     & (db.auth_membership.user_id == employee.id)
    ).delete()
    # db.auth_membership.insert(user_id=employee.id, group_id=group.id)

    return locals()


@auth.requires_membership('Admin')
def add_employee_membership():
    """
        args: [id_user, group_name]
    """

    employee = db.auth_user(request.args(0))
    group = db(db.auth_group.role == request.args(1).replace('_', ' ')).select().first()

    if not employee or not group:
        raise HTTP(404)

    db.auth_membership.insert(user_id=employee.id, group_id=group.id)

    return locals()


@auth.requires_membership('Admin')
def update():
    return common_update('auth_user', request.args)


@auth.requires_membership('Admin')
def delete():
    return common_delete('auth_user', request.args)


@auth.requires(auth.has_membership('Admin'))
def clients():
    """ List of clients """

    client_group = db(db.auth_group.role == 'Clients').select().first()
    query = (db.auth_membership.user_id == db.auth_user.id) & (db.auth_membership.group_id == client_group.id) & (db.auth_membership.user_id != auth.user.id)
    data = super_table('auth_user', ['first_name','last_name','email'], query, options_function=lambda row: TD(option_btn('pencil', URL('get_client', args=row.id)))
    )
    return locals()


@auth.requires_membership('Admin')
def index():
    """ List of employees """

    employee_group = db(db.auth_group.role == 'Employee').select().first()
    query = (db.auth_membership.user_id == db.auth_user.id) & (db.auth_membership.group_id == employee_group.id) & (db.auth_membership.user_id != auth.user.id)
    data = super_table('auth_user', ['first_name','last_name','email'], query, options_function=lambda row: TD(option_btn('pencil', URL('get_employee', args=row.id)))
    )
    return locals()


@auth.requires_login()
def post_login():
    # set the current bag, if theres is one
    if not session.current_bag or db.bag(session.current_bag).id_store != session.store:
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
    session.current_bag = None
    redirect(URL('default', 'index'))


@auth.requires_login()
def store_selection():
    """ """

    if session.store or not auth.has_membership('Employee'):
        redirect(URL('default', 'index'))

    user_stores_query = (db.store.id < 0)
    if auth.has_membership('Admin'):
        user_stores_query = (db.store.is_active == True)
    else:
        user_stores_query = (db.store.is_active == True)
        user_store_groups = db((db.auth_membership.group_id == db.auth_group.id)
                             & (db.auth_group.role.contains('Store '))
                             & (db.auth_membership.user_id == auth.user.id)
                             ).select(db.auth_group.role)
        extra_query = (db.store.id < 0)
        for user_store_group in user_store_groups:
            store_id = int(user_store_group.role.split(' ')[1])
            extra_query |= (db.store.id == store_id)
        user_stores_query = (user_stores_query & (extra_query))

    form = SQLFORM.factory(
        Field('store', "reference store", label=T('Store'), requires=IS_IN_DB(db(user_stores_query), 'store.id', '%(name)s'))
    )

    if form.process().accepted:
        session.store = form.vars.store
        redirect(URL('user', 'post_login'))
        response.flash = "You are in store %s" % db(form.vars.store).name
    elif form.errors:
        response.flash = 'form has errors'
    return dict(form=form)
