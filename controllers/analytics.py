# -*- coding: utf-8 -*-
#
# Author: Daniel J. Ramirez


import calendar
import datetime


def analize(queries):
    pass


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


def analyze(tablename, field, timestep, start_date):
    """ """




@auth.requires_membership("Analytics")
def index():
    start_date, end_date, timestep = daily_interval(11, 2015)
    print start_date, end_date, timestep
    print session.store

    purchases = db((db.purchase.id_store == session.store)
                & (db.purchase.is_done == True)
                & (db.purchase.created_on >= start_date)
                & (db.purchase.created_on < end_date)
                ).select()
    sales = db((db.sale.id_store == session.store)
                & (db.sale.created_on >= start_date)
                & (db.sale.created_on < end_date)
                ).select()

    current_date = start_date
    total = db.purchase.total.sum()
    s_total = db.sale.total.sum()
    day = 1
    purchase_totals = []
    sales_totals = []
    while current_date + timestep < end_date:
        purchases_total = db((db.purchase.id_store == session.store)
                    & (db.purchase.is_done == True)
                    & (db.purchase.created_on >= current_date)
                    & (db.purchase.created_on < current_date + timestep)
                    ).select(total).first()[total]
        purchase_totals.append(purchases_total or DQ(0))
        sales_total = db((db.sale.id_store == session.store)
                    & (db.sale.created_on >= current_date)
                    & (db.sale.created_on < current_date + timestep)
                    ).select(s_total).first()[s_total]
        sales_totals.append(sales_total or DQ(0))
        current_date += timestep
        day += 1
    print len(purchase_totals)
    print len(sales_totals)

    return locals()
