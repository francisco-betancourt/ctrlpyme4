# -*- coding: utf-8 -*-
#
# Copyright (C) <2016>  <Daniel J. Ramirez>
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


precheck()

from datetime import timedelta, datetime


@auth.requires_membership('Cash out')
def create():
    """ args: [id_seller] """

    # cash
    last_cash_out = db(
        db.cash_out.id_seller == request.args(0)
    ).select(orderby=db.cash_out.end_date).last()

    start_date = datetime(1500, 1, 1) if not last_cash_out else last_cash_out.end_date
    end_date = request.now

    # the time between cash outs is lower than the cash out interval
    if end_date - start_date < CASH_OUT_INTERVAL:
        btn_text = T('View last cash out')
        if not last_cash_out.is_done:
            btn_text = T('Edit current cash out')
        session.info = dict(
            text=T('Cash out interval is set to %s day(s)') % CASH_OUT_INTERVAL.days,
            btn=dict(
                href=URL(
                    'analytics', 'sales_for_cash_out', args=last_cash_out.id
                ),
                text=btn_text
            )
        )
        redirect(URL('analytics', 'index'))

    seller = db.auth_user(request.args(0))
    if not seller:
        raise HTTP(404)
    if not auth.has_membership(None, seller.id, 'Sales checkout'):
        raise HTTP(405)

    new_cash_out_id = db.cash_out.insert(
        id_seller=seller.id,
        start_date=start_date,
        end_date=end_date
    )

    redirect(URL('analytics', 'sales_for_cash_out', args=new_cash_out_id ))


@auth.requires_membership('Cash out')
def update():
    """ args: [id_cash_out]
        vars: [target <cash, notes>, value ]
    """
    if not request.vars.target in ['cash', 'notes']:
        raise HTTP(405)
    value = request.vars.value
    update_dict = {request.vars.target: request.vars.value}
    res = db((db.cash_out.id == request.args(0))
           & (db.cash_out.is_done == False)
    ).validate_and_update(**update_dict)
    if res.errors:
        raise HTTP(400)
    else:
        value = DQ(value, True) if request.vars.target == 'cash' else value
        return dict(target=request.vars.target, value=value)


@auth.requires_membership('Cash out')
def done():
    """ args: [id_cash_out] """

    value = request.vars.value
    cash_out = db.cash_out(request.args(0))
    if not cash_out:
        raise HTTP(404)
    cash_out.is_done = True
    cash_out.update_record()

    session.info = INFO(
        T('Cash out done'),
        T('Print report'),
        URL('analytics', 'sales_for_cash_out', args=cash_out.id, vars=dict(_print=True)),
        '_blank'
    )

    redirect(URL('analytics', 'index'))


@auth.requires_membership('Cash out')
def index():
    """
        args: [seller_id]
    """

    seller = db.auth_user(request.args(0))

    if not auth.has_membership(None, seller.id, 'Sales checkout'):
        raise HTTP(404)

    def cash_out_options(row):
        options = OPTION_BTN(
            'assignment', URL('analytics', 'sales_for_cash_out', args=row.id)
        )

        return options

    def status_format(r, f):
        if r.sys_cash == r.cash:
            return T("Ok")
        elif r.sys_cash < r.cash:
            return T("Added money")
        elif r.sys_cash < r.cash:
            return T("Missing money")

    data = SUPERT(
        (db.cash_out.id_seller == seller.id) & (db.cash_out.is_done == True)
        , fields=[
            'start_date', 'end_date', 'sys_cash', 'cash', 'is_done',
            dict(
                fields=['id'],
                label_as=T('Status'),
                custom_format=status_format
            )
        ]
        , options_func=cash_out_options
        , global_options=[]
        , searchable=False
    )

    return locals()
