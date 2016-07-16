# -*- coding: utf-8 -*-
#
# Copyright (C) 2016 Bet@net
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#
# Author Daniel J. Ramirez <djrmuv@gmail.com>


if not auth.has_membership('Admin'):
    precheck()

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


def get_paid_bags_in_range_as_payments(start_date, end_date, id_store):
    """ Return paid bags not related with sales """

    paid_bags = db(
        (db.bag.is_sold == False)
        & (db.bag.is_paid == True)
        & (db.bag.created_on >= start_date)
        & (db.bag.created_on <= end_date)
    ).select()

    for paid_bag in paid_bags:
        yield Storage(amount=paid_bag.total, change_amount=0, created_on=paid_bag.created_on)


def get_day_sales_data(day, id_store):
    if not day:
        day = date(request.now.year, request.now.month, request.now.day)

    start_date = datetime(day.year, day.month, day.day, 0)
    end_date = start_date + timedelta(hours=23, minutes=59, seconds=59)

    data = [0 for i in range(24)]

    # income
    payments = get_payments_in_range(start_date, end_date, id_store).as_list()
    for bag_pay in get_paid_bags_in_range_as_payments(start_date, end_date, id_store):
        payments.append(bag_pay)
    income = 0
    for payment in payments:
        income += payment['amount'] - payment['change_amount']
        index = payment['created_on'].hour
        data[index] += float(payment['amount'] - payment['change_amount'])

    return data


@auth.requires_membership("Analytics")
def sales_for_cash_out():
    """ Get the sales created in the specified cash out time interval

        args: [id_cash_out]
    """

    cash_out = db.cash_out(request.args(0))
    if not cash_out:
        raise HTTP(404)
    seller = cash_out.id_seller

    start_date = cash_out.start_date
    end_date = cash_out.end_date

    payment_opts = db(db.payment_opt.is_active == True).select()
    payment_opts_ref = {}
    # will be used to create a payments chart
    for payment_opt in payment_opts:
        payment_opt.c_value = 0
        payment_opt.c_label = payment_opt.name
        payment_opt.c_color = random_color_mix(PRIMARY_COLOR)
        payment_opts_ref[str(payment_opt.id)] = payment_opt

    sales = db(
        (db.sale.id == db.sale_log.id_sale)
        & (
            (db.sale_log.sale_event == SALE_PAID)
          | (db.sale_log.sale_event == SALE_DEFERED)
        )
        & (db.sale.id_store == session.store)
        & (db.sale.created_by == seller.id)
        & time_interval_query('sale', start_date, end_date)
    ).select(db.sale.ALL, orderby=~db.sale.id)

    total = 0
    total_cash = 0
    payment_index = 0

    # this will be the total amount of income
    payments = db(
        (db.sale_log.id_sale == db.sale.id)
        & (db.payment.id_sale == db.sale.id)
        & (
            (db.sale_log.sale_event == SALE_PAID)
            | (db.sale_log.sale_event == SALE_DEFERED)
        )
        & time_interval_query('sale', start_date, end_date)
    ).select(db.payment.ALL, orderby=~db.payment.id_sale)

    for sale in sales:
        sale.total_change = 0
        sale.payments = {}
        sale.payments_total = 0
        sale.change = 0

        payments_count = 0
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
            # payments that allow change are considered cash.
            if payment.id_payment_opt.allow_change:
                total_cash += payment.amount - payment.change_amount
            sale.total_change += payment.change_amount
            sale.change += payment.change_amount
            total += payment.amount - payment.change_amount
            payments_count += 1

        sale.change = DQ(sale.change, True)
        payment_index += payments_count
    total = DQ(total, True)
    total_cash = DQ(total_cash, True)

    if not cash_out.is_done:
        cash_out.sys_cash = total_cash
        cash_out.update_record()

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
    payments = get_payments_in_range(start_date, end_date, session.store).as_list()
    income = 0

    # get paid bags
    for paid_bag in get_paid_bags_in_range_as_payments(start_date, end_date, session.store):
        payments.append(paid_bag)

    for payment in payments:
        income += payment['amount'] - payment['change_amount']
        index = payment['created_on'].hour
        sales_data['datasets'][0]['data'][index] += float(payment['amount'] - payment['change_amount'])
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
        # the stock is from purchase

        if row.id_purchase:
            return A(T('Purchase'), _href=URL('purchase', 'get', args=row.id_purchase.id))
        # stock is from inventory
        elif row.id_inventory:
            return A(T('Inventory'), _href=URL('inventory', 'get', args=row.id_inventory.id))
        # stock is from credit note
        elif row.id_credit_note:
            return A(T('Credit note'), _href=URL('credit_note', 'get', args=row.id_credit_note.id))
        elif row.id_stock_transfer:
            return A(T('Stock transfer'), _href=URL('stock_transfer', 'ticket', args=row.id_stock_transfer.id))

    return SUPERT(
        (db.stock_item.id_item == item.id) & (db.stock_item.id_store == session.store),
        fields=[
            {
                'fields': ['id'],
                'label_as': T('Concept'),
                'custom_format': stock_row
            },
            {
                'fields': ['purchase_qty'],
                'label_as': T('Quantity'),
                'custom_format': lambda r, f : DQ(r[f[0]], True, True)
            },
            'created_on',
            {
                'fields': ['created_by'],
                'label_as': T('Created by'),
                'custom_format': lambda r, f : "%s %s" % (r[f[0]].first_name, r[f[0]].last_name)
            }
        ], options_enabled=False, searchable=False, global_options=[],
        title=T('Input')
    )


