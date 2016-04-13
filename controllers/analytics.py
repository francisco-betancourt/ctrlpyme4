# -*- coding: utf-8 -*-
#
# Author: Daniel J. Ramirez


import calendar
from datetime import timedelta, datetime, date
import random
import json
from gluon.storage import Storage


hex_chars = [str(i) for i in range(0,9)] + ['A', 'B', 'C', 'D', 'E', 'F']


def get_month_interval(year, month):
    start_date = date(year, month, 1)
    end_date = start_date + timedelta(days=calendar.monthrange(year, month)[1])
    return start_date, end_date


def time_interval_query(tablename, start_date, end_date):
    return (db[tablename].created_on >= start_date) & (db[tablename].created_on < end_date)


def get_payments_in_range(start_date, end_date, id_store, id_seller=None):
    """ Returns all income payments in the specified time interval, performed in the specified store """
    payments = db(
        (db.payment.id_sale == db.sale.id)
        & ((db.sale.is_done == True) | (db.sale.is_defered == True))
        & (db.sale.id_store == id_store)
        & (db.payment.created_on >= start_date)
        & (db.payment.created_on <= end_date)
        # do not consider wallet payments
        & (db.payment.id_payment_opt != get_wallet_payment_opt())
        & (db.payment.is_settled == True)
    ).select(db.payment.ALL, orderby=db.payment.created_on)
    return payments


def get_day_sales_data(day, id_store):
    if not day:
        day = date(request.now.year, request.now.month, request.now.day)

    start_date = datetime(day.year, day.month, day.day, 0)
    end_date = start_date + timedelta(hours=23, minutes=59, seconds=59)

    data = [0 for i in range(24)]

    # income
    payments = get_payments_in_range(start_date, end_date, id_store)
    income = 0
    for payment in payments:
        income += payment.amount - payment.change_amount
        index = payment.created_on.hour
        data[index] += float(payment.amount - payment.change_amount)

    return data


@auth.requires_membership("Analytics")
def cash_out():
    """ Returns the specified date, information

        args: [year, month, day]
        vars: [id_cash_out]
    """

    year, month, day = None, None, None
    try:
        year, month, day = int(request.args(0)), int(request.args(1)), int(request.args(2))
    except:
        today = date.today()
        year, month, day = today.year, today.month, today.day
    if not year or not month or not day:
        raise HTTP(400)
    cash_out = db.cash_out(request.vars.id_cash_out)
    if not cash_out:
        raise HTTP(404)
    seller = cash_out.id_seller

    s_date = date(year, month, day)
    start_date = datetime(s_date.year, s_date.month, s_date.day, 0)
    end_date = start_date + CASH_OUT_INTERVAL

    if not (cash_out.created_on > start_date and cash_out.created_on < end_date):
        raise HTTP(405)

    payment_opts = db(db.payment_opt.is_active == True).select()
    # will be used to create a payments chart
    payment_opt_data = {}
    for payment_opt in payment_opts:
        payment_opt_data[str(payment_opt.id)] = {
            "color": random_color_mix(PRIMARY_COLOR), "label": payment_opt.name, "value": 0
        }

    sales = db((db.sale.id == db.sale_log.id_sale)
                & ((db.sale_log.sale_event == 'paid')
                | (db.sale_log.sale_event == 'defered'))
                & (db.sale.id_store == session.store)
                & (db.sale.created_by == seller.id)
                & time_interval_query('sale', start_date, end_date)
                ).select(db.sale.ALL, orderby=db.sale.id)
    payments_query = (db.payment.id < 0)

    total = 0
    total_cash = 0
    # set payments query and total sold quantity
    for sale in sales:
        payments_query |= db.payment.id_sale == sale.id
    payment_index = 0
    payments = db(payments_query).select(orderby=db.payment.id_sale)
    for sale in sales:
        sale.total_change = 0
        sale.payments = {}
        sale.payments_total = 0
        sale.change = 0
        for payment in payments[payment_index:]:
            if payment.id_sale != sale.id:
                break
            sale.payments_total += payment.amount
            if not sale.payments.has_key(str(payment.id_payment_opt.id)):
                sale.payments[str(payment.id_payment_opt.id)] = Storage(dict(amount=payment.amount, change_amount=payment.change_amount))
            else:
                _payment = sale.payments[str(payment.id_payment_opt.id)]
                _payment.amount += payment.amount
                _payment.change_amount += payment.change_amount
            if payment.id_payment_opt.allow_change:
                total_cash += payment.amount - payment.change_amount
            sale.total_change += payment.change_amount
            sale.change += payment.change_amount
            total += payment.amount - payment.change_amount
        sale.change = DQ(sale.change, True)
        payment_index += 1
    total = DQ(total, True)
    total_cash = DQ(total_cash, True)

    return locals()


