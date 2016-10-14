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

expiration_redirect()


if not 'Admin' in auth.user_groups.values():
    precheck()

import calendar
from datetime import timedelta, datetime, date
import random
import json
from gluon.storage import Storage

import analysis_utils



def get_month_interval(year, month):
    start_date = date(year, month, 1)
    end_date = start_date + timedelta(days=calendar.monthrange(year, month)[1])
    return start_date, end_date


def get_payments_in_range(start_date, end_date, id_store, id_seller=None):
    """ Returns all income payments in the specified time interval, performed in the specified store """
    payments = db(
        (db.payment.id_sale == db.sale.id)
        & ((db.sale.is_done == True) | (db.sale.is_deferred == True))
        & (db.sale.id_store == id_store)
        & (db.payment.created_on >= start_date)
        & (db.payment.created_on <= end_date)
        # do not consider wallet payments
        & (db.payment.id_payment_opt != get_wallet_payment_opt())
        & (db.payment.is_settled == True)
    ).iterselect(db.payment.ALL, orderby=db.payment.created_on)
    return payments


def get_paid_bags_in_range_as_payments(start_date, end_date, id_store):
    """ Return paid bags not related with sales """

    paid_bags = db(
        (db.bag.is_sold == False)
        & (db.bag.is_paid == True)
        & (db.bag.created_on >= start_date)
        & (db.bag.created_on <= end_date)
    ).iterselect()

    for paid_bag in paid_bags:
        yield Storage(amount=paid_bag.total, change_amount=0, created_on=paid_bag.created_on)


def _get_day_sales_data(day, id_store):
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