from item_utils import get_wavg_days_in_shelf

@auth.requires_membership("Analytics")
def item_analysis():
    """
        args: [id_item]
    """

    item = db.item(request.args(0))
    if not item:
        session.info = T('Item not found')
        redirect(URL('default', 'index'))
    main_image = db(db.item_image.id_item == item.id).select().first()

    existence = 0
    stocks = None
    if item.has_inventory:
        existence = item_stock(item, id_store=session.store)['quantity']
        stocks = stocks_table(item)

    def out_custom_format(row, fields):
        link = ''
        if row.sale.id:
            link = A('%s %s' % (T('Sale'), row.sale.consecutive), _href=URL('sale', 'ticket', args=row.sale.id))
        elif row.product_loss.id:
            link = A('%s %s' % (T('Product loss'), row.product_loss.id), _href=URL('product_loss', 'get', args=row.product_loss.id))
        elif row.stock_transfer.id:
            link = A('%s %s' % (T('Stock transfer'), row.stock_transfer.id), _href=URL('stock_transfer', 'ticket', args=row.stock_transfer.id))
        return link


    # since services do not have stocks the following table is only applied to items with inventory
    # every stock removal is stored in a stock_item_removal_record
    outputs_t = None
    if item.has_inventory:
        outputs_t = SUPERT(
            (db.bag_item.id_bag == db.bag.id)
            & (db.bag_item.id_item == item.id)
            & (db.stock_item_removal.id_bag_item == db.bag_item.id)
            & (db.bag.id_store == session.store)
            , select_fields=[
                db.bag.ALL, db.stock_item_removal.ALL, db.sale.ALL,
                db.product_loss.ALL, db.product_loss.ALL, db.stock_transfer.ALL
            ]
            , select_args=dict(left=[
                db.sale.on(db.bag.id == db.sale.id_bag),
                db.product_loss.on(db.bag.id == db.product_loss.id_bag),
                db.stock_transfer.on(db.bag.id == db.stock_transfer.id_bag)
            ]),
            fields=[
                dict(
                    fields=[''],
                    label_as=T('Concept'),
                    custom_format=out_custom_format
                ),
                dict(
                    fields=['stock_item_removal.qty'],
                    label_as=T('Quantity'),
                    custom_format=lambda r, f : DQ(r[f[0]], True, True)
                ),
                'bag.created_on',
                dict(
                    fields=['bag.created_by'],
                    label_as=T('Created by'),
                    custom_format=lambda r, f : "%s %s" % (r[f[0]].first_name, r[f[0]].last_name)
                )
            ],
            base_table_name='stock_item_removal',
            title=T('Output'), searchable=False, options_enabled=False,
            global_options=[]
        )
    else:
        outputs_t = SUPERT(
            (db.bag_item.id_bag == db.bag.id)
            & (db.bag_item.id_item == item.id)
            & (db.bag.id_store == session.store)
            , select_fields=[
                db.bag.ALL, db.sale.ALL, db.bag_item.ALL
            ]
            , select_args=dict(left=[
                db.sale.on(db.bag.id == db.sale.id_bag)
            ]),
            fields=[
                dict(
                    fields=[''],
                    label_as=T('Concept'),
                    custom_format=lambda r, f : A(T('Sale') + ' %s' % r.sale.consecutive, _href=URL('sale', 'ticket', args=r.sale.id))
                ),
                dict(
                    fields=['bag_item.quantity'],
                    label_as=T('Quantity'),
                    custom_format=lambda r, f : DQ(r[f[0]], True, True)
                ),
                'bag.created_on',
                dict(
                    fields=['bag.created_by'],
                    label_as=T('Created by'),
                    custom_format=lambda r, f : "%s %s" % (r[f[0]].first_name, r[f[0]].last_name)
                )
            ],
            base_table_name='bag_item',
            title=T('Output'), searchable=False, options_enabled=False,
            global_options=[]
        )

    out_inventories_t = SUPERT(
        (db.inventory_item.id_inventory == db.inventory.id)
        & (db.inventory_item.id_item == item.id)
        & (db.stock_item_removal.id_inventory_item == db.inventory_item.id)
        & (db.inventory.id_store == session.store)
        , select_args=dict(distinct=db.inventory.id, orderby=~db.inventory.id)
        , fields=[
            dict(
                fields=[''],
                label_as=T('Inventory'),
                custom_format=lambda r, f : A(r.inventory.id, _href=URL('inventory', 'get', args=r.inventory.id))
            ),
            dict(
                fields=['stock_item_removal.qty'],
                label_as=T('Quantity'),
                custom_format=lambda r, f : DQ(r[f[0]], True, True)
            ),
            'inventory.created_on',
            dict(
                fields=['inventory.created_by'],
                label_as=T('Created by'),
                custom_format=lambda r, f : "%s %s" % (r[f[0]].first_name, r[f[0]].last_name)
            )
        ],
        base_table_name='stock_item_removal',
        title=T('Missing items'), searchable=False, options_enabled=False,
        global_options=[]
    )

    wavg_days_in_shelf = get_wavg_days_in_shelf(item, session.store)

    return locals()


