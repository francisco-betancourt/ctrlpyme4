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

precheck()


import json
from uuid import uuid4
from datetime import date, timedelta
from item_utils import item_discounts, apply_discount, item_stock_qty, remove_stocks, undo_stock_removal, reintegrate_stock
from constants import *

import sale_utils


def ticket():
    redirect( URL( 'ticket', 'get', vars=dict(id_sale=request.args(0)) ) )


def valid_sale(sale):
    if not sale.created_by.id == auth.user.id:
        raise HTTP(401)
    if not sale:
        raise HTTP(404)
    if sale.is_done:
        session.info = {
            'text': T('Sale has been paid'),
            'btn': {'text': T('View ticket'), 'target': '_blank' , 'href': URL('sale', 'ticket', args=sale.id)}
        }
        redirect(URL('default', 'index'))
    return True



@auth.requires_membership('Sales checkout')
def add_payment():
    """ Adds a payment related to a bag, with the specified payment option
        args: [id_sale, id_payment_opt]
    """

    from cp_errors import CP_PaymentError

    sale = db.sale(request.args(0))
    valid_sale(sale)
    if sale.id_bag.is_paid:
        raise HTTP(405, "The bag has been paid and its complete now.")

    payment_opt = db.payment_opt(request.args(1))
    if not payment_opt:
        raise HTTP(404, T('Could not find the specified payment option.'))

    # do not accept stripe payment opt
    if payment_opt.name == 'stripe':
        raise HTTP(405)

    # check if the payments total is lower than the total
    s = db.payment.amount.sum()
    payments_total = db(db.payment.id_sale == sale.id).select(s).first()[s]
    if not payments_total < sale.total:
        raise HTTP(400,
            T('Total already covered by the current payments.')
        )

    # only accept credit payments for registered clients
    if payment_opt.credit_days > 0 and not sale.id_client:
        raise HTTP(500,
            T('Payments with credit days are only available for registered clients.')
        )


    try:
        new_payment_id = sale_utils.add_payment(sale, payment_opt)
        new_payment = db.payment(new_payment_id)

        return dict(
            payment_opt=payment_opt, payment=new_payment,
            payments_total=payments_total
        )
    except CP_PaymentError as e:
        raise HTTP(400, str(e) )


@auth.requires_membership('Sales checkout')
def update_payment():
    """
        args: [id_sale, id_payment]
        vars: [amount, account, wallet_code, delete]
    """

    from cp_errors import CP_PaymentError


    sale = db.sale(request.args(0))
    valid_sale(sale)
    # cant modify payments for bag paid online
    if sale.id_bag.is_paid:
        raise HTTP(405)

    payment = db((db.payment.id == request.args(1))
               & (db.payment.id_sale == sale.id)).select().first()
    if not payment:
        raise HTTP(404)
    if not payment.is_updatable:
        raise HTTP(405)

    # Accept updates for certain amount of time (7 minutes) when the sale has been defered, this prevents sellers to modify previous sale payments
    if (request.now - payment.created_on).seconds / 60.0 / 7.0 > 1:
        if sale.is_deferred:
            payment.is_updatable = False
            payment.update_record()
            raise HTTP(405)

    try:
        new_amount = D(request.vars.amount or payment.amount)
    except:
        raise HTTP(417)

    delete_payment = bool(request.vars.delete)

    payment_data = dict(
        amount=D(request.vars.amount or payment.amount),
        account=request.vars.account or payment.account,
        wallet_code=request.vars.wallet_code or payment.wallet_code
    )

    d = sale_utils.modify_payment(sale, payment, payment_data, delete_payment)
    extra_updated_payments = d.get('updated_payments')
    payments_total = d.get('payments_total')

    return dict(updated=extra_updated_payments, payments_total=payments_total)



@auth.requires_membership('Sales checkout')
def cancel():
    """ args: [id_sale] """

    sale = db.sale(request.args(0))
    valid_sale(sale)
    # cannot cancel a defered sale, without credit note and all that stuff
    if sale.is_deferred or sale.id_bag.is_paid:
        raise HTTP(405)

    # return wallet payments
    wallet_opt = get_wallet_payment_opt()
    payments = db((db.payment.id_payment_opt == wallet_opt.id) & (db.payment.id_sale == sale.id)).select()
    for payment in payments:
        wallet = db(
            db.wallet.wallet_code == payment.wallet_code
        ).select().first()
        if wallet:
            wallet.balance += payment.amount
            wallet.update_record()

    # delete the bag and all its bag items
    db(db.bag_item.id_bag == sale.id_bag.id).delete()
    db(db.bag.id == sale.id_bag.id).delete()
    db(db.payment.id_sale == sale.id).delete()
    db(db.sale_order.id_bag == sale.id_bag.id).delete()
    sale.delete_record()

    session.info = T('Sale canceled')
    redirect(URL('default', 'index'))


