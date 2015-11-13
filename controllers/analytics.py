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


def daily_analisis(query, tablename, field, month, year):
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


@auth.requires_membership("Analytics")
def index():
    start_date, end_date, timestep = daily_interval(11, 2015)


    query = (db.purchase.id_store == session.store) & (db.purchase.is_active == True)
    print daily_analisis(query, 'purchase', 'total', 11, 2015)

    return locals()