def stocks_table(item, Supert):

    def stock_row(row, fields):
        # the stock is from purchase

        if row.id_purchase:
            return A(T('Purchase'), _href=URL('purchase', 'get', args=row.id_purchase.id), _target='_blank')
        # stock is from inventory
        elif row.id_inventory:
            return A(T('Inventory'), _href=URL('inventory', 'get', args=row.id_inventory.id), _target='_blank')
        # stock is from credit note
        elif row.id_credit_note:
            return A(
                T('Credit note'),
                _href=URL(
                    'ticket', 'show_ticket',
                    vars=dict(id_credit_note=row.id_credit_note.id)
                ), _target='_blank'
            )
        elif row.id_stock_transfer:
            return A(
                T('Stock transfer'),
                _href=URL(
                    'stock_transfer', 'ticket',
                    vars=dict(id_stock_transfer=ow.id_stock_transfer.id)
                ), _target='_blank'
            )

    return Supert.SUPERT(
        (
            (db.stock_item.id_item == item.id) &
            (db.stock_item.id_store == session.store)
        ),
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

    precheck()

    import supert
    Supert = supert.Supert()

    item = db.item(request.args(0))
    if not item:
        session.info = T('Item not found')
        redirect(URL('default', 'index'))
    main_image = db(db.item_image.id_item == item.id).select().first()

    existence = 0
    stocks = None
    if item.has_inventory:
        existence = item_stock_qty(item, id_store=session.store)
        stocks = stocks_table(item, Supert)

    def out_custom_format(row, fields):
        link = ''
        if row.sale.id:
            link = A(
                '%s %s' % (T('Sale'), row.sale.consecutive),
                _href=URL(
                    'ticket', 'show_ticket', vars=dict(id_sale=row.sale.id)
                ),
                _target='_blank'
            )
        elif row.product_loss.id:
            link = A(
                '%s %s' % (T('Product loss'), row.product_loss.id),
                _href=URL('product_loss', 'get', args=row.product_loss.id),
                _target='_blank'
            )
        elif row.stock_transfer.id:
            link = A(
                '%s %s' % (T('Stock transfer'), row.stock_transfer.id),
                _href=URL(
                    'ticket', 'show_ticket',
                    vars=dict(id_stock_transfer=row.stock_transfer.id)
                ),
                _target='_blank'
            )
        return link


    def created_on_format(row, fields):
        date = None
        if row.sale.id:
            date = row.sale.created_on
        elif row.product_loss.id:
            date = row.prodcut_loss.created_on
        elif row.stock_transfer.id:
            date = row.stock_transfer.created_on
        return date


    # since services do not have stocks the following table is only applied to items with inventory
    # every stock removal is stored in a stock_item_removal_record
    outputs_t = None
    if item.has_inventory:
        outputs_t = Supert.SUPERT(
            (db.bag_item.id_bag == db.bag.id)
            & (db.bag_item.id_item == item.id)
            & (db.bag.id_store == session.store)
            & (db.bag.is_delivered == True)
            , select_fields=[
                db.bag.ALL, db.bag_item.ALL, db.sale.ALL,
                db.product_loss.ALL, db.product_loss.ALL, db.stock_transfer.ALL
            ]
            , select_args=dict(left=[
                db.sale.on((db.bag.id == db.sale.id_bag)),
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
                    fields=['bag_item.quantity'],
                    label_as=T('Quantity'),
                    custom_format=lambda r, f : DQ(r[f[0]], True, True)
                ),
                dict(
                    fields=[''],
                    label_as=T('Created on'),
                    custom_format=created_on_format
                ),
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
    else:
        outputs_t = Supert.SUPERT(
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
                    custom_format=lambda r, f : A(T('Sale') + ' %s' % r.sale.consecutive, _href=URL('ticket', 'show_ticket', vars=dict(id_sale=r.sale.id)), _target='_blank')
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

    out_inventories_t = Supert.SUPERT(
        (db.inventory_item.id_inventory == db.inventory.id)
        & (db.inventory_item.id_item == item.id)
        & (db.stock_item_removal.id_inventory_item == db.inventory_item.id)
        & (db.inventory.id_store == session.store)
        , select_args=dict(distinct=db.inventory.id, orderby=~db.inventory.id)
        , fields=[
            dict(
                fields=[''],
                label_as=T('Inventory'),
                custom_format=lambda r, f : A(
                    r.inventory.id, _href=URL('inventory', 'get', args=r.inventory.id), _target='_blank'
                )
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

    avg_days_in_shelf = get_wavg_days_in_shelf(item, session.store)

    return locals()


def dataset_format(label, data, f_color):
    fill_color = f_color
    if not f_color:
        fill_color = random_color_mix(PRIMARY_COLOR)
    return {
        'label': str(label),
        'data': data,
        'backgroundColor': hex_to_css_rgba(fill_color, .03),
        'borderColor': fill_color,
        'pointBorderColor': fill_color,
        'lineTension': .1
    }


@auth.requires_membership("Analytics")
def index():
    # if 'Admin' in auth.user_groups.values():
    #     precheck()

    precheck()


    access_stores = map(
        lambda s: int(s.replace('Store ', '')),
        filter(lambda x: x.startswith('Store '), MEMBERSHIPS.iterkeys())
    )
    stores = db(
        (db.store.id.belongs(access_stores)) &
        (db.store.is_active == True)
    ).iterselect()

    return dict(stores=stores)



def chart_data_template_for(time_mode, datasets, day_date):
    labels = None
    if time_mode == analysis_utils.TIME_MODE_DAY:
        labels = ["%d:00" % hour for hour in xrange(24)]
    elif time_mode == analysis_utils.TIME_MODE_WEEK:
        labels = [
            T("Monday"), T("Tuesday"), T("Wednesday"), T("Thursday"),
            T("Friday"), T("Saturday"), T("Sunday")
        ]
    elif time_mode == analysis_utils.TIME_MODE_MONTH:
        dom = calendar.monthrange(day_date.year, day_date.month)[1]
        labels = [day for day in xrange(1, dom + 1)]
    elif time_mode == analysis_utils.TIME_MODE_YEAR:
        labels = [
            T("January"), T("February"), T("March"), T("April"), T("May"),
            T("June"), T("July"), T("August"), T("September"), T("October"),
            T('November'), T('December')
        ]
    chart_data = {
        'labels': labels,
        'datasets': datasets
    }

    return chart_data



def get_date_from_request(request):
    try:
        year = int(request.vars.year)
        month = int(request.vars.month)
        day = int(request.vars.day)
    except:
        raise HTTP(400)


    # the good thing about this is that you we can receive a special request parameter to specify the time step and it will just work
    start_date = datetime(year, month, day, 0)

    t_step = analysis_utils.TIME_HOUR
    delta = timedelta(days=1)
    delta2 = None

    # Modify time range based the specified time mode
    try:
        time_mode = int(request.vars.t_mode)

        if time_mode == analysis_utils.TIME_MODE_WEEK:
            t_step = analysis_utils.TIME_DAY
            delta = timedelta(days=7)
            # the start day in this case is the first day of the current week
            start_date -= timedelta(days=start_date.weekday())

        if time_mode == analysis_utils.TIME_MODE_MONTH:
            # the start day in this case is the first day of the current month
            t_step = analysis_utils.TIME_DAY
            # days of the month
            start_date = datetime(start_date.year, start_date.month, 1)
            prev = start_date - timedelta(days=1)
            dom = calendar.monthrange(prev.year, prev.month)[1]
            delta = timedelta(days=dom)
            dom2 = calendar.monthrange(start_date.year, start_date.month)[1]
            delta2 = timedelta(days=dom2)

        if time_mode == analysis_utils.TIME_MODE_YEAR:
            t_step = analysis_utils.TIME_MONTH
            start_date = datetime(start_date.year, 1, 1)
            delta = timedelta(days=365)
    except:
        pass

    if not delta2:
        delta2 = delta

    end_date = start_date + delta2

    next_date = end_date
    prev_date = start_date - delta


    # set title
    title = str(start_date.strftime('%d/%m/%Y'))
    if start_date.strftime("%y/%j") == request.now.strftime("%y/%j"):
        title = T("Today")
    if time_mode == analysis_utils.TIME_MODE_WEEK:
        title = str("%s - %s" % (
            start_date.strftime('%d/%m/%Y'), end_date.strftime('%d/%m/%Y')
        ))
        if request.now >= start_date and request.now < end_date:
            title = T("This week")
    if time_mode == analysis_utils.TIME_MODE_MONTH:
        title = "%s %s" % (T(start_date.strftime("%B")), start_date.year)
    if time_mode == analysis_utils.TIME_MODE_YEAR:
        title = str(start_date.year)

    stores = []
    if request.vars.stores:
        # Only allowed stores
        for sid in request.vars.stores.split(','):
            if MEMBERSHIPS.get("Store %s" % sid) or MEMBERSHIPS.get('Admin'):
                stores.append(sid)
    else:
        stores = [session.store] if session.store else []


    return Storage(
        start_date=start_date,
        end_date=end_date,
        time_step=t_step,
        time_mode=time_mode,
        next_date=next_date,
        prev_date=prev_date,
        title=title,
        stores=stores
    )



@auth.requires_membership("Analytics")
def get_item_sales_data():
    date_data = get_date_from_request(request)
    id_item = request.args(0)


    raw_data = db(
        (db.sale.id_bag == db.bag.id) &
        (db.bag_item.id_bag == db.bag.id) &
        (db.bag_item.id_item == id_item) &
        (db.sale.id_store.belongs(date_data.stores)) &
        (db.sale.created_on >= date_data.start_date) &
        (db.sale.created_on < date_data.end_date)
    ).iterselect(
        db.bag_item.quantity, db.sale.created_on, orderby=db.sale.created_on
    )

    groups = analysis_utils.group_items(
        raw_data, date_data.start_date, date_data.end_date, date_data.time_step,
        lambda r : r.sale.created_on
    )
    rr = analysis_utils.reduce_groups(groups, dict(
        qty_total=dict(func=lambda r : float(r.bag_item.quantity))
    ))
    data = rr['qty_total']['results']
    total_sales = DQ(sum(rr['qty_total']['results']), True, True)
    chart_data = chart_data_template_for(
        date_data.time_mode,
        [dataset_format(T('Sold quantity'), data, ACCENT_COLOR)],
        date_data.start_date
    )

    return dict(
        chart_data=chart_data,
        current_date=date_data.start_date,
        next_date=date_data.next_date,
        prev_date=date_data.prev_date,
        title=date_data.title,

        total_sales=total_sales
    )




@auth.requires_membership("Analytics")
def get_day_sales_data():
    """ Returns relevant data for the specified day
        args: [year, month, day]
    """

    date_data = get_date_from_request(request)

    wallet_opt = get_wallet_payment_opt()

    sales_total = 0
    datasets = []
    for store_id in date_data.stores:
        data = db(
            (db.payment.id_sale == db.sale.id) &
            (db.sale.id_store == store_id) &
            (db.payment.id_payment_opt != wallet_opt.id) &
            (db.payment.created_on >= date_data.start_date) &
            (db.payment.created_on < date_data.end_date)
        ).iterselect(db.payment.ALL, orderby=db.sale.created_on)
        payments_groups = analysis_utils.group_items(
            data, date_data.start_date, date_data.end_date,
            date_data.time_step
        )

        rr = analysis_utils.reduce_groups(
            payments_groups, dict(
                payments_total=dict(
                    func=lambda r : float(r.amount - r.change_amount)
                )
            )
        )

        store_color = similar_color(ACCENT_COLOR, store_id * 100)

        sales_data = rr['payments_total']['results']
        dataset = dataset_format(
            T("Store %s") % store_id, sales_data, store_color
        )
        dataset['store_id'] = store_id
        datasets.append(dataset)
        sales_total += DQ(sum(sales_data), True)


    chart_sales_data = chart_data_template_for(
        date_data.time_mode, datasets, date_data.start_date
    )

    # important averages
    avg_sale_total = db.sale.total.avg()
    avg_sale_volume = db.sale.quantity.avg()
    total_items_sold = db.sale.quantity.sum()
    sales_data = db(
        (db.sale.id_store.belongs(date_data.stores)) &
        (db.sale.is_done == True) &
        (db.sale.created_on >= date_data.start_date) &
        (db.sale.created_on < date_data.end_date)
    ).select(avg_sale_total, avg_sale_volume, total_items_sold).first()
    avg_sale_volume = DQ(sales_data[avg_sale_volume] or 0, True)
    avg_sale_total = DQ(sales_data[avg_sale_total] or 0, True)
    # average items sell price
    avg_item_price = DQ(sales_total / (sales_data[total_items_sold] or 1), True)

    total_items_sold = DQ(sales_data[total_items_sold] or 0, True)

    expenses = db.bag_item.total_buy_price.sum()
    expenses = db(
        (db.sale.id_bag == db.bag.id) &
        (db.bag_item.id_bag == db.bag.id) &
        (db.sale.id_store.belongs(date_data.stores)) &
        (db.sale.created_on >= date_data.start_date) &
        (db.sale.created_on < date_data.end_date)
    ).select(expenses).first()[expenses]
    expenses = DQ(expenses or 0, True)

    profit = sales_total - expenses

    return dict(
        chart_data=chart_sales_data,
        current_date=date_data.start_date,
        next_date=date_data.next_date,
        prev_date=date_data.prev_date,
        title=date_data.title,

        avg_sale_total=avg_sale_total,
        avg_sale_volume=avg_sale_volume,
        total_items_sold=total_items_sold,
        avg_item_price=avg_item_price,
        sales_total=sales_total,
        profit=profit
    )






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
