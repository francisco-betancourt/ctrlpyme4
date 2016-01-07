# -*- coding: utf-8 -*-
#
# Author: Daniel J. Ramirez


import calendar
import datetime
import random
import json


hex_chars = [str(i) for i in range(0,9)] + ['A', 'B', 'C', 'D', 'E', 'F']


def time_interval_query(tablename, start_date, end_date):
    return (db[tablename].created_on >= start_date) & (db[tablename].created_on < end_date)


def analize(queries):
    pass


@auth.requires_membership("Analytics")
def cash_out():
    """ Returns the specified date, information

        args: [year, month, day]
        vars: [id_seller]
    """

    year, month, day = None, None, None
    try:
        year, month, day = int(request.args(0)), int(request.args(1)), int(request.args(2))
    except:
        today = datetime.date.today()
        year, month, day = today.year, today.month, today.day
    if not year or not month or not day:
        raise HTTP(400)
    seller = db.auth_user(request.vars.id_seller)
    if not seller:
        raise HTTP(404)

    date = datetime.date(year, month, day)
    start_date = datetime.datetime(date.year, date.month, date.day, 0)
    end_date = start_date + datetime.timedelta(hours=23, minutes=59, seconds=59)

    sales_data = db((db.sale.id == db.sale_log.id_sale)
                    & (db.sale_log.sale_event == 'paid')
                    & (db.sale.id_store == session.store)
                    & (db.sale.created_by == seller.id)
                    & time_interval_query('sale', start_date, end_date)
                    ).select()

    payment_opts = db(db.payment_opt.is_active == True).select()

    # will be used to create a pay chart
    payment_opt_data = {}
    for payment_opt in payment_opts:
        payment_opt_data[str(payment_opt.id)] = {
            "color": random_color_mix(PRIMARY_COLOR), "label": payment_opt.name, "value": 0
        }
    change_color = "#333"

    return locals()



def day_report_data(year, month, day):
    year = datetime.date.today().year if not year else year
    month = datetime.date.today().month if not month else month
    day = datetime.date.today().day if not day else day

    date = datetime.date(year, month, day)


    start_date = datetime.datetime(date.year, date.month, date.day, 0)
    end_date = start_date + datetime.timedelta(hours=23, minutes=59, seconds=59)

    # income
    sales_total_sum = db.sale.total.sum()
    income = db((db.sale.id_store == session.store)
                & (db.sale.created_on >= start_date)
                & (db.sale.created_on <= end_date)
                ).select(sales_total_sum).first()[sales_total_sum] or DQ(0)
    # expenses
    purchases_total_sum =db.purchase.total.sum()
    expenses = db((db.purchase.id_store == session.store)
                & (db.purchase.is_done >= True)
                & (db.purchase.created_on >= start_date)
                & (db.purchase.created_on <= end_date)
                ).select(purchases_total_sum).first()[purchases_total_sum] or DQ(0)

    sales_data = {
        'labels': [],
        'datasets': [{
            'data': []
        }]
    }

    for hour in range(23):
        sales_data['labels'].append('%d:00' % hour)
        start_hour = datetime.datetime(date.year, date.month, date.day, hour)
        end_hour = start_hour + datetime.timedelta(hours=1)
        hour_sales = db((db.sale.id_store == session.store)
                      & (db.sale.created_on >= start_hour)
                      & (db.sale.created_on < end_hour)
                     ).select(sales_total_sum).first()[sales_total_sum] or 0
        sales_data['datasets'][0]['data'].append(float(hour_sales))
    sales_data = json.dumps(sales_data)
    print sales_data
    return locals()



@auth.requires_membership("Analytics")
def day_report():
    """ Returns the specified date, information

        args: [year, month, day]
    """

    return day_report_data(int(request.args(0)), int(request.args(1)), int(request.args(2)))

    year, month, day = None, None, None
    try:
        year, month, day = int(request.args(0)), int(request.args(1)), int(request.args(2))
    except:
        raise HTTP(400)
    if not year or not month or not day:
        raise HTTP(400)

    date = datetime.date(year, month, day)

    start_date = datetime.datetime(date.year, date.month, date.day, 0)
    end_date = start_date + datetime.timedelta(hours=23, minutes=59, seconds=59)

    # income
    sales_total_sum = db.sale.total.sum()
    income = db((db.sale.id_store == session.store)
                & (db.sale.created_on >= start_date)
                & (db.sale.created_on <= end_date)
                ).select(sales_total_sum).first()[sales_total_sum] or 0
    # expenses
    purchases_total_sum = db.purchase.total.sum()
    expenses = db((db.purchase.id_store == session.store)
                & (db.purchase.is_done >= True)
                & (db.purchase.created_on >= start_date)
                & (db.purchase.created_on <= end_date)
                ).select(purchases_total_sum).first()[purchases_total_sum] or 0
    return locals()


@auth.requires_membership("Analytics")
def daily_report():
    """ """

    today = datetime.date.today()
    redirect(URL('day_report', args=[today.year, today.month, today.day]))


#TODO check if the selected interval has already passed
def daily_interval(month, year):
    # Days Of The Month
    dotm = calendar.monthrange(year, month)[1]
    # the first day of the specified month and year
    end_date = datetime.date(year, month, 1)
    # a month previous to the specified month
    start_date = end_date - datetime.timedelta(days=dotm)
    start_date = datetime.date(start_date.year, start_date.month, 1)

    timestep = datetime.timedelta(days=1)

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

        for field in fields:
            tr.append(TD(row[field]))
        tr.append(TD(row['created_on'].strftime('%d %b %Y, %H:%M')))

        #TODO  add link to employee analysis
        tr.append(TD(row.created_by.first_name + ' ' + row.created_by.last_name))

        return tr

    return super_table('stock_item', ['purchase_qty'], (db.stock_item.id_item == item.id) & (db.stock_item.id_store == session.store), row_function=stock_row, options_enabled=False, custom_headers=['concept', 'quantity', 'created on', 'created by'], paginate=False, orderby=~db.stock_item.created_on)


@auth.requires_membership("Analytics")
def item_analysis():
    """
        args: [id_item]
    """

    item = db.item(request.args(0))
    main_image = db(db.item_image.id_item == item.id).select().first()

    existence = item_stock(item, id_store=session.store)['quantity']

    # purchases = None
    stocks = stocks_table(item)

    sales = db(
        (db.bag_item.id_bag == db.bag.id)
        & (db.sale.id_bag == db.bag.id)
        & (db.sale.id_store == session.store)
        & (db.bag_item.id_item == item.id)
    ).select(db.sale.ALL, db.bag_item.ALL, orderby=~db.sale.created_on)

    return locals()


@auth.requires_membership("Analytics")
def index():
    start_date, end_date, timestep = daily_interval(11, 2015)

    query = (db.purchase.id_store == session.store) & (db.purchase.is_active == True)
    # print monthly_analysis(query, 'purchase', 'total', 11, 2015)

    day_data = day_report_data(None, None, None)
    income = day_data['income']
    expenses = day_data['expenses']
    today_sales_data_script = SCRIPT('today_sales_data = %s;' % day_data['sales_data'])

    employees_query = ((db.auth_membership.group_id == db.auth_group.id)
                    & (db.auth_membership.user_id == db.auth_user.id)
                    & (db.auth_group.role == 'Sales'))
    employees_data = super_table('auth_user', ['email'], employees_query, show_id=True, selectable=False, options_function=lambda row: option_btn('', URL('cash_out', vars={'id_seller': row.id}), T('Cash out')))

    return locals()
