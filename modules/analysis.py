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


from datetime import timedelta, date, datetime
from gluon import current



TIME_HOUR = 0
TIME_DAY = 1
TIME_WEEK = 2
TIME_MONTH = 3
TIME_YEAR = 4



def group_time(interval):
    if interval == TIME_HOUR:
        return timedelta(hours=1)
    elif interval == TIME_DAY:
        return timedelta(days=1)
    elif interval == TIME_WEEK:
        return timedelta(weeks=1)
    elif interval == TIME_MONTH:
        return timedelta(days=30)
    elif interval == TIME_YEAR:
        return timedelta(weeks=52)


def created_on_range_query(target, start_date, end_date):
    db = current.db

    return (target.created_on >= start_date) & (target.created_on < end_date)


def avg_time_between_sales(start_date, end_date, group_by=TIME_HOUR):
    db = current.db
    

    sales = db( 
        (db.sale.created_on >= start_date) &
        (db.sale.created_on < end_date) 
    ).iterselect(
        db.sale.created_on, 
        orderby=db.sale.created_on
    )

    avg = 0
    last_date = sales.first().created_on
    count = 1
    for sale in sales:
        avg += (sale.created_on - last_date).total_seconds()
        last_date = sale.created_on
        count += 1

    avg /= 3600
    avg /= count




def normalized_date(_date, interval):
    
    year = _date.year
    month = _date.month
    day = _date.day
    hour = _date.hour

    if interval == TIME_DAY:
        hour = 0
    elif interval == TIME_WEEK:
        day = day // 7
    elif interval == TIME_MONTH:
        day = 0
    elif interval == TIME_YEAR:
        month = 0

    return datetime(
        year=year,
        month=month,
        day=day,
        hour=hour,
        minute=0,
        second=0
    )

    



def group_items(records, start_date, end_date, t_step, creation_date_f=None):
    """ group a set of records using their creation date, the final result
        is a set of groups from start_date to end_date grouped by time
        intervals of t_step

        if creation_date_f is specified the record creation date will be
        obtained by the result of that function 
    """

    t_step_dt = group_time(t_step)
    current_group = []
    current_limit_date = start_date + t_step_dt

    for record in records:
        created_on = None
        if creation_date_f:
            created_on = creation_date_f(record)
        else:
            created_on = record.created_on 
        
        # yield emptys until we get to the relevant date

        while current_limit_date < normalized_date(created_on, t_step):
            yield []
            current_limit_date += t_step_dt

        if created_on > current_limit_date:
            yield current_group
            current_group = []
            current_limit_date += t_step_dt
        current_group.append(record)
    yield current_group

    # yield emptys until we reach the end_date
    while current_limit_date < end_date:
        current_limit_date += t_step_dt
        yield []



def get_data_groups(table, start_date, end_date, t_step=TIME_HOUR, 
    id_store=None, id_user=None
):
    """ For the specified table, return the records created in the specified time interval grouped by the specified t_step"""

    db = current.db

    if not ('created_on' in table.fields and 'created_by' in table.fields):
        raise CP_AnalysisError(
            'the table does not meet the analizable requirements'
        )

    query = created_on_range_query(table, start_date, end_date)
    if id_store and 'id_store' in table.fields:
        query &= table.id_store == id_store
    if id_user:
        query &= table.created_by == id_user

    data = db(query).iterselect()

    return group_items(data, start_date, end_date, t_step)



def reduce_groups(data, functions):
    """ for every group in the data list, perform every function in the functions dict, and store a single result

        functions is a dictionary like:
        {
            'value_name': {
                'func': function,
                'results': []   # this will be added by this function
            }
        }

        the functions must be a function that takes a register and returns a
        single numeric value.

        the results list will contain the reduced value for every group
    """

    index = 0
    for group in data:
        for record in group:
            for f in functions.itervalues():
                if not f.get('results'):
                    f['results'] = []
                while len(f['results']) < index + 1:
                    f['results'].append(0)
                f['results'][index] += f['func'](record)
        index += 1

    # fill remaining values
    for f in functions.itervalues():
        if not f.get('results'):
            f['results'] = []
        while len(f['results']) < index + 1:
            f['results'].append(0)

    return functions



def get_month_interval(year, month):
    """ Returns a time interval covering the specified month and year
        (1/month/year - last_day_of_month/month/year) 
    """

    start_date = date(year, month, 1)
    end_date = start_date + timedelta(days=calendar.monthrange(year, month)[1])

    return start_date, end_date