def day_report_data(year, month, day):
    year = date.today().year if not year else year
    month = date.today().month if not month else month
    day = date.today().day if not day else day
    c_date = date(year, month, day)
    start_date = datetime(c_date.year, c_date.month, c_date.day, 0)
    end_date = start_date + timedelta(hours=23, minutes=59, seconds=59)

    sales_data = {
        'labels': [],
        'datasets': [{
            'data': []
        }]
    }
    for hour in range(24):
        sales_data['labels'].append('%d:00' % hour)
        sales_data['datasets'][0]['data'].append(0)

    # income
    payments = get_payments_in_range(start_date, end_date, session.store)
    income = 0
    for payment in payments:
        income += payment.amount - payment.change_amount
        index = payment.created_on.hour
        sales_data['datasets'][0]['data'][index] += float(payment.amount - payment.change_amount)
    sales_data = json.dumps(sales_data)

    # expenses
    purchases_total_sum =db.purchase.total.sum()
    expenses = db((db.purchase.id_store == session.store)
                & (db.purchase.is_done >= True)
                & (db.purchase.created_on >= start_date)
                & (db.purchase.created_on <= end_date)
                ).select(purchases_total_sum).first()[purchases_total_sum] or DQ(0)

    return locals()


#TODO check if the selected interval has already passed
def daily_interval(month, year):
    # Days Of The Month
    dotm = calendar.monthrange(year, month)[1]
    # the first day of the specified month and year
    end_date = date(year, month, 1)
    # a month previous to the specified month
    start_date = end_date - timedelta(days=dotm)
    start_date = date(start_date.year, start_date.month, 1)

    timestep = timedelta(days=1)

    return start_date, end_date, timestep


def monthly_analysis(query, tablename, field, month, year):
    """ """

    start_date, end_date, timestep = daily_interval(month, year)

    current_date = start_date
    data_set = []
    field_sum = db[tablename][field].sum()
    while current_date + timestep < end_date:
        partial_sum = db(query
                        & (db[tablename].created_on >= current_date)
                        & (db[tablename].created_on < current_date + timestep)
                        ).select(field_sum).first()[field_sum]
        data_set.append(partial_sum or DQ(0))
        current_date += timestep
    return data_set


def stocks_table(item):
    def stock_row(row, fields):
        tr = TR()
        # the stock is from purchase
        if row.id_purchase:
            tr.append(TD(A(T('Purchase'), _href=URL('purchase', 'get', args=row.id_purchase.id))))
        # stock is from inventory
        elif row.id_inventory:
            tr.append(TD(A(T('Inventory'), _href=URL('inventory', 'get', args=row.id_inventory.id))))
        # stock is from credit note
        elif row.id_credit_note:
            tr.append(TD(A(T('Credit note'), _href=URL('credit_note', 'get', args=row.id_credit_note.id))))
        elif row.id_stock_transfer:
            tr.append(TD(A(T('Stock transfer'), _href=URL('stock_transfer', 'ticket', args=row.id_stock_transfer.id))))

        tr.append(TD(DQ(row.purchase_qty, True)))
        tr.append(TD(row['created_on'].strftime('%d %b %Y, %H:%M')))

        #TODO  add link to employee analysis
        tr.append(TD(row.created_by.first_name + ' ' + row.created_by.last_name))

        return tr

    return super_table('stock_item', ['purchase_qty'], (db.stock_item.id_item == item.id) & (db.stock_item.id_store == session.store), row_function=stock_row, options_enabled=False, custom_headers=['concept', 'quantity', 'created on', 'created by'], paginate=False, orderby=~db.stock_item.created_on, search_enabled=False)