@auth.requires_membership('Sales checkout')
def update():
    """ This is the main interface to modify sale data, and its payments
        args: [id_sale] """

    sale = db.sale(request.args(0))
    if not sale:
        raise HTTP(404)

    valid_sale(sale)

    clients = db(db.auth_user.is_client == True).select()

    payments = db(db.payment.id_sale == sale.id).select()
    payment_options = db((db.payment_opt.is_active == True) & (db.payment_opt.name != 'stripe')).select(orderby=~db.payment_opt.allow_change)

    bag_items = db(db.bag_item.id_bag == sale.id_bag.id).select()

    # remove 0 amount payments and calculate the payments total
    payments_total = 0
    for payment in payments:
        if payment.amount <= 0:
            payment.delete_record()
            continue
        payments_total += payment.amount - payment.change_amount
    remaining = sale.total - payments_total
    payments = db(db.payment.id_sale == sale.id).select()

    return locals()


@auth.requires_membership('Sales checkout')
def set_sale_client():
    """ set the specified sale client
        args: [id_sale, id_client] """

    sale = db.sale(request.args(0))
    valid_sale(sale)
    # we cannot modify defered sale or online purchased bag
    if sale.is_deferred or sale.id_bag.is_paid:
        raise HTTP(405)
    client = db((db.auth_user.is_client == True)
                & (db.auth_user.registration_key == '')
                & (db.auth_user.id == request.args(1))
                ).select().first()
    wallet = None
    #TODO remove credit payments if the client is None
    if not client:
        sale.id_client = None
    # the user changed the sale client
    # elif client != sale.id_client:
    #     # refund wallet
    #     wallet = db.wallet(sale.id_client.id_wallet.id)
    #     payments_sum = db.payment.amount.sum()
    #     payments_amount = db(
    #         (db.payment.wallet_code == wallet.wallet_code)
    #         & (db.payment.id_sale == sale.id)
    #     ).select(payments_sum).first()[payments_sum]
    #     print payments_amount
    else:
        sale.id_client = client.id
        if client.id_wallet:
            wallet = client.id_wallet
            wallet = db.wallet(wallet)
            wallet.balance = str(DQ(wallet.balance, True))
    sale.update_record()

    return dict(wallet=wallet)



@auth.requires_membership('Sales checkout')
def select_bag():
    """ args: [id_bag] """

    bag = check_bag_owner(request.args(0))
    return bag_selection_return_format(bag)


@auth.requires_membership('Sales checkout')
def create():
    """ args: [ id_bag ] """

    bag = db.bag(request.args(0))
    if not bag:
        raise HTTP(404)
    # theres a sale asociated with the specified bag
    if db(db.sale.id_bag == bag.id).select().first():
        session.info = T('Bag already sold')
        redirect(URL('default', 'index'))

    new_sale_id = sale_utils.new(bag, session.store, request.now, auth.user)

    redirect(URL('update', args=new_sale_id))


@auth.requires_membership('Sales checkout')
def complete():
    """
        args: [id_sale]
    """

    from cp_errors import CP_PaymentError, CP_OutOfStockError


    sale = db.sale(request.args(0))
    valid_sale(sale)

    try:
        sale_utils.complete(sale)
    except (CP_PaymentError, CP_OutOfStockError) as e:
        session.info = str(e)
        redirect(URL('update', args=sale.id))

    session.info = INFO(T("Sale created"), T("undo"), URL('undo', args=sale.id))
    #TODO check company workflow
    if not auth.has_membership('Sales delivery'):
        redirect(URL('scan_ticket'))
    # deliver sale
    else:
        sale_utils.deliver(sale)
        redirect(
            URL( 'ticket', 'get', vars=dict(id_sale=sale.id, next_url=URL('default', 'index'), _print=True) )
        )


