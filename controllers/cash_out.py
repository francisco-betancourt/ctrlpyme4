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


expiration_redirect()
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
            redirect(
                URL('details', args=last_cash_out.id)
            )
        session.info = dict(
            text=T('Cash out interval is set to %s day(s)') % CASH_OUT_INTERVAL.days,
            btn=dict(
                href=URL(
                    'details', args=last_cash_out.id
                ),
                text=btn_text
            )
        )
        redirect(URL('index'))

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

    redirect(URL('details', args=new_cash_out_id ))



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
        URL('details', args=cash_out.id, vars=dict(_print=True)),
        '_blank'
    )

    redirect(URL('index'))


@auth.requires_membership("Cash out")
def details():
    """ Get the sales created in the specified cash out time interval

        args: [id_cash_out]
    """

    cash_out = db.cash_out(request.args(0))
    if not cash_out:
        raise HTTP(404)
    seller = cash_out.id_seller

    start_date = cash_out.start_date
    end_date = cash_out.end_date

    payment_opts = db(db.payment_opt.id > 0).select()
    payment_opts_ref = {}
    # will be used to create a payments chart
    for payment_opt in payment_opts:
        payment_opt.c_value = 0
        payment_opt.c_label = payment_opt.name
        payment_opt.c_color = similar_color(
            ACCENT_COLOR, payment_opt.id * 771
        )
        payment_opts_ref[str(payment_opt.id)] = payment_opt


    def payments_iter():
        return db(
            (db.sale_log.id_sale == db.sale.id)
          & (db.payment.id_sale == db.sale.id)
          & (
              (db.sale_log.sale_event == SALE_PAID)
              | (db.sale_log.sale_event == SALE_DEFERED)
          )
          & (db.sale.created_by == seller.id)
          & (db.sale.id_store == session.store)
          & time_interval_query('sale', start_date, end_date)
        ).iterselect(db.payment.ALL, orderby=~db.payment.id_sale)

    def sales_generator():
        total = 0
        total_cash = 0

        # this will be the total amount of income
        payments = payments_iter()

        sale = None
        for payment in payments:
            if payment.id_sale and payment.id_sale != sale:
                if sale:
                    sale.total = sale.total - (sale.discount or 0)
                    yield sale
                sale = payment.id_sale
                sale.total_change = 0
                sale.payments = {}
                sale.payments_total = 0
                sale.change = 0

            sale.payments_total = (sale.payments_total or 0) + payment.amount
            payment_opt_key = str(payment.id_payment_opt.id)
            if not sale.payments.has_key(payment_opt_key):
                sale.payments[payment_opt_key] = Storage(dict(
                    amount=payment.amount, change_amount=payment.change_amount
                ))
            else:
                _payment = sale.payments[payment_opt_key]
                _payment.amount += payment.amount
                _payment.change_amount += payment.change_amount
            sale.total_change += payment.change_amount
            sale.change += payment.change_amount
        if sale:
            sale.total = sale.total - (sale.discount or 0)
        yield sale

    sales = sales_generator()

    # this is ugly but it only happens when the cash out is created
    if cash_out.sys_total < 0:
        payments = payments_iter()

        total = 0
        total_cash = 0
        for payment in payments:
            # payments that allow change are considered cash.
            if payment.id_payment_opt.allow_change:
                total_cash += payment.amount - payment.change_amount
            total += payment.amount - payment.change_amount

        cash_out.sys_total = total
        cash_out.sys_cash = total_cash
        cash_out.update_record()

    total = DQ(cash_out.sys_total, True)
    total_cash = DQ(cash_out.sys_cash, True)

    return locals()



@auth.requires_membership('Cash out')
def archive():
    """
        args: [seller_id]
    """

    import supert
    Supert = supert.Supert()

    seller = db.auth_user(request.args(0))
    if not seller:
        raise HTTP(404)
    if not auth.has_membership(None, seller.id, 'Sales checkout'):
        raise HTTP(404)

    def cash_out_options(row):
        options = supert.OPTION_BTN(
            'assignment', URL('details', args=row.id),
            title=T('details')
        )

        return options

    def status_format(r, f):
        diff = DQ(abs(r.sys_cash - (r.cash or 0)), True)
        if r.sys_cash == r.cash:
            return I(_class='status-circle bg-success'), A(T("Ok"),
                _href=URL('index', args=seller.id, vars=dict(status="ok"))
            ),
        elif r.sys_cash < r.cash:
            return I(_class='status-circle bg-success'), A(T("Added money"),
                _href=URL('index', args=seller.id, vars=dict(status="added"))
            ), B(" ($ %s)" % diff)
        elif r.sys_cash > r.cash:
            return I(_class='status-circle bg-danger'), A(T("Missing money"),
                _href=URL('index', args=seller.id, vars=dict(status="missing"))
            ), B(" ($ %s)" % diff)

    status = request.vars.status
    query = (db.cash_out.id_seller == seller.id) & (db.cash_out.is_done == True)
    if status == 'missing':
        query &= db.cash_out.sys_cash > db.cash_out.cash
    elif status == 'added':
        query &= db.cash_out.sys_cash < db.cash_out.cash
    elif status == 'ok':
        query &= db.cash_out.sys_cash == db.cash_out.cash

    data = Supert.SUPERT(
        query
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



@auth.requires_membership('Cash out')
def index():
    import supert
    Supert = supert.Supert()

    store_group = db(
        db.auth_group.role == 'Store %s' % session.store
    ).select().first()
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
    employees_data = Supert.SUPERT(
        employees_query,
        select_fields=[db.auth_user.ALL],
        fields=[
            dict(
                fields=['first_name', 'last_name'],
                label_as=T('Name')
            ), 'email'
        ],
        options_func=lambda row : (
            supert.OPTION_BTN('attach_money',
                URL('cash_out', 'create', args=row.id),
                title=T('cash out')
            ),
            supert.OPTION_BTN('archive', URL('cash_out', 'archive',
                args=row.id), title=T('previous cash outs'))
            )
        , global_options=[], title=T("Sellers")
    )

    return dict(employees=employees_data)