@auth.requires_membership("Analytics")
def item_analysis():
    """
        args: [id_item]
    """

    item = db.item(request.args(0))
    main_image = db(db.item_image.id_item == item.id).select().first()

    existence = item_stock(item, id_store=session.store)['quantity']

    stocks = stocks_table(item)

    sales = db(
        # (db.bundle_item.id_bundle == db.item.id)
        (db.bag_item.id_bag == db.bag.id)
        & (db.sale.id_bag == db.bag.id)
        & (db.sale.id_store == session.store)
        & (db.bag_item.id_item == item.id)
    ).select(db.sale.ALL, db.bag_item.ALL, orderby=~db.sale.created_on)
    stock_transfers = db(
        # (db.bundle_item.id_bundle == db.item.id)
        (db.bag_item.id_bag == db.bag.id)
        & (db.stock_transfer.id_bag == db.bag.id)
        & (db.stock_transfer.id_store_from == session.store)
        & (db.bag_item.id_item == item.id)
    ).select(db.stock_transfer.ALL, db.bag_item.ALL, orderby=~db.stock_transfer.created_on)

    return locals()


def dataset_format(label, data, f_color):
    fill_color = f_color
    if not f_color:
        fill_color = random_color_mix(PRIMARY_COLOR)
    return {
        'label': label,
        'data': data,
        'fillColor': hex_to_css_rgba(fill_color, .4),
        'strokeColor': fill_color,
        'pointColor': fill_color,
    }


def pie_data_format(records):
    data = []
    for record in records:
        f_color = record.c_color if record.c_color else random_color_mix(PRIMARY_COLOR)
        data.append(dict(
            value=record.c_value,
            label=record.c_label,
            color=f_color
        ))
    return data



@auth.requires_membership('Admin')
def dashboard():
    # store income
    current_month = request.now.month
    current_year = request.now.year
    year_start_date = date(current_year, 1, 1)
    start_date = date(current_year, current_month, 1)
    end_date = start_date + timedelta(days=30)

    sales_data = {
        'labels': ['%d:00' % hour for hour in range(24)],
        'datasets': []
    }

    items_data = {
        'labels': [],
        'datasets': []
    }

    stocks_sum = db.stock_item.stock_qty.sum()
    stores = db(db.store.is_active == True).select()
    for store in stores:
        store.c_color = random_color_mix(PRIMARY_COLOR)
        store.c_label = store.name
        # select this month payments
        payments = get_payments_in_range(start_date, end_date, store.id)
        store.c_value = 0
        for payment in payments:
            store.c_value += payment.amount - payment.change_amount
        store.c_value = str(DQ(store.c_value, True))
        sales_data['datasets'].append(
            dataset_format(store.name, get_day_sales_data(None, store.id), store.c_color)
        )

        # query items quantity monthly
        current_max_stock_date = year_start_date
        stocks_qty_data = []
        while current_max_stock_date < end_date:
            # add labels if this is the first time that we add data
            if not items_data['datasets']:
                items_data['labels'].append(current_max_stock_date.strftime('%B'))
            current_items = db(
                (db.stock_item.id_store == store.id)
                & (db.stock_item.created_on < current_max_stock_date)
                ).select(stocks_sum).first()[stocks_sum]
            stocks_qty_data.append(float(current_items or 0))
            # select next month assuming that the end date is the las month of the current year
            current_max_stock_date = date(current_max_stock_date.year, current_max_stock_date.month + 1, 1)
        items_data['datasets'].append(dataset_format(store.name, stocks_qty_data, store.c_color))

    script_stores_income = SCRIPT('var stores_income_data = %s;' % json.dumps(pie_data_format(stores)))
    script_stores_sales = SCRIPT('var stores_sales_data = %s;' % json.dumps(sales_data))
    script_stores_items = SCRIPT('var stores_items_data = %s;' % json.dumps(items_data))


    return locals()