@auth.requires_membership('Sales checkout')
def defer():
    """ args: [id_sale] """

    from sale_utils import create_sale_event, SALE_DEFERED

    sale = db.sale(request.args(0))
    valid_sale(sale)
    if sale.id_bag.is_paid:
        raise HTTP(405)

    payments = db(db.payment.id_sale == sale.id).select()
    sale_utils.verify_payments(payments, sale, False)

    payments = db(db.payment.id_sale == sale.id).iterselect()
    # Since this sale will be edited later we have to make sure that current payments will not be modified, so we set them as non updatable
    for payment in payments:
        payment.is_updatable = False;
        payment.update_record()

    # if defered function is called on a defered sale, we skip the following steps
    if not sale.is_deferred:
        sale.is_deferred = True
        create_sale_event(sale, SALE_DEFERED)
        sale.update_record()

        # create sale order based on the defered sale
        db.sale_order.insert(
            id_store=session.store, id_bag=sale.id_bag.id, id_sale=sale.id,
            is_for_defered_sale=True
        )

    url = URL('default', 'index')
    redirect(URL('ticket', 'get', vars=dict(id_sale=sale.id, next_url=url)))


@auth.requires_membership('Sales delivery')
def deliver():
    """
        this function presents just a deliver button, used when the checkout
        users cant deliver products.

        args: [sale_id]
    """

    sale = db.sale(request.args(0))
    if not sale:
        raise HTTP(404)
    # find all the sold items whose purchase had serial numbers
    bag_items = db(db.bag_item.id_bag == sale.id_bag.id).iterselect()
    resume = DIV()
    for bag_item in bag_items:
        resume.append(bag_item.product_name + str(DQ(bag_item.quantity, True)) + ' x $' + str(DQ(bag_item.sale_price, True)))

    form = SQLFORM.factory(
        submit_button=T("Deliver")
    )
    form[0].insert(0, sqlform_field("", "", resume))

    if form.process().accepted:
        sale_utils.deliver(sale)

    return locals()


@auth.requires(auth.has_membership('Sales checkout'))
def undo():
    """ Undo a sale, only available for 5 minutes after the sale creation
        args: [sale_id]
    """

    sale = db(
        (db.sale.id == request.args(0))
        & (db.sale.created_by == auth.user.id)
        & (db.sale.is_done == True)
    ).select().first()

    # undo timeout
    err = ''
    if not sale:
        err = T('Sale not found')
    if request.now > sale.created_on + timedelta(minutes=5):
        print sale.created_on
        err = T('Its too late to undo it')
    if err:
        session.info = err
        redirect(URL('default', 'index'))

    # return wallet payments
    for payment in db(db.payment.id_payment_opt == get_wallet_payment_opt()).select():
        wallet = db(db.wallet.wallet_code == payment.wallet_code).select().first()
        wallet.balance += payment.amount
        wallet.update_record()

    undo_stock_removal(bag=sale.id_bag)

    session.info = T('Sale undone')
    redirect(URL('default', 'index'))


@auth.requires(auth.has_membership('Sales returns')
            or auth.has_membership('Sales checkout')
            )
def get():
    """ args: [sale_id] """

    sale = db.sale(request.args(0))
    return dict(sale=sale)


@auth.requires(auth.has_membership('Sales returns')
            or auth.has_membership('Sales checkout')
            or auth.has_membership('Sales invoices')
            )
def get_by_barcode():
    """
        args: [barcode]
    """

    barcode = int(request.args(0))

    sale = db.sale(barcode)
    if not sale:
        raise HTTP(404)
    if sale.is_invoiced:
        raise HTTP(404)
    return dict(sale=sale)


@auth.requires_membership('Sales checkout')
def scan_ticket():
    """ Scan a bag ticket to create a sale """
    return dict()


@auth.requires_membership('Sales checkout')
def scan_order_ticket():
    """ Scan order ticket to create a sale """
    return dict()


@auth.requires_membership('Sales invoices')
def scan_for_invoice():
    return dict()


@auth.requires_membership('Sales returns')
def scan_for_refund():
    return dict()


@auth.requires_membership('Sales returns')
def scan_for_update():
    """ used to update deferred sales """

    return dict()