def dataset_format(label, data, f_color):
    fill_color = f_color
    if not f_color:
        fill_color = random_color_mix(PRIMARY_COLOR)
    return {
        'label': label,
        'data': data,
        'backgroundColor': hex_to_css_rgba(fill_color, .4),
        'borderColor': fill_color,
        'pointBorderColor': fill_color,
    }


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
        payments = get_payments_in_range(start_date, end_date, store.id).as_list()
        store.c_value = 0
        for payment in payments:
            store.c_value += payment['amount'] - payment['change_amount']
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
            # select next month assuming that the end date is the last month of the current year
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

    store_group = db(db.auth_group.role == 'Store %s' % session.store).select().first()
    checkout_group = db(db.auth_group.role == 'Sales checkout').select().first()
    # query the employees with current store membership
    store_employees_ids = [r.id for r in db(
          (db.auth_user.id == db.auth_membership.user_id)
        & (db.auth_membership.group_id == store_group.id)
    ).select(db.auth_user.id)]
    # employees with store membership and checkout membership
    employees_query = (
        (db.auth_user.id == db.auth_membership.user_id)
        & (db.auth_user.id.belongs(store_employees_ids))
        & (db.auth_membership.group_id == checkout_group.id)
        & (db.auth_user.registration_key == '')
    )
    employees_data = SUPERT(
        employees_query,
        select_fields=[db.auth_user.ALL],
        fields=[
            dict(
                fields=['first_name', 'last_name'],
                label_as=T('Name')
            ), 'email'
        ],
        options_func=lambda row : (
            OPTION_BTN('attach_money',
                URL('cash_out', 'create', args=row.id),
                title=T('cash out')
            ),
            OPTION_BTN('archive', URL('cash_out', 'index',
                args=row.id), title=T('previous cash outs'))
            )
        , global_options=[], title=T("Cash out")
    )

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
