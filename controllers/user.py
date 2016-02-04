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


@auth.requires_membership('Employee')
def employee_profile():
    return dict()


def profile():
    if auth.has_membership('Clients'):
        redirect(URL('client_profile'))
    elif auth.has_membership('Employee'):
        redirect(URL('employee_profile'))


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
        new_client = db.auth_user(form.vars.id)
        new_client.is_client = True
        # add a new wallet to client
        new_client.id_wallet = new_wallet()
        new_client.update_record()
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
        redirect(URL('get_employee', args=form.vars.id))
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

    permission_cards = WORKFLOW_DATA[COMPANY_WORKFLOW].cards()

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
def set_access_card():
    user = db.auth_user(request.args(0))
    if not user:
        raise HTTP(404)
    if not auth.has_membership(None, user.id, 'Employee'):
        raise HTTP(401)
    card_index = int(request.args(1))

    try:
        card_data = WORKFLOW_DATA[COMPANY_WORKFLOW].card(card_index)
        # remove all memberships
        memberships_query = (db.auth_membership.user_id == user.id)
        for store_group in db(db.auth_group.role.like('Store %')).select():
            memberships_query &= (db.auth_membership.group_id != store_group.id)
        employee_group = db(db.auth_group.role == 'Employee').select().first()
        if employee_group:
            memberships_query &= (db.auth_membership.group_id != employee_group.id)
        db(memberships_query).delete()

        # add access card memberships
        for role in card_data.groups():
            group = db(db.auth_group.role == role).select().first()
            if group:
                auth.add_membership(group_id=group.id, user_id=user.id)
        user.access_card_index = card_index
        user.update_record()
    except:
        import traceback as tb
        tb.print_exc()
        raise HTTP(500)

    return dict()


@auth.requires_membership('Admin')
def update():
    return common_update('auth_user', request.args)


@auth.requires_membership('Admin')
def delete():
    user = db.auth_user(request.args(0))
    if not user:
        raise HTTP(404)

    user.is_active = False
    user.registration_key = 'blocked'
    user.update_record()

    redirection()


@auth.requires_membership('Admin')
def ban():
    user = db.auth_user(request.args(0))
    if not user:
        raise HTTP(404)

    # ban client
    if auth.has_membership(user_id=user.id, role='Clients'):
        user.registration_key = 'blocked' if not user.registration_key else ''

    user.update_record()

    redirect(URL('clients'))
    # redirection()


def client_options_function(row):
    td = TD()
    td.append(option_btn('pencil', URL('get_client', args=row.id)))
    ban_text = T('Ban')
    if row.registration_key == 'blocked':
        ban_text = T('Unban')
    td.append(option_btn('ban', URL('ban', args=row.id, vars=dict(_next=URL('user', 'clients'))), ' ' + ban_text))

    return td


@auth.requires(auth.has_membership('Admin'))
def clients():
    """ List of clients """

    client_group = db(db.auth_group.role == 'Clients').select().first()
    query = (db.auth_membership.user_id == db.auth_user.id) & (db.auth_membership.group_id == client_group.id) & (db.auth_membership.user_id != auth.user.id)
    data = super_table('auth_user', ['first_name','last_name','email'], query, options_function=client_options_function
    )
    return locals()


@auth.requires_membership('Admin')
def index():
    """ List of employees """

    employee_group = db(db.auth_group.role == 'Employee').select().first()
    query = (db.auth_membership.user_id == db.auth_user.id) & (db.auth_membership.group_id == employee_group.id) & (db.auth_membership.user_id != auth.user.id) & (db.auth_user.registration_key == '')
    data = super_table('auth_user', ['first_name','last_name','email'], query, options_function=lambda row: TD(option_btn('pencil', URL('get_employee', args=row.id)), option_btn('eye-slash', URL('delete', args=row.id, vars=dict(_next=URL('user', 'index')))) )
    )
    return locals()


@auth.requires_login()
def post_login():
    if auth.has_membership('Clients'):
        auto_bag_selection()

    redirection()


def post_logout():
    session.store = None
    session.current_bag = None
    redirect(URL('default', 'index'))


@auth.requires_login()
def store_selection():
    """ """

    if not auth.has_membership('Employee') or session.store:
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

    stores = db(user_stores_query).select()
    if len(stores) == 1:
        session.store = stores.first().id
        auto_bag_selection()
        redirection()

    form = SQLFORM.factory(
        Field('store', "reference store", label=T('Store'), requires=IS_IN_DB(db(user_stores_query), 'store.id', '%(name)s'))
    )

    if form.process().accepted:
        session.store = form.vars.store
        response.flash = T("You are in store") + " %s" % db.store(form.vars.store).name

        auto_bag_selection()

        redirection()
    elif form.errors:
        response.flash = T('form has errors')
    return dict(form=form)