@auth.requires_membership('Sales returns')
def refund():
    """ Performs the logic to refund a sale

        args: [sale_id]
    """

    sale = db.sale(request.args(0))
    if not sale:
        raise HTTP(404)

    # check if the sale has been delivered
    is_delivered = db(
        (db.sale_log.id_sale == sale.id) &
        (db.sale_log.sale_event == SALE_DELIVERED)
    ).select().first()
    if not is_delivered and not sale.is_deferred:
        session.info = T('The sale has not been delivered!')
        redirect(URL('scan_for_refund'))

    payments_sum = (db.payment.amount - db.payment.change_amount).sum()
    payments_total = db(
        (db.payment.id_sale == sale.id)
    ).select(payments_sum).first()[payments_sum] or 0

    invalid = False
    item_removals = {}
    no_more_items = False

    if is_delivered:
        # obtain all returnable items from the specified sale
        c_items = db(
              (db.bag_item.id_item == db.item.id)
            & (db.bag_item.id_bag == sale.id_bag.id)
            & (db.item.has_inventory == True)
            & (db.item.is_returnable == True)
        ).select(
            left=db.credit_note_item.on(
                db.bag_item.id == db.credit_note_item.id_bag_item
            ),
            orderby=db.credit_note_item.id_bag_item
        )
        current_data = None
        current_id = None
        for r in c_items:
            if current_id != r.bag_item.id:

                current_id = r.bag_item.id
                current_data = Storage(
                    max=r.bag_item.quantity,
                    product_name=r.bag_item.product_name,
                    id=r.bag_item.id
                )
                item_removals[str(r.bag_item.id)] = current_data

            if r.credit_note_item.quantity:
                current_data.max -= r.credit_note_item.quantity

    # since pure defered sales does not remove stocks, we can only refund all payments once, so we have to make sure that there are no credit notes associated with the specified sale
    elif sale.is_deferred:
        credit_note = db(db.credit_note.id_sale == sale.id).select().first()
        invalid = bool(credit_note)  # hack to convert to boolean

        session.info = T('The sale already has a credit note')
        redirect(URL('index'))


    btn_text = T('Refund') if item_removals else T('Return all payments')
    form = SQLFORM.factory(
        Field('wallet_code', label=T('Wallet Code'))
        , Field('returned_items')
        , submit_button=btn_text, formstyle='bootstrap3_stacked'
    )


    if form.process().accepted:
        # normalize to the max number of allowed returns (since the ones specified in r_item are user defined)
        def max_available(r_item):
            return DQ(
                max(min(D(r_item[1]), item_removals[str(r_item[0])].max), 0)
            )


        r_items = map(
            lambda r : r.split(':')[0:2], form.vars.returned_items.split(',')
        )
        r_items = (
            (db.bag_item(int(r_item[0])), max_available(r_item)) for r_item in r_items
        )
        credit_note = sale_utils.refund(
            sale, request.now, auth.user, r_items,
            wallet_code=form.vars.wallet_code
        )

        wallet = db(db.wallet.wallet_code == credit_note.code).select().first()

        if sale.id_client:
            session.info = INFO(
                T('Sale returned, money added to: ') + wallet.wallet_code,
                T('Print'), URL('wallet', 'print_wallet', args=wallet.id), 'blank'
            )
        else:
            # new wallet created, and it does not have a client associated
            session.info = INFO(
                T('Sale returned, your wallet code is: ') + wallet.wallet_code,
                T('Print'), URL('wallet', 'print_wallet', args=wallet.id), 'blank'
            )

        redirect(URL('credit_note', 'get', args=credit_note.id))


    return locals()



@auth.requires_membership("Sales invoices")
def index():
    def sale_options(row):
        buttons = ()
        if row.is_deferred or not row.last_log_event:
            buttons += OPTION_BTN(
                'edit', URL('update', args=row.id), title=T('update')
            ),
        buttons += OPTION_BTN('receipt', URL('ticket', 'show_ticket', vars=dict(id_sale=row.id)), title=T('view ticket'), _target='_blank'), OPTION_BTN('description', URL('invoice', 'create')),
        return buttons

    def status_format(r, f):
        if r[f[0]]:
            return A(T(r[f[0]]), _href=URL('index', vars=dict(term_0=r[f[0]]) ))
        return '???'

    data = SUPERT(
        (db.sale.id_store == session.store)
        , fields=['consecutive', 'subtotal', 'total',
            dict(
                fields=['last_log_event'],
                label_as=T("Status"),
                custom_format=status_format
            ),
            'created_on'
        ],
        options_func=sale_options, global_options=[])
    return locals()