@auth.requires_membership("Analytics")
def index():
    if auth.has_membership('Admin'):
        redirect(URL('dashboard'))

    day_data = day_report_data(None, None, None)
    income = day_data['income']
    expenses = day_data['expenses']
    today_sales_data_script = SCRIPT('today_sales_data = %s;' % day_data['sales_data'])

    employees_query = ((db.auth_membership.group_id == db.auth_group.id)
                    & (db.auth_user.id == db.auth_membership.user_id)
                    & (db.auth_user.registration_key == '')
                    & (db.auth_membership.user_id == db.auth_user.id)
                    & (db.auth_group.role == 'Sales checkout'))
    employees_data = SUPERT(employees_query, (db.auth_user.ALL), fields=[dict(fields=['first_name', 'last_name'], label_as=T('Name')), 'email'], options_func=lambda row : OPTION_BTN('attach_money', URL('cash_out', 'create', args=row.id)))

    return locals()


@auth.requires_membership("Analytics")
def get_calendar():
    today = date(request.now.year, request.now.month, request.now.day)
    selected_day = today
    if len(request.args) == 3:
        try:
            selected_day = date(int(request.args(0)), int(request.args(1)), int(request.args(2)))
        except:
            pass

    calendar.setfirstweekday(calendar.MONDAY)
    # print calendar.monthrange(selected_day.year, selected_day.month)
    day_names = calendar.day_name
    month_calendar = calendar.monthcalendar(selected_day.year, selected_day.month)

    # get selected month events
    # events array
    events = [[] for day in range(0, calendar.monthrange(today.year, today.month)[1])]
    events_added = [{} for day in range(0, calendar.monthrange(today.year, today.month)[1])]
    start_date, end_date = get_month_interval(today.year, today.month)
    # accounts payable
    accounts_payable = db(
        (db.account_payable.epd >= start_date)
        & (db.account_payable.epd < end_date)
        & (db.account_payable.is_settled == False)
    ).select(orderby=db.account_payable.epd)
    for payable in accounts_payable:
        day = payable.epd.day - 1
        if not events_added[day].has_key('account_payable'):
            events_added[day]['account_payable'] = dict(ids=[])
        events_added[day]['account_payable']['ids'].append(str(payable.id))

    accounts_receivable = db(
        (db.payment.epd >= start_date)
        & (db.payment.epd < end_date)
        & (db.payment.is_settled == False)
    ).select(orderby=db.payment.epd)
    for receivable in accounts_receivable:
        day = receivable.epd.day - 1
        if not events_added[day].has_key('account_receivable'):
            events_added[day]['account_receivable'] = dict(ids=[])
        events_added[day]['account_receivable']['ids'].append(str(receivable.id))
        # events[day - 1].append(Storage(name='Account receivable', icon='attach_money'))
    keys = [
        dict(key='account_payable', icon='money_off', name='Accounts payable'),
        dict(key='account_receivable', icon='attach_money', name='Accounts receivable'),
    ]
    for index, _events in enumerate(events_added):
        for _key in keys:
            key = _key['key']
            if _events.has_key(key):
                ids_str = ','.join(_events[key]['ids'])
                # print ids_str
                event_name = str(T(_key['name']))
                event_icon = _key['icon']
                events[index].append(
                    Storage(
                        name=event_name,
                        url=URL(key, 'index', vars=dict(ids=ids_str)),
                        icon=event_icon
                    )
                )

    events_script = SCRIPT('var events = %s' % json.dumps(events))
    return locals()